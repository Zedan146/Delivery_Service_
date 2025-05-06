from django import forms
from .models import Order, Client

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['first_name', 'last_name', 'middle_name', 'phone_number', 'email', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['client', 'delivery_address', 'order_amount', 'delivery_date', 'notes']
        widgets = {
            'delivery_address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'delivery_date': forms.DateInput(attrs={'type': 'date'}),
        } 