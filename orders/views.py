from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.utils import timezone
from .models import Order
from clients.models import Client, ClientAddress
from .forms import OrderForm
from clients.forms import ClientForm, ClientAddressInlineFormSet
from users.models import CustomUser as User
from logistics.models import DeliveryReport, CourierVehicle
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from django.conf import settings
import qrcode
import base64
from io import BytesIO
from django.urls import reverse
from datetime import datetime, timedelta, date
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.templatetags.static import static
import os

@login_required
def order_list(request):
    """Представление для просмотра списка заказов с фильтрацией по статусу для логиста и администратора"""
    if request.user.is_logistician() or request.user.is_admin():
        default_status = 'ALL' if request.user.is_admin() else 'NEW'
        status = request.GET.get('status', default_status)
        if status == 'ALL':
            orders = Order.objects.all()
        else:
            orders = Order.objects.filter(status=status)
    elif request.user.is_courier():
        orders = Order.objects.filter(courier=request.user)
        status = None
    else:
        return HttpResponseForbidden()
    
    return render(request, 'orders/order_list.html', {'orders': orders, 'status': status})

@login_required
def order_create(request):
    """Представление для создания нового заказа"""
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для создания заказов')
        return redirect('orders:order_list')
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            messages.success(request, 'Заказ успешно создан')
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = OrderForm()
    
    return render(request, 'orders/order_form.html', {'form': form, 'title': 'Создание заказа'})

@login_required
def order_detail(request, pk):  
    """Представление для просмотра информации о заказе"""
    order = get_object_or_404(Order, pk=pk)
    
    # Проверяем права доступа
    if not (request.user.is_logistician() or request.user.is_admin() or 
            (request.user.is_courier() and order.courier == request.user)):
        messages.error(request, 'У вас нет прав для просмотра этого заказа')
        return HttpResponseForbidden()
    
    default_address = order.client.addresses.filter(is_default=True).first()
    context = {
        'order': order,
        'default_address': default_address,
    }
    
    # Добавляем список доступных курьеров для логиста и админа
    if request.user.is_logistician() or request.user.is_admin():
        context['available_couriers'] = User.objects.filter(role='COURIER', is_active=True)
    
    return render(request, 'orders/order_detail.html', context)

@login_required
def order_edit(request, pk):
    """Представление для редактирования заказа"""
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для редактирования заказов')
        return redirect('orders:order_list')
    
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Заказ успешно обновлен')
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = OrderForm(instance=order)
    
    return render(request, 'orders/order_form.html', {'form': form, 'title': 'Редактирование заказа'})

def is_courier(user):
    return user.role == 'COURIER'

@login_required
@user_passes_test(is_courier)
def courier_orders(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        action = request.POST.get('action')
        order = get_object_or_404(Order, pk=order_id, courier=request.user)
        if action == 'take_in_progress' and order.status == 'ASSIGNED':
            order.status = 'IN_PROGRESS'
            order.save()
            messages.success(request, f'Заказ {order.order_number} взят в работу')
        elif action == 'mark_delivered' and order.status == 'IN_PROGRESS':
            order.status = 'DELIVERED'
            order.save()
            messages.success(request, f'Заказ {order.order_number} отмечен как доставленный')
        else:
            messages.error(request, 'Недопустимое действие для этого заказа')
        return redirect('orders:courier_orders')
    orders = Order.objects.filter(courier=request.user).order_by('-created_at')
    return render(request, 'orders/courier_orders.html', {'orders': orders})

@login_required
@user_passes_test(is_courier)
def courier_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, courier=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        current_status = order.status
        
        # Проверяем корректность перехода статуса
        if new_status in dict(Order.Status.choices):
            # Курьер может менять статус только по определенным правилам
            if current_status == 'ASSIGNED' and new_status == 'IN_PROGRESS':
                order.status = new_status
                order.save()
                messages.success(request, 'Статус заказа изменен на "В процессе"')
            elif current_status == 'IN_PROGRESS' and new_status == 'DELIVERED':
                order.status = new_status
                order.save()
                messages.success(request, 'Заказ успешно доставлен')
            elif new_status == 'CANCELLED':
                messages.error(request, 'Курьер не может отменять заказы')
            else:
                messages.error(request, 'Недопустимое изменение статуса')
            return redirect('orders:courier_orders')
    
    # Определяем доступные статусы для текущего заказа
    available_statuses = []
    if order.status == 'ASSIGNED':
        available_statuses = [('IN_PROGRESS', 'В процессе')]
    elif order.status == 'IN_PROGRESS':
        available_statuses = [('DELIVERED', 'Доставлен')]
    
    context = {
        'order': order,
        'available_statuses': available_statuses
    }
    return render(request, 'orders/courier_order_detail.html', context)

@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Заказ успешно удален')
        return redirect('orders:order_list')
    return render(request, 'orders/order_confirm_delete.html', {'order': order})

@login_required
def order_cancel(request, pk):
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для отмены заказов')
        return HttpResponseForbidden()
    
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        if order.status not in ['DELIVERED', 'CANCELLED']:
            order.status = 'CANCELLED'
            order.save()
            messages.success(request, 'Заказ успешно отменен')
        else:
            messages.error(request, 'Невозможно отменить заказ в текущем статусе')
    
    return redirect('orders:order_detail', pk=order.pk)

@login_required
def order_assign_courier(request, pk):
    if not (request.user.is_logistician() or request.user.is_admin()):
        return HttpResponseForbidden()
    
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        courier_id = request.POST.get('courier')
        if courier_id == 'None':
            # Снимаем курьера с заказа
            order.courier = None
            order.status = 'NEW'  # Возвращаем заказ в статус "Новый"
            # Удаляем отчет о доставке, если он существует
            DeliveryReport.objects.filter(order=order).delete()
            order.save()
            messages.success(request, 'Курьер успешно снят с заказа, статус заказа изменен на "Новый"')
        elif courier_id:
            courier = get_object_or_404(User, pk=courier_id, role='COURIER')
            # Проверяем, есть ли у курьера назначенное транспортное средство
            courier_vehicle = CourierVehicle.objects.filter(courier=courier, is_current=True).first()
            if not courier_vehicle:
                messages.error(request, 'Невозможно назначить курьера без транспортного средства')
                return redirect('orders:order_detail', pk=order.pk)
            
            order.courier = courier
            order.status = 'ASSIGNED'
            order.save()
            
            # Создаем или обновляем отчет о доставке
            delivery_report, created = DeliveryReport.objects.get_or_create(
                order=order,
                defaults={
                    'courier': courier,
                    'vehicle': courier_vehicle.vehicle,
                    'delivery_started': timezone.now()
                }
            )
            if not created:
                delivery_report.courier = courier
                delivery_report.vehicle = courier_vehicle.vehicle
                delivery_report.delivery_started = timezone.now()
                delivery_report.delivery_completed = None
                delivery_report.save()
            
            messages.success(request, 'Курьер успешно назначен')
        else:
            messages.error(request, 'Пожалуйста, выберите курьера')
    
    return redirect('orders:order_detail', pk=order.pk)

@login_required
def order_receipt_pdf(request, pk):
    """Представление для генерации PDF-квитанции заказа"""
    order = get_object_or_404(Order, pk=pk)
    
    # Проверяем права доступа
    if not (request.user.is_logistician() or request.user.is_admin() or 
            (request.user.is_courier() and order.courier == request.user)):
        messages.error(request, 'У вас нет прав для просмотра квитанции')
        return HttpResponseForbidden()
    
    # Генерируем QR-код с информацией о заказе
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(f'Заказ #{order.order_number}\n'
                f'Статус: {order.get_status_display()}\n'
                f'Клиент: {order.client.get_full_name()}\n'
                f'Адрес: {order.delivery_address.get_full_address()}\n'
                f'Дата доставки: {order.delivery_date}')
    qr.make(fit=True)
    
    # Создаем изображение QR-кода
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # Конвертируем изображение в base64
    buffered = BytesIO()
    qr_image.save(buffered, format="PNG")
    qr_code = base64.b64encode(buffered.getvalue()).decode()
    
    # Рендерим HTML-шаблон
    html_string = render_to_string('print/order_receipt.html', {
        'order': order,
        'qr_code': qr_code,
    })
    
    # Абсолютный путь к CSS для WeasyPrint
    css_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'print_forms.css')
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf(stylesheets=[CSS(filename=css_path)])
    
    # Формируем имя файла
    filename = f'order_{order.order_number}_receipt.pdf'
    
    # Создаем HTTP-ответ
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response

@login_required
def delivery_report_pdf(request):
    """Представление для генерации PDF-отчета по доставкам"""
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для просмотра отчетов')
        return HttpResponseForbidden()
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date or start_date == '':
        start_date = (timezone.now() - timedelta(days=30)).date()
    else:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = (timezone.now() - timedelta(days=30)).date()

    if not end_date or end_date == '':
        end_date = timezone.now().date()
    else:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = timezone.now().date()

    all_orders = Order.objects.all().values('order_number', 'delivery_date')
    orders = Order.objects.filter(
        delivery_date__range=[start_date, end_date]
    ).select_related('client', 'delivery_address', 'courier')
    
    # Статистика по статусам
    status_stats = {}
    for status, _ in Order.Status.choices:
        count = sum(1 for o in orders if o.status == status)
        if count > 0:
            status_stats[dict(Order.Status.choices)[status]] = count
    
    # Статистика по курьерам
    courier_stats = {}
    for courier in User.objects.filter(role='COURIER'):
        courier_orders = [o for o in orders if o.courier == courier]
        if courier_orders:
            courier_stats[courier] = {
                'total': len(courier_orders),
                'delivered': sum(1 for o in courier_orders if o.status == 'DELIVERED'),
                'in_progress': sum(1 for o in courier_orders if o.status == 'IN_PROGRESS'),
                'cancelled': sum(1 for o in courier_orders if o.status == 'CANCELLED'),
            }
    
    # Общая статистика
    total_orders = len(orders)
    total_amount = sum(o.order_amount for o in orders)
    average_amount = total_amount / total_orders if total_orders > 0 else 0
    success_rate = (sum(1 for o in orders if o.status == 'DELIVERED') / total_orders * 100) if total_orders > 0 else 0
    
    # Рендерим HTML-шаблон
    html_string = render_to_string('print/delivery_report.html', {
        'orders': orders,
        'status_stats': status_stats,
        'courier_stats': courier_stats,
        'total_orders': total_orders,
        'total_amount': total_amount,
        'average_amount': average_amount,
        'success_rate': success_rate,
        'generated_at': timezone.now(),
        'start_date': start_date,
        'end_date': end_date,
    })
    
    # Абсолютный путь к CSS для WeasyPrint
    css_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'print_forms.css')
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf(stylesheets=[CSS(filename=css_path)])
    
    # Формируем имя файла
    filename = f'delivery_report_{timezone.now().strftime("%Y-%m-%d")}.pdf'
    
    # Создаем HTTP-ответ
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response

@login_required
def get_client_addresses(request):
    """Получение списка адресов клиента для AJAX-запроса"""
    client_id = request.GET.get('client_id')
    if not client_id:
        return JsonResponse({'error': 'Не указан ID клиента'}, status=400)
    
    try:
        addresses = ClientAddress.objects.filter(client_id=client_id)
        data = [{'id': addr.id, 'address': addr.get_full_address()} for addr in addresses]
        return JsonResponse({'addresses': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
