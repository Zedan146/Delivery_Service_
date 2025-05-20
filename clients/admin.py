from django.contrib import admin

from .models import Client, ClientAddress

class ClientAddressInline(admin.TabularInline):
    model = ClientAddress
    extra = 1
    fields = ('city', 'street', 'house_number', 'apartment', 'postal_code', 'courier_notes', 'is_default')

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'middle_name', 'phone_number', 'email')
    search_fields = ('last_name', 'first_name', 'phone_number', 'email')
    list_filter = ('created_at',)
    inlines = [ClientAddressInline]

@admin.register(ClientAddress)
class ClientAddressAdmin(admin.ModelAdmin):
    list_display = ('client', 'get_full_address', 'is_default', 'created_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('client__last_name', 'client__first_name', 'city', 'street', 'house_number', 'apartment', 'postal_code')
    raw_id_fields = ('client',)

    def get_full_address(self, obj):
        return obj.get_full_address()
    get_full_address.short_description = 'Адрес'
