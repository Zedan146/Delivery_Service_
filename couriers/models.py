from django.db import models
from django.conf import settings
from logistics.models import Vehicle

class CourierVehicle(models.Model):
    courier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courier_vehicles')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='courier_vehicles')
    is_current = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    unassigned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['courier', 'vehicle']
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.courier.get_full_name()} - {self.vehicle}"
