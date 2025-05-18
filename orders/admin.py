from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'client', 'courier', 'delivery_date', 'order_amount', 'delivery_cost', 'status', 'created_at')
    list_filter = ('status', 'delivery_date', 'created_at')
    search_fields = ('order_number', 'client__first_name', 'client__last_name', 'courier__username')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('order_number', 'client', 'courier', 'status')
        }),
        ('Детали доставки', {
            'fields': ('delivery_address', 'delivery_date', 'delivery_cost')
        }),
        ('Финансовая информация', {
            'fields': ('order_amount',)
        }),
        ('Дополнительно', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )
    ordering = ('-created_at',)
