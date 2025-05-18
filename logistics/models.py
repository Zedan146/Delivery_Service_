from django.db import models
from django.conf import settings
from orders.models import Order
from django.utils import timezone
from django.core.cache import cache

class Vehicle(models.Model):
    """Модель для хранения информации о транспортных средствах"""
    class Type(models.TextChoices):
        BICYCLE = 'BICYCLE', 'Велосипед'
        MOTORCYCLE = 'MOTORCYCLE', 'Мотоцикл'
        CAR = 'CAR', 'Машина'
        TRUCK = 'TRUCK', 'Грузовик'
    
    type = models.CharField(max_length=20, choices=Type.choices, verbose_name='Тип транспортного средства')
    model = models.CharField(max_length=100, verbose_name='Модель')
    color = models.CharField(max_length=50, verbose_name='Цвет')
    plate_number = models.CharField(max_length=20, blank=True, verbose_name='Номер машины')
    description = models.TextField(blank=True, verbose_name='Описание')
    is_active = models.BooleanField(default=True, verbose_name='Активность', db_index=True)
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания', db_index=True)
    updated_at = models.DateTimeField(default=timezone.now, verbose_name='Дата обновления')
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.model}"

    def get_status_display_ext(self):
        cache_key = f'vehicle_status_{self.id}'
        cached_status = cache.get(cache_key)
        if cached_status:
            return cached_status

        if not self.is_active:
            status = ('В ремонте', 'danger')
        else:
            current_assignment = self.couriervehicle_set.filter(is_current=True).first()
            if not current_assignment:
                status = ('Не назначено', 'secondary')
            else:
                in_progress = Order.objects.filter(
                    courier=current_assignment.courier,
                    status=Order.Status.IN_PROGRESS
                ).exists()
                status = ('В работе', 'primary') if in_progress else ('Назначено', 'success')
        
        cache.set(cache_key, status, 300)  # Кэшируем на 5 минут
        return status

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        # Инвалидируем кэш при сохранении
        cache.delete(f'vehicle_status_{self.id}')
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Транспортное средство'
        verbose_name_plural = 'Транспортные средства'
        ordering = ['type', 'model']


class CourierVehicle(models.Model):
    """Модель для хранения информации о курьерских транспортных средствах"""
    courier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Курьер')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, verbose_name='Транспортное средство')
    assigned_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата назначения')
    is_current = models.BooleanField(default=True, verbose_name='Текущее назначение')
    
    def __str__(self):
        return f"{self.courier.username} - {self.vehicle}"

    class Meta:
        verbose_name = 'Назначение транспорта'
        verbose_name_plural = 'Назначения транспорта'
        ordering = ['-assigned_date']


class DeliveryReport(models.Model):
    """Модель для хранения информации о доставке"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, verbose_name='Заказ')
    courier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Курьер')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, verbose_name='Транспортное средство')
    delivery_started = models.DateTimeField(verbose_name='Время начала доставки')
    delivery_completed = models.DateTimeField(null=True, blank=True, verbose_name='Время завершения доставки')
    delivery_notes = models.TextField(blank=True, verbose_name='Примечания к доставке')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')
    updated_at = models.DateTimeField(default=timezone.now, verbose_name='Дата обновления')
    
    def __str__(self):
        return f"Delivery Report for {self.order}"
    
    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Отчет о доставке'
        verbose_name_plural = 'Отчеты о доставках'
        ordering = ['-delivery_started']


class CourierPerformance(models.Model):
    """Модель для хранения информации о производительности курьеров"""
    courier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Курьер')
    date = models.DateField(verbose_name='Дата')
    orders_completed = models.IntegerField(default=0, verbose_name='Выполнено заказов')
    total_delivery_time = models.DurationField(default=0, verbose_name='Общее время доставки')
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Общий заработок')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')
    updated_at = models.DateTimeField(default=timezone.now, verbose_name='Дата обновления')
    
    def calculate_efficiency(self):
        if self.total_delivery_time.total_seconds() > 0:
            return self.orders_completed / (self.total_delivery_time.total_seconds() / 3600)
        return 0
    
    def __str__(self):
        return f"Performance Report - {self.courier.username} ({self.date})"
    
    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Производительность курьера'
        verbose_name_plural = 'Производительность курьеров'
        ordering = ['-date']
        unique_together = ['courier', 'date']
