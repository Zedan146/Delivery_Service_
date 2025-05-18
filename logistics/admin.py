from django.contrib import admin
from .models import Vehicle, CourierVehicle, DeliveryReport, CourierPerformance

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('get_type_display', 'model', 'color', 'plate_number', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('model', 'plate_number', 'description')
    fieldsets = (
        ('Основная информация', {
            'fields': ('type', 'model', 'color', 'plate_number')
        }),
        ('Дополнительно', {
            'fields': ('description', 'is_active')
        }),
    )

@admin.register(CourierVehicle)
class CourierVehicleAdmin(admin.ModelAdmin):
    list_display = ('courier', 'vehicle', 'assigned_date', 'is_current')
    list_filter = ('is_current', 'assigned_date')
    search_fields = ('courier__username', 'vehicle__model', 'vehicle__plate_number')
    readonly_fields = ('assigned_date',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('courier', 'vehicle', 'is_current')
        }),
        ('Даты', {
            'fields': ('assigned_date',)
        }),
    )

@admin.register(DeliveryReport)
class DeliveryReportAdmin(admin.ModelAdmin):
    list_display = ('order', 'courier', 'vehicle', 'delivery_started', 'delivery_completed')
    list_filter = ('delivery_started', 'delivery_completed')
    search_fields = ('order__order_number', 'courier__username', 'vehicle__model')
    readonly_fields = ('delivery_started', 'delivery_completed')
    fieldsets = (
        ('Основная информация', {
            'fields': ('order', 'courier', 'vehicle')
        }),
        ('Время доставки', {
            'fields': ('delivery_started', 'delivery_completed')
        }),
        ('Дополнительно', {
            'fields': ('delivery_notes',)
        }),
    )

@admin.register(CourierPerformance)
class CourierPerformanceAdmin(admin.ModelAdmin):
    list_display = ('courier', 'date', 'orders_completed', 'total_delivery_time', 'total_earnings')
    list_filter = ('date',)
    search_fields = ('courier__username',)
    readonly_fields = ('total_delivery_time', 'total_earnings')
    fieldsets = (
        ('Основная информация', {
            'fields': ('courier', 'date', 'orders_completed')
        }),
        ('Статистика', {
            'fields': ('total_delivery_time', 'total_earnings')
        }),
    )
