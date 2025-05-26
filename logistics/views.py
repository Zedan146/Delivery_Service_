from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Vehicle, CourierVehicle, DeliveryReport, CourierPerformance
from .forms import VehicleForm, CourierVehicleForm
from datetime import timedelta

@login_required
def vehicle_list(request):
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для просмотра списка транспортных средств')
        return redirect('home')
    
    vehicles = Vehicle.objects.all()
    return render(request, 'logistics/vehicle_list.html', {'vehicles': vehicles})

@login_required
def vehicle_create(request):
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для создания транспортных средств')
        return redirect('logistics:vehicle_list')
    
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save()
            messages.success(request, 'Транспортное средство успешно создано')
            return redirect('logistics:vehicle_detail', pk=vehicle.pk)
    else:
        form = VehicleForm()
    
    return render(request, 'logistics/vehicle_form.html', {'form': form, 'title': 'Создание транспортного средства'})

@login_required
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    # Проверяем права доступа
    if request.user.is_logistician() or request.user.is_admin():
        # Логист и админ могут видеть все детали и управлять назначениями
        current_courier_vehicles = vehicle.couriervehicle_set.filter(is_current=True)
        from .forms import CourierVehicleForm
        if request.method == 'POST':
            form = CourierVehicleForm(request.POST)
            if form.is_valid():
                courier_vehicle = form.save(commit=False)
                courier_vehicle.vehicle = vehicle
                # Снимаем старое назначение с курьера
                CourierVehicle.objects.filter(courier=courier_vehicle.courier, is_current=True).update(is_current=False)
                courier_vehicle.is_current = True
                courier_vehicle.save()
                messages.success(request, 'Курьер успешно назначен на транспортное средство')
                return redirect('logistics:vehicle_detail', pk=vehicle.pk)
        else:
            form = CourierVehicleForm()
            form.fields['vehicle'].queryset = Vehicle.objects.filter(pk=vehicle.pk)
        
        context = {
            'vehicle': vehicle,
            'current_courier_vehicles': current_courier_vehicles,
            'form': form,
            'is_logistician': True
        }
    elif request.user.is_courier():
        # Проверяем, назначен ли транспорт курьеру
        if not vehicle.couriervehicle_set.filter(courier=request.user, is_current=True).exists():
            messages.error(request, 'У вас нет доступа к этому транспортному средству')
            return redirect('couriers:vehicle_list')
        
        context = {
            'vehicle': vehicle,
            'is_logistician': False
        }
    else:
        messages.error(request, 'У вас нет прав для просмотра информации о транспортных средствах')
        return redirect('home')
    
    return render(request, 'logistics/vehicle_detail.html', context)

@login_required
def vehicle_edit(request, pk):
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для редактирования транспортных средств')
        return redirect('logistics:vehicle_list')
    
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, 'Информация о транспортном средстве успешно обновлена')
            return redirect('logistics:vehicle_detail', pk=vehicle.pk)
    else:
        form = VehicleForm(instance=vehicle)
    
    return render(request, 'logistics/vehicle_form.html', {'form': form, 'title': 'Редактирование транспортного средства'})

@login_required
def vehicle_delete(request, pk):
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для удаления транспортных средств')
        return redirect('logistics:vehicle_list')
    
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    # Проверяем, не назначено ли транспортное средство курьеру
    if vehicle.couriervehicle_set.filter(is_current=True).exists():
        messages.error(request, 'Невозможно удалить транспортное средство, так как оно назначено курьеру')
        return redirect('logistics:vehicle_list')
    
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, 'Транспортное средство успешно удалено')
        return redirect('logistics:vehicle_list')
    
    return render(request, 'logistics/vehicle_confirm_delete.html', {'vehicle': vehicle})

@login_required
def courier_vehicle_assign(request):
    """Назначение транспортного средства курьеру"""
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для назначения транспортных средств')
        return redirect('logistics:vehicle_list')
    
    if request.method == 'POST':
        form = CourierVehicleForm(request.POST)
        if form.is_valid():
            # Деактивируем текущее транспортное средство курьера
            CourierVehicle.objects.filter(
                courier=form.cleaned_data['courier'],
                is_current=True
            ).update(is_current=False)
            
            # Создаем новую запись
            courier_vehicle = form.save(commit=False)
            courier_vehicle.is_current = True
            courier_vehicle.save()
            
            messages.success(request, 'Транспортное средство успешно назначено курьеру')
            return redirect('users:courier_detail', form.cleaned_data['courier'].pk)
    else:
        form = CourierVehicleForm()
    
    return render(request, 'logistics/courier_vehicle_form.html', {'form': form, 'title': 'Назначение транспортного средства'})

@login_required
def courier_vehicle_unassign(request, pk):
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для снятия транспортного средства')
        return redirect('logistics:vehicle_list')
    courier_vehicle = get_object_or_404(CourierVehicle, pk=pk, is_current=True)
    if request.method == 'POST':
        courier_vehicle.is_current = False
        courier_vehicle.save()
        messages.success(request, 'Транспортное средство успешно снято с курьера')
        return redirect('users:courier_detail', courier_vehicle.courier.pk)

@login_required
def delivery_report_list(request):
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для просмотра отчетов о доставках')
        return redirect('home')
    
    # Получаем только отчеты по доставленным заказам
    reports = DeliveryReport.objects.filter(
        order__status='DELIVERED'
    ).select_related(
        'order', 
        'courier', 
        'vehicle', 
        'order__client'
    ).order_by('-delivery_completed')  # Сортировка по дате завершения доставки
    
    return render(request, 'logistics/delivery_report_list.html', {
        'reports': reports,
        'status': 'DELIVERED'  # Фиксированный статус для выполненных заказов
    })

@login_required
def delivery_report_detail(request, pk):
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для просмотра отчетов о доставках')
        return redirect('logistics:delivery_report_list')
    
    report = get_object_or_404(DeliveryReport, pk=pk)
    return render(request, 'logistics/delivery_report_detail.html', {'report': report})

@login_required
def courier_performance_list(request):
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для просмотра отчетов о производительности курьеров')
        return redirect('home')
    
    performances = CourierPerformance.objects.all()
    return render(request, 'logistics/courier_performance_list.html', {'performances': performances})

@login_required
def courier_performance_detail(request, courier_id=None):
    user = request.user
    if user.is_courier():
        courier_id = user.pk
    elif not (user.is_logistician() or user.is_admin()):
        messages.error(request, 'У вас нет прав для просмотра отчетов о производительности курьеров')
        return redirect('home')
    elif courier_id is None:
        messages.error(request, 'Не указан курьер')
        return redirect('logistics:courier_performance_list')

    performances = CourierPerformance.objects.filter(courier_id=courier_id).order_by('-date')
    total_orders = sum(p.orders_completed for p in performances)
    total_earnings = sum(p.total_earnings for p in performances)
    total_time = sum((p.total_delivery_time for p in performances), timedelta())
    avg_delivery_time = total_time / total_orders if total_orders > 0 else timedelta()

    context = {
        'performances': performances,
        'total_orders': total_orders,
        'total_earnings': total_earnings,
        'avg_delivery_time': avg_delivery_time
    }
    return render(request, 'logistics/courier_performance_detail.html', context)
