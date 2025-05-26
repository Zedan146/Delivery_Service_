from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from clients.models import Client
from clients.forms import ClientForm, ClientAddressInlineFormSet
from orders.models import Order

# Create your views here.

@login_required
def client_list(request):
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для просмотра списка клиентов')
        return redirect('home')
    clients = Client.objects.all()
    for client in clients:
        client.default_address = client.addresses.filter(is_default=True).first()
    return render(request, 'clients/client_list.html', {'clients': clients})

@login_required
def client_create(request):
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для создания клиентов')
        return redirect('clients:client_list')
    if request.method == 'POST':
        form = ClientForm(request.POST)
        formset = ClientAddressInlineFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            client = form.save()
            formset.instance = client
            formset.save()
            messages.success(request, 'Клиент успешно создан')
            return redirect('clients:client_detail', pk=client.pk)
    else:
        form = ClientForm()
        formset = ClientAddressInlineFormSet()
    return render(request, 'clients/client_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Создание клиента'
    })

@login_required
def client_detail(request, pk):
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для просмотра информации о клиентах')
        return redirect('clients:client_list')
    client = get_object_or_404(Client, pk=pk)
    active_orders_count = client.orders.exclude(status__in=['DELIVERED', 'CANCELLED']).count()
    return render(request, 'clients/client_detail.html', {'client': client, 'active_orders_count': active_orders_count})

@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if not (request.user.is_logistician() or request.user.is_admin()):
        messages.error(request, 'У вас нет прав для редактирования клиентов')
        return redirect('clients:client_list')
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        formset = ClientAddressInlineFormSet(request.POST, instance=client)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Клиент успешно обновлен')
            return redirect('clients:client_detail', pk=client.pk)
    else:
        form = ClientForm(instance=client)
        formset = ClientAddressInlineFormSet(instance=client)
    return render(request, 'clients/client_form.html', {
        'form': form,
        'formset': formset,
    })

@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if not request.user.is_admin:
        messages.error(request, 'У вас нет прав для удаления клиентов')
        return redirect('clients:client_list')
    
    active_orders_count = client.orders.exclude(status__in=['DELIVERED', 'CANCELLED']).count()
    
    if active_orders_count > 0 and request.method == 'POST':
        messages.error(request, 'Нельзя удалить клиента с активными заказами. Сначала завершите или отмените все заказы.')
        return redirect('clients:client_detail', pk=client.pk)
    
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Клиент успешно удалён')
        return redirect('clients:client_list')
    
    return render(request, 'clients/client_confirm_delete.html', {'client': client, 'active_orders_count': active_orders_count})
