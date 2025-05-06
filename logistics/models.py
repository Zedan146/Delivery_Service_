from django.db import models
from django.conf import settings
from orders.models import Order

class Vehicle(models.Model):
    """Модель для хранения информации о транспортных средствах"""
    class Type(models.TextChoices):
        BICYCLE = 'BICYCLE', 'Bicycle'
        MOTORCYCLE = 'MOTORCYCLE', 'Motorcycle'
        CAR = 'CAR', 'Car'
    
    type = models.CharField(max_length=20, choices=Type.choices)
    model = models.CharField(max_length=100)
    color = models.CharField(max_length=50)
    plate_number = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.model}"


class CourierVehicle(models.Model):
    """Модель для хранения информации о курьерских транспортных средствах"""
    courier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    assigned_date = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.courier.username} - {self.vehicle}"


class DeliveryReport(models.Model):
    """Модель для хранения информации о доставке"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    courier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    delivery_started = models.DateTimeField()
    delivery_completed = models.DateTimeField(null=True, blank=True)
    delivery_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Delivery Report for {self.order}"
    
    class Meta:
        ordering = ['-delivery_started']


class CourierPerformance(models.Model):
    """Модель для хранения информации о производительности курьеров"""
    courier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    orders_completed = models.IntegerField(default=0)
    total_delivery_time = models.DurationField(default=0)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def calculate_efficiency(self):
        if self.total_delivery_time.total_seconds() > 0:
            return self.orders_completed / (self.total_delivery_time.total_seconds() / 3600)
        return 0
    
    def __str__(self):
        return f"Performance Report - {self.courier.username} ({self.date})"
    
    class Meta:
        unique_together = ['courier', 'date']
        ordering = ['-date']
