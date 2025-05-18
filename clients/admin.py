from django.contrib import admin

from .models import Client, ClientAddress

class ClientAddressInline(admin.TabularInline):
    model = ClientAddress
    extra = 1
    fields = ('address', 'is_default')

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'middle_name', 'phone_number', 'email')
    search_fields = ('last_name', 'first_name', 'phone_number', 'email')
    list_filter = ('created_at',)
    inlines = [ClientAddressInline]

@admin.register(ClientAddress)
class ClientAddressAdmin(admin.ModelAdmin):
    list_display = ('client', 'address', 'is_default', 'created_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('client__last_name', 'client__first_name', 'address')
    raw_id_fields = ('client',)
