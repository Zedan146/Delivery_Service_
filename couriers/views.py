from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from orders.models import Order
from logistics.models import Vehicle, CourierVehicle

@login_required
def courier_orders(request):
    """View for listing orders assigned to the current courier и фильтрации по статусу заказа."""
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
            order.save()
            messages.success(request, f'Заказ {order.order_number} взят в работу')
        elif action == 'mark_delivered' and order.status == 'IN_PROGRESS':
            order.status = 'DELIVERED'
            order.save()
            messages.success(request, f'Заказ {order.order_number} отмечен как доставленный')
        else:
            messages.error(request, 'Недопустимое действие для этого заказа')
        return redirect('couriers:order_list')

    return render(request, 'orders/courier_orders.html', {'orders': orders, 'show': show})

@login_required
def courier_order_detail(request, pk):
    """View for displaying and updating courier order details."""
    if not request.user.is_courier:
        raise PermissionDenied
    
    order = get_object_or_404(Order, pk=pk, courier=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [status[0] for status in Order.Status.choices]:
            order.status = new_status
            order.save()
            messages.success(request, 'Статус заказа успешно обновлен.')
            return redirect('couriers:order_detail', pk=order.pk)
    
    return render(request, 'orders/courier_order_detail.html', {'order': order})

@login_required
def courier_vehicles(request):
    """View for listing vehicles assigned to the current courier."""
    if not request.user.is_courier:
        raise PermissionDenied
    
    courier_vehicles = CourierVehicle.objects.filter(
        courier=request.user,
        is_current=True
    ).select_related('vehicle')
    
    vehicles = [cv.vehicle for cv in courier_vehicles]
    return render(request, 'couriers/vehicle_list.html', {'vehicles': vehicles})
