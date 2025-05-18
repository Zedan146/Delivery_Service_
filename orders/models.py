from django.db import models
from django.conf import settings
from decimal import Decimal

from clients.models import Client, ClientAddress


class Order(models.Model):
    """Модель для хранения информации о заказах"""
    class Status(models.TextChoices):
        NEW = 'NEW', 'Новый'
        ASSIGNED = 'ASSIGNED', 'Назначен'
        IN_PROGRESS = 'IN_PROGRESS', 'В процессе'
        DELIVERED = 'DELIVERED', 'Доставлен'
        CANCELLED = 'CANCELLED', 'Отменен'
    
    order_number = models.CharField(max_length=50, unique=True, verbose_name='Номер заказа', db_index=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='orders', verbose_name='Клиент')
    delivery_address = models.ForeignKey(
        ClientAddress,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Адрес доставки'
    )
    courier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_orders',
        verbose_name='Курьер'
    )
    order_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма заказа')
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Стоимость доставки')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name='Статус',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания', db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    delivery_date = models.DateField(verbose_name='Дата доставки', db_index=True)
    notes = models.TextField(blank=True, verbose_name='Комментарии')

    def create_order_number(self):
        # Создание номера заказа
        last_order_number = Order.objects.order_by('-order_number').first()
        if last_order_number:
            last_number = int(last_order_number.order_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        return f"ORD-{new_number:03d}"
        
    def calculate_delivery_cost(self):
        # Расчет стоимости доставки

        # Базовая стоимость доставки
        base_cost = Decimal('200.00')
        
        # Добавляем 5% от суммы заказа
        order_percentage = self.order_amount * Decimal('0.05')
        
        self.delivery_cost = base_cost + order_percentage
        return self.delivery_cost
    
    def save(self, *args, **kwargs):
        if not self.delivery_cost:
            self.delivery_cost = self.calculate_delivery_cost()
        if not self.order_number:
            self.order_number = self.create_order_number()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
