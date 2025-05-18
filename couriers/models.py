from django.db import models
from django.conf import settings
from logistics.models import Vehicle

class CourierVehicle(models.Model):
    courier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courier_vehicles', verbose_name='Курьер')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='courier_vehicles', verbose_name='Транспортное средство')
    is_current = models.BooleanField(default=True, verbose_name='Текущее назначение')
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата назначения')
    unassigned_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата снятия с назначения')

    class Meta:
        verbose_name = 'Назначение транспорта'
        verbose_name_plural = 'Назначения транспорта'
        unique_together = ['courier', 'vehicle']
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.courier.get_full_name()} - {self.vehicle}"
