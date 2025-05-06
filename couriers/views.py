from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from orders.models import Order
from logistics.models import Vehicle, CourierVehicle

@login_required
def courier_orders(request):
    """View for listing orders assigned to the current courier."""
    if not request.user.is_courier:
        raise PermissionDenied
    
    orders = Order.objects.filter(courier=request.user).order_by('-created_at')
    return render(request, 'couriers/order_list.html', {'orders': orders})

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
    
    return render(request, 'couriers/order_detail.html', {'order': order})

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
