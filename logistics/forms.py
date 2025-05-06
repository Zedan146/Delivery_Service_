from django import forms
from .models import Vehicle, CourierVehicle

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['type', 'model', 'color', 'plate_number', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class CourierVehicleForm(forms.ModelForm):
    class Meta:
        model = CourierVehicle
        fields = ['courier', 'vehicle'] 