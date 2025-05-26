from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from orders.models import Order
from logistics.models import Vehicle, CourierVehicle, DeliveryReport, CourierPerformance
from datetime import timedelta
from decimal import Decimal

@login_required
def courier_orders(request):
    """Просмотр заказов, назначенных текущему курьеру, и фильтрация по статусу заказа."""
    if not request.user.is_courier:
        raise PermissionDenied

    show = request.GET.get('show', 'active')
    if show == 'delivered':
        orders = Order.objects.filter(courier=request.user, status='DELIVERED').order_by('-created_at')
    else:
        orders = Order.objects.filter(courier=request.user, status__in=['ASSIGNED', 'IN_PROGRESS']).order_by('-created_at')

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        action = request.POST.get('action')
        order = get_object_or_404(Order, pk=order_id, courier=request.user)
        # Проверка: есть ли у курьера активный транспорт
        has_vehicle = CourierVehicle.objects.filter(courier=request.user, is_current=True).exists()
        if not has_vehicle:
            messages.error(request, 'Нельзя взять заказ в работу или завершить доставку без назначенного транспорта!')
            return redirect('couriers:order_list')
        
        if action == 'take_in_progress' and order.status == 'ASSIGNED':
            order.status = 'IN_PROGRESS'
            # Обновляем отчет о доставке
            try:
                delivery_report = DeliveryReport.objects.get(order=order)
                delivery_report.delivery_started = timezone.now()
                delivery_report.save()
            except DeliveryReport.DoesNotExist:
                courier_vehicle = CourierVehicle.objects.filter(courier=request.user, is_current=True).first()
                if courier_vehicle:
                    DeliveryReport.objects.create(
                        order=order,
                        courier=request.user,
                        vehicle=courier_vehicle.vehicle,
                        delivery_started=timezone.now()
                    )
            order.save()
            messages.success(request, f'Заказ {order.order_number} взят в работу')
        elif action == 'mark_delivered' and order.status == 'IN_PROGRESS':
            order.status = 'DELIVERED'
            # Обновляем отчет о доставке
            try:
                delivery_report = DeliveryReport.objects.get(order=order)
                delivery_report.delivery_completed = timezone.now()
                delivery_report.save()
                delivery_time = delivery_report.delivery_completed - delivery_report.delivery_started
            except DeliveryReport.DoesNotExist:
                courier_vehicle = CourierVehicle.objects.filter(courier=request.user, is_current=True).first()
                delivery_time = timedelta()
                if courier_vehicle:
                    DeliveryReport.objects.create(
                        order=order,
                        courier=request.user,
                        vehicle=courier_vehicle.vehicle,
                        delivery_started=timezone.now(),
                        delivery_completed=timezone.now()
                    )
            update_courier_performance(request.user, delivery_time, order.delivery_cost)
            order.save()
            messages.success(request, f'Заказ {order.order_number} отмечен как доставленный')
        else:
            messages.error(request, 'Недопустимое действие для этого заказа')
        return redirect('couriers:order_list')

    return render(request, 'orders/courier_orders.html', {'orders': orders, 'show': show})

@login_required
def courier_order_detail(request, pk):
    """Просмотр и обновление деталей заказа курьера."""
    if not request.user.is_courier:
        raise PermissionDenied
    
    order = get_object_or_404(Order, pk=pk, courier=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [status[0] for status in Order.Status.choices]:
            old_status = order.status
            order.status = new_status
            
            # Обновляем отчет о доставке
            try:
                delivery_report = DeliveryReport.objects.get(order=order)
                if new_status == 'IN_PROGRESS' and old_status == 'ASSIGNED':
                    delivery_report.delivery_started = timezone.now()
                elif new_status == 'DELIVERED' and old_status == 'IN_PROGRESS':
                    delivery_report.delivery_completed = timezone.now()
                delivery_report.save()
            except DeliveryReport.DoesNotExist:
                # Если отчет не существует, создаем его
                courier_vehicle = CourierVehicle.objects.filter(courier=request.user, is_current=True).first()
                if courier_vehicle:
                    DeliveryReport.objects.create(
                        order=order,
                        courier=request.user,
                        vehicle=courier_vehicle.vehicle,
                        delivery_started=timezone.now(),
                        delivery_completed=timezone.now() if new_status == 'DELIVERED' else None
                    )
            
            if new_status == 'DELIVERED' and old_status == 'IN_PROGRESS':
                try:
                    delivery_report = DeliveryReport.objects.get(order=order)
                    delivery_report.delivery_completed = timezone.now()
                    delivery_report.save()
                    delivery_time = delivery_report.delivery_completed - delivery_report.delivery_started
                except DeliveryReport.DoesNotExist:
                    courier_vehicle = CourierVehicle.objects.filter(courier=request.user, is_current=True).first()
                    delivery_time = timedelta()
                    if courier_vehicle:
                        DeliveryReport.objects.create(
                            order=order,
                            courier=request.user,
                            vehicle=courier_vehicle.vehicle,
                            delivery_started=timezone.now(),
                            delivery_completed=timezone.now()
                        )
                update_courier_performance(request.user, delivery_time, order.delivery_cost)
            
            order.save()
            messages.success(request, 'Статус заказа успешно обновлен.')
            return redirect('couriers:order_detail', pk=order.pk)
    
    return render(request, 'orders/courier_order_detail.html', {'order': order})

@login_required
def courier_vehicles(request):
    """Показ детальной информации о текущем назначенном транспорте курьера."""
    if not request.user.is_courier:
        raise PermissionDenied
    current_cv = CourierVehicle.objects.filter(courier=request.user, is_current=True).select_related('vehicle').first()
    vehicle = current_cv.vehicle if current_cv else None
    return render(request, 'couriers/vehicle_detail.html', {'vehicle': vehicle})

def update_courier_performance(courier, delivery_time, delivery_cost):
    # Расчет заработка курьера за доставку
    earnings = max(delivery_cost * Decimal('0.3'), Decimal('200'))
    perf, created = CourierPerformance.objects.get_or_create(
        courier=courier,
        date=timezone.now().date(),
        defaults={'orders_completed': 0, 'total_delivery_time': timedelta(), 'total_earnings': 0}
    )
    perf.orders_completed += 1
    perf.total_delivery_time += delivery_time
    perf.total_earnings += earnings
    perf.save()
