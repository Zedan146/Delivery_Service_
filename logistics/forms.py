from django import forms
from .models import Vehicle, CourierVehicle
from users.models import CustomUser

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['type', 'model', 'color', 'plate_number', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class CourierVehicleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Показывать только курьеров
        self.fields['courier'].queryset = CustomUser.objects.filter(role=CustomUser.Role.COURIER, is_active=True)
        self.fields['courier'].label = 'Курьер'
        self.fields['vehicle'].label = 'Транспортное средство'
        self.fields['courier'].label_from_instance = lambda obj: f'{obj.last_name} {obj.first_name}'
        # Показывать только свободные транспортные средства
        busy_vehicles = CourierVehicle.objects.filter(is_current=True).values_list('vehicle_id', flat=True)
        self.fields['vehicle'].queryset = Vehicle.objects.exclude(id__in=busy_vehicles)

    def clean_vehicle(self):
        vehicle = self.cleaned_data['vehicle']
        if CourierVehicle.objects.filter(vehicle=vehicle, is_current=True).exists():
            raise forms.ValidationError('Это транспортное средство уже назначено другому курьеру!')
        return vehicle

    class Meta:
        model = CourierVehicle
        fields = ['courier', 'vehicle'] 