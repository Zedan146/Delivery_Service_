import os
from datetime import timedelta, datetime, date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.templatetags.static import static
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Count, Sum, Avg

from weasyprint import HTML

from .forms import CustomUserChangeForm, StaffCreationForm, ProfileEditForm
from .models import CustomUser
from orders.models import Order
from logistics.models import DeliveryReport, CourierPerformance, CourierVehicle, Vehicle


@login_required
def profile(request):
    """Отображение профиля пользователя"""
    return render(request, 'users/profile.html')


@login_required
def profile_edit(request):
    """Редактирование профиля пользователя"""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен')
            return redirect('users:profile')
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'users/profile_edit.html', {'form': form})


@login_required
def courier_list(request):
    """Список активных курьеров (доступно админам и логистам)"""
    if not (request.user.is_admin() or request.user.is_logistician()):
        return redirect('users:profile')
    
    couriers = CustomUser.objects.filter(
        role=CustomUser.Role.COURIER,
        is_active=True
    ).prefetch_related(
        'couriervehicle_set__vehicle'
    )
    
    # Добавляем информацию о текущем ТС для каждого курьера
    for courier in couriers:
        courier.current_vehicle = courier.couriervehicle_set.filter(is_current=True).first()
    
    return render(request, 'users/courier_list.html', {'couriers': couriers})


def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days} дн.")
    if hours:
        parts.append(f"{hours} ч.")
    if minutes:
        parts.append(f"{minutes} мин.")
    if seconds or not parts:
        parts.append(f"{seconds} сек.")
    return " ".join(parts)


@login_required
def courier_detail(request, pk):
    """Детальная информация о курьере (доступно админам и логистам)"""
    if not (request.user.is_admin() or request.user.is_logistician()):
        return redirect('users:profile')
    
    courier = get_object_or_404(CustomUser, pk=pk, role=CustomUser.Role.COURIER)
    
    # Получаем текущее назначение ТС
    courier.current_vehicle = CourierVehicle.objects.filter(
        courier=courier,
        is_current=True
    ).select_related('vehicle').first()
    
    # Получаем доставленные заказы курьера
    delivered_orders = Order.objects.filter(
        courier=courier,
        status=Order.Status.DELIVERED
    ).order_by('-delivery_date')
    
    # Рассчитываем статистику
    total_delivered = delivered_orders.count()
    total_earnings = delivered_orders.aggregate(total=Sum('delivery_cost'))['total'] or 0
    
    # Новый расчет среднего времени доставки по DeliveryReport
    reports = DeliveryReport.objects.filter(
        courier=courier,
        delivery_started__isnull=False,
        delivery_completed__isnull=False
    )
    delivery_times = [
        (r.delivery_completed - r.delivery_started).total_seconds()
        for r in reports
        if r.delivery_completed and r.delivery_started
    ]
    avg_time = None
    if delivery_times:
        avg_seconds = sum(delivery_times) / len(delivery_times)
        avg_time = timedelta(seconds=avg_seconds)
    
    # Получаем доступные ТС для назначения
    available_vehicles = Vehicle.objects.filter(is_active=True).exclude(
        couriervehicle__is_current=True
    )
    
    context = {
        'courier': courier,
        'delivered_orders': delivered_orders,
        'total_delivered': total_delivered,
        'total_earnings': total_earnings,
        'avg_time': format_timedelta(avg_time) if avg_time else None,
        'current_vehicle': courier.current_vehicle,
        'available_vehicles': available_vehicles,
    }
    
    return render(request, 'users/courier_detail.html', context)


@login_required
def courier_report_pdf(request):
    """Генерация PDF-отчета по работе курьеров (доступно админам и логистам)"""
    if not (request.user.is_admin() or request.user.is_logistician()):
        return redirect('users:profile')
        
    couriers = []
    for user in CustomUser.objects.filter(role=CustomUser.Role.COURIER, is_active=True):
        delivered_orders = Order.objects.filter(courier=user, status=Order.Status.DELIVERED)
        total_delivered = delivered_orders.count()
        total_earnings = delivered_orders.aggregate(total=Sum('delivery_cost'))['total'] or 0
        reports = DeliveryReport.objects.filter(
            courier=user, 
            delivery_completed__isnull=False, 
            delivery_started__isnull=False
        )
        
        avg_time = None
        if reports.exists():
            total_seconds = sum([(r.delivery_completed - r.delivery_started).total_seconds() for r in reports])
            avg_seconds = total_seconds / reports.count()
            hours = int(avg_seconds // 3600)
            minutes = int((avg_seconds % 3600) // 60)
            avg_time = f"{hours}ч {minutes}м" if hours else f"{minutes}м"
            
        couriers.append({
            'full_name': user.get_full_name(),
            'phone_number': user.phone_number,
            'email': user.email,
            'total_delivered': total_delivered,
            'total_earnings': total_earnings,
            'avg_time': avg_time,
            'delivered_orders': delivered_orders,
        })
        
    html_string = render_to_string('print/courier_report.html', {
        'couriers': couriers,
        'report_date': timezone.now().date(),
    })
    
    css_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'print_forms.css')
    html = HTML(string=html_string)
    pdf = html.write_pdf(stylesheets=[css_path])
    
    filename = f'courier_report_{timezone.now().date()}.pdf'
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


@login_required
def logistician_list(request):
    """Список активных логистов (доступно только админам)"""
    if not request.user.is_admin():
        return redirect('users:profile')
        
    logisticians = CustomUser.objects.filter(role=CustomUser.Role.LOGISTICIAN, is_active=True)
    return render(request, 'users/logistician_list.html', {'logisticians': logisticians})


@login_required
def staff_create(request):
    """Создание нового сотрудника (курьера или логиста)"""
    if not request.user.is_admin():
        return redirect('users:profile')
        
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('users:logistician_list' if user.role == user.Role.LOGISTICIAN else 'users:courier_list')
    else:
        form = StaffCreationForm()
        
    return render(request, 'users/staff_create.html', {'form': form})


@login_required
def staff_edit(request, pk):
    """Редактирование сотрудника (курьера или логиста)"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для редактирования сотрудников')
        return redirect('users:profile')
    
    staff = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, 'Информация о сотруднике успешно обновлена')
            return redirect('users:logistician_list' if staff.role == staff.Role.LOGISTICIAN else 'users:courier_list')
    else:
        form = CustomUserChangeForm(instance=staff)
    
    return render(request, 'users/staff_form.html', {
        'form': form,
        'title': 'Редактирование сотрудника',
        'staff': staff
    })


@login_required
def staff_delete(request, pk):
    """Удаление сотрудника (курьера или логиста)"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для удаления сотрудников')
        return redirect('users:profile')
    
    staff = get_object_or_404(CustomUser, pk=pk)
    
    # Проверяем, не назначен ли курьер на активные заказы
    if staff.role == staff.Role.COURIER and Order.objects.filter(courier=staff, status__in=['ASSIGNED', 'IN_PROGRESS']).exists():
        messages.error(request, 'Невозможно удалить курьера, так как у него есть активные заказы')
        return redirect('users:courier_list')
    
    if request.method == 'POST':
        staff.delete()
        messages.success(request, 'Сотрудник успешно удален')
        return redirect('users:logistician_list' if staff.role == staff.Role.LOGISTICIAN else 'users:courier_list')
    
    return render(request, 'users/staff_confirm_delete.html', {'staff': staff})
