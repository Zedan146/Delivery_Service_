from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponse
from django.utils import timezone
from .models import Order, Client
from .forms import OrderForm, ClientForm
from users.models import CustomUser as User
from logistics.models import DeliveryReport, CourierVehicle
from django.template.loader import render_to_string
from weasyprint import HTML
from django.conf import settings
import qrcode
import base64
from io import BytesIO
from django.urls import reverse

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
    
    context = {
        'order': order,
    }
    
    # Добавляем список доступных курьеров для логиста и админа
    if request.user.is_logistician() or request.user.is_admin():
        context['available_couriers'] = User.objects.filter(role='COURIER', is_active=True)
    
    return render(request, 'orders/order_detail.html', context)

@login_required
def order_edit(request, pk):
    """Представление для редактирования заказа"""
    if not request.user.is_logistician():
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

@login_required
def client_list(request):
    """Представление для просмотра списка клиентов"""
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для просмотра списка клиентов')
        return redirect('home')
    
    clients = Client.objects.all()
    return render(request, 'clients/client_list.html', {'clients': clients})

@login_required
def client_create(request):
    """Представление для создания нового клиента"""
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для создания клиентов')
        return redirect('orders:client_list')
    
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, 'Клиент успешно создан')
            return redirect('orders:client_detail', pk=client.pk)
    else:
        form = ClientForm()
    
    return render(request, 'clients/client_form.html', {'form': form, 'title': 'Создание клиента'})

@login_required
def client_detail(request, pk):
    """Представление для просмотра информации о клиенте"""
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для просмотра информации о клиентах')
        return redirect('orders:client_list')
    
    client = get_object_or_404(Client, pk=pk)
    return render(request, 'clients/client_detail.html', {'client': client})

@login_required
def client_edit(request, pk):
    """Представление для редактирования информации о клиенте"""
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для редактирования клиентов')
        return redirect('orders:client_list')
    
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Информация о клиенте успешно обновлена')
            return redirect('orders:client_detail', pk=client.pk)
    else:
        form = ClientForm(instance=client)
    
    return render(request, 'clients/client_form.html', {'form': form, 'title': 'Редактирование клиента'})

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
    """Генерация PDF-квитанции для заказа."""
    if not (request.user.is_logistician or request.user.is_admin):
        messages.error(request, 'У вас нет прав для просмотра квитанций')
        return redirect('orders:order_list')
    
    order = get_object_or_404(Order, pk=pk)
    
    # Генерируем QR-код
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    # В QR-код помещаем URL для отслеживания заказа
    tracking_url = request.build_absolute_uri(
        reverse('orders:order_detail', kwargs={'pk': order.pk})
    )
    qr.add_data(tracking_url)
    qr.make(fit=True)
    
    # Создаем изображение QR-кода
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # Конвертируем изображение в base64
    buffer = BytesIO()
    qr_image.save(buffer, format='PNG')
    qr_code = base64.b64encode(buffer.getvalue()).decode()
    
    # Рендерим HTML
    html_string = render_to_string('orders/print/order_receipt.html', {
        'order': order,
        'qr_code': qr_code,
    })
    
    # Создаем PDF
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    
    # Формируем имя файла
    filename = f'order_receipt_{order.order_number}.pdf'
    
    # Отправляем PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
