from django import forms
from .models import Client, ClientAddress
import re

class ClientForm(forms.ModelForm):
    """Форма для создания и редактирования клиента"""
    class Meta:
        model = Client
        fields = ['first_name', 'last_name', 'middle_name', 'phone_number', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        # Удаляем все кроме + и цифр
        phone = re.sub(r'[^\d+]', '', phone)
        # Приводим к формату +7XXXXXXXXXX
        if phone.startswith('8'):
            phone = '+7' + phone[1:]
        elif not phone.startswith('+7'):
            phone = '+7' + phone.lstrip('+')
        return phone

class ClientAddressForm(forms.ModelForm):
    """Форма для создания и редактирования адреса клиента"""
    class Meta:
        model = ClientAddress
        fields = [
            'city', 'street', 'house_number', 'apartment', 'postal_code', 'courier_notes', 'is_default'
        ]
        widgets = {
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'street': forms.TextInput(attrs={'class': 'form-control'}),
            'house_number': forms.TextInput(attrs={'class': 'form-control'}),
            'apartment': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'courier_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ClientAddressInlineFormSet(forms.models.inlineformset_factory(
    Client,
    ClientAddress,
    form=ClientAddressForm,
    extra=1,
    can_delete=True
)):
    """FormSet для управления адресами клиента"""
    def clean(self):
        super().clean()
        # Проверяем, что хотя бы один адрес отмечен как адрес по умолчанию
        has_default = False
        for form in self.forms:
            if form.cleaned_data.get('is_default'):
                has_default = True
                break
        
        if not has_default and self.forms:
            raise forms.ValidationError('Необходимо указать адрес по умолчанию') 