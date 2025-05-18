from django.contrib import admin
from .models import CourierVehicle

@admin.register(CourierVehicle)
class CourierVehicleAdmin(admin.ModelAdmin):
    list_display = ('courier', 'vehicle', 'is_current', 'assigned_at', 'unassigned_at')
    list_filter = ('is_current', 'assigned_at', 'unassigned_at')
    search_fields = ('courier__username', 'vehicle__model', 'vehicle__plate_number')
    readonly_fields = ('assigned_at', 'unassigned_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('courier', 'vehicle', 'is_current')
        }),
        ('Даты', {
            'fields': ('assigned_at', 'unassigned_at')
        }),
    )
