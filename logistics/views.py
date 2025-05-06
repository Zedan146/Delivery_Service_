from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Vehicle, CourierVehicle, DeliveryReport, CourierPerformance
from .forms import VehicleForm, CourierVehicleForm

@login_required
def vehicle_list(request):
    if not request.user.is_logistician():
        messages.error(request, 'У вас нет прав для просмотра списка транспортных средств')
        return redirect('home')
    
    vehicles = Vehicle.objects.all()
    return render(request, 'logistics/vehicle_list.html', {'vehicles': vehicles})

@login_required
def vehicle_create(request):
    if not request.user.is_logistician():
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
    if not request.user.is_logistician():
        messages.error(request, 'У вас нет прав для просмотра информации о транспортных средствах')
        return redirect('logistics:vehicle_list')
    
    vehicle = get_object_or_404(Vehicle, pk=pk)
    return render(request, 'logistics/vehicle_detail.html', {'vehicle': vehicle})

@login_required
def vehicle_edit(request, pk):
    if not request.user.is_logistician():
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
def courier_vehicle_list(request):
    if not request.user.is_logistician():
        messages.error(request, 'У вас нет прав для просмотра списка транспортных средств курьеров')
        return redirect('home')
    
    courier_vehicles = CourierVehicle.objects.filter(is_current=True)
    return render(request, 'logistics/courier_vehicle_list.html', {'courier_vehicles': courier_vehicles})

@login_required
def courier_vehicle_assign(request):
    if not request.user.is_logistician():
        messages.error(request, 'У вас нет прав для назначения транспортных средств')
        return redirect('logistics:courier_vehicle_list')
    
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
            return redirect('logistics:courier_vehicle_list')
    else:
        form = CourierVehicleForm()
    
    return render(request, 'logistics/courier_vehicle_form.html', {'form': form, 'title': 'Назначение транспортного средства'})

@login_required
def delivery_report_list(request):
    if not request.user.is_logistician():
        messages.error(request, 'У вас нет прав для просмотра отчетов о доставках')
        return redirect('home')
    
    reports = DeliveryReport.objects.all()
    return render(request, 'logistics/delivery_report_list.html', {'reports': reports})

@login_required
def delivery_report_detail(request, pk):
    if not request.user.is_logistician():
        messages.error(request, 'У вас нет прав для просмотра отчетов о доставках')
        return redirect('logistics:delivery_report_list')
    
    report = get_object_or_404(DeliveryReport, pk=pk)
    return render(request, 'logistics/delivery_report_detail.html', {'report': report})

@login_required
def courier_performance_list(request):
    if not request.user.is_logistician():
        messages.error(request, 'У вас нет прав для просмотра отчетов о производительности курьеров')
        return redirect('home')
    
    performances = CourierPerformance.objects.all()
    return render(request, 'logistics/courier_performance_list.html', {'performances': performances})

@login_required
def courier_performance_detail(request, courier_id):
    if not request.user.is_logistician():
        messages.error(request, 'У вас нет прав для просмотра отчетов о производительности курьеров')
        return redirect('logistics:courier_performance_list')
    
    performances = CourierPerformance.objects.filter(courier_id=courier_id)
    return render(request, 'logistics/courier_performance_detail.html', {'performances': performances})
