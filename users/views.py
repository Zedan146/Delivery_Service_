from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserChangeForm, StaffCreationForm
from .models import CustomUser
from orders.models import Order
from logistics.models import DeliveryReport, CourierPerformance, CourierVehicle, Vehicle
from django.db.models import Count, Sum, Avg
from django.templatetags.static import static
import os
from django.utils import timezone
from weasyprint import HTML
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from datetime import timedelta, datetime, date


@login_required
def profile(request):
    """Представление для просмотра профиля пользователя"""
    return render(request, 'users/profile.html')


@login_required
def profile_edit(request):
    """Представление для редактирования профиля пользователя"""
    # Проверяем, что пользователь редактирует свой профиль
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            # Проверяем права доступа
            if not request.user.is_admin() and 'password' in form.cleaned_data:
                messages.error(request, 'У вас нет прав для изменения пароля')
                return redirect('users:profile')
            
            form.save()
            messages.success(request, 'Профиль успешно обновлен')
            return redirect('users:profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    
    return render(request, 'users/profile_edit.html', {'form': form})


@login_required
def courier_list(request):
    if not (request.user.is_admin() or request.user.is_logistician()):
        return redirect('users:profile')
    
    couriers = CustomUser.objects.filter(
        role=CustomUser.Role.COURIER,
        is_active=True
    ).prefetch_related(
        'couriervehicle_set__vehicle'
    )
    
    # Add current vehicle information to each courier
    for courier in couriers:
        courier.current_vehicle = courier.couriervehicle_set.filter(is_current=True).first()
    
    return render(request, 'users/courier_list.html', {'couriers': couriers})


@login_required
def courier_detail(request, pk):
    if not (request.user.is_admin() or request.user.is_logistician()):
        return redirect('users:profile')
    
    courier = get_object_or_404(CustomUser, pk=pk, role=CustomUser.Role.COURIER)
    
    # Get current vehicle assignment
    courier.current_vehicle = CourierVehicle.objects.filter(
        courier=courier,
        is_current=True
    ).select_related('vehicle').first()
    
    # Get courier's delivered orders
    delivered_orders = Order.objects.filter(
        courier=courier,
        status=Order.Status.DELIVERED
    ).order_by('-delivery_date')
    
    # Calculate statistics
    total_delivered = delivered_orders.count()
    total_earnings = delivered_orders.aggregate(total=Sum('delivery_cost'))['total'] or 0
    
    # Calculate average delivery time
    delivery_times = []
    for order in delivered_orders:
        if order.delivery_date and order.created_at:
            # Convert delivery_date to datetime if it's a date
            delivery_datetime = timezone.make_aware(
                datetime.combine(order.delivery_date, datetime.min.time())
            ) if isinstance(order.delivery_date, date) else order.delivery_date
            delivery_time = delivery_datetime - order.created_at
            delivery_times.append(delivery_time)
    
    avg_time = None
    if delivery_times:
        avg_seconds = sum(t.total_seconds() for t in delivery_times) / len(delivery_times)
        avg_time = timedelta(seconds=avg_seconds)
    
    # Get available vehicles for assignment
    available_vehicles = Vehicle.objects.filter(is_active=True).exclude(
        couriervehicle__is_current=True
    )
    
    context = {
        'courier': courier,
        'delivered_orders': delivered_orders,
        'total_delivered': total_delivered,
        'total_earnings': total_earnings,
        'avg_time': avg_time,
        'current_vehicle': courier.current_vehicle,
        'available_vehicles': available_vehicles,
    }
    
    return render(request, 'users/courier_detail.html', context)


@login_required
def courier_report_pdf(request):
    if not (request.user.is_admin() or request.user.is_logistician()):
        return redirect('users:profile')
    couriers = []
    from orders.models import Order
    from logistics.models import DeliveryReport
    for user in CustomUser.objects.filter(role=CustomUser.Role.COURIER, is_active=True):
        delivered_orders = Order.objects.filter(courier=user, status=Order.Status.DELIVERED)
        total_delivered = delivered_orders.count()
        total_earnings = delivered_orders.aggregate(total=Sum('delivery_cost'))['total'] or 0
        reports = DeliveryReport.objects.filter(courier=user, delivery_completed__isnull=False, delivery_started__isnull=False)
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
    html_string = render_to_string('users/print/courier_report.html', {
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
    if not request.user.is_admin():
        return redirect('users:profile')
    logisticians = CustomUser.objects.filter(role=CustomUser.Role.LOGISTICIAN, is_active=True)
    return render(request, 'users/logistician_list.html', {'logisticians': logisticians})


@login_required
def staff_create(request):
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
