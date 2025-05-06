from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden
from .models import Order, Client
from .forms import OrderForm, ClientForm
from users.models import CustomUser as User

@login_required
def order_list(request):
    """Представление для просмотра списка заказов"""
    if request.user.is_logistician():
        orders = Order.objects.all()
    elif request.user.is_courier():
        orders = Order.objects.filter(courier=request.user)
    else:
        return HttpResponseForbidden()
    
    return render(request, 'orders/order_list.html', {'orders': orders})

@login_required
def order_create(request):
    """Представление для создания нового заказа"""
    if not request.user.is_logistician():
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
    if not (request.user.is_logistician or 
            (request.user.is_courier and order.courier == request.user)):
        return HttpResponseForbidden()
    
    context = {
        'order': order,
    }
    
    # Добавляем список доступных курьеров для логиста
    if request.user.is_logistician:
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
    if not request.user.is_logistician():
        messages.error(request, 'У вас нет прав для просмотра списка клиентов')
        return redirect('home')
    
    clients = Client.objects.all()
    return render(request, 'orders/client_list.html', {'clients': clients})

@login_required
def client_create(request):
    """Представление для создания нового клиента"""
    if not request.user.is_logistician():
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
    
    return render(request, 'orders/client_form.html', {'form': form, 'title': 'Создание клиента'})

@login_required
def client_detail(request, pk):
    """Представление для просмотра информации о клиенте"""
    if not request.user.is_logistician():
        messages.error(request, 'У вас нет прав для просмотра информации о клиентах')
        return redirect('orders:client_list')
    
    client = get_object_or_404(Client, pk=pk)
    return render(request, 'orders/client_detail.html', {'client': client})

@login_required
def client_edit(request, pk):
    """Представление для редактирования информации о клиенте"""
    if not request.user.is_logistician():
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
    
    return render(request, 'orders/client_form.html', {'form': form, 'title': 'Редактирование клиента'})

def is_courier(user):
    return user.role == 'COURIER'

@login_required
@user_passes_test(is_courier)
def courier_orders(request):
    orders = Order.objects.filter(courier=request.user).order_by('-created_at')
    return render(request, 'orders/courier_orders.html', {'orders': orders})

@login_required
@user_passes_test(is_courier)
def courier_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, courier=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.Status.choices):
            order.status = new_status
            order.save()
            messages.success(request, 'Статус заказа успешно обновлен')
            return redirect('orders:courier_orders')
    return render(request, 'orders/courier_order_detail.html', {'order': order})

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
    if not request.user.is_logistician:
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
    if not request.user.is_logistician:
        return HttpResponseForbidden()
    
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        courier_id = request.POST.get('courier')
        if courier_id == 'None':
            # Снимаем курьера с заказа
            order.courier = None
            order.status = 'NEW'  # Возвращаем заказ в статус "Новый"
            order.save()
            messages.success(request, 'Курьер успешно снят с заказа, статус заказа изменен на "Новый"')
        elif courier_id:
            courier = get_object_or_404(User, pk=courier_id, role='COURIER')
            order.courier = courier
            order.status = 'ASSIGNED'
            order.save()
            messages.success(request, 'Курьер успешно назначен')
        else:
            messages.error(request, 'Пожалуйста, выберите курьера')
    
    return redirect('orders:order_detail', pk=order.pk)
