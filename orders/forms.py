from django import forms

from .models import Order
from clients.models import Client, ClientAddress


class OrderForm(forms.ModelForm):
    """Форма для создания и редактирования заказа"""
    class Meta:
        model = Order
        fields = ['client', 'delivery_address', 'order_amount', 'delivery_date', 'notes']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'delivery_address': forms.Select(attrs={'class': 'form-control'}),
            'order_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Если клиент выбран, показываем только его адреса
        if 'client' in self.data:
            try:
                client_id = int(self.data.get('client'))
                self.fields['delivery_address'].queryset = ClientAddress.objects.filter(
                    client_id=client_id
                ).order_by('-is_default')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.client:
            self.fields['delivery_address'].queryset = ClientAddress.objects.filter(
                client=self.instance.client
            ).order_by('-is_default')
        else:
            self.fields['delivery_address'].queryset = ClientAddress.objects.none() 