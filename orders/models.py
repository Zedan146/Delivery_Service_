from django.db import models
from django.conf import settings
from decimal import Decimal
import re

class Client(models.Model):
    """Модель для хранения информации о клиентах"""
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name='Отчество')
    phone_number = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    address = models.TextField(verbose_name='Адрес')
    
    def format_phone_number(self):
        """Форматирует номер телефона в формат +7 (XXX) XXX-XX-XX"""
        # Удаляем все нецифровые символы из номера
        phone = re.sub(r'\D', '', self.phone_number)
        
        # Если номер начинается с 8, заменяем на 7
        if phone.startswith('8'):
            phone = '7' + phone[1:]
        # Если номер не начинается с 7, добавляем 7 в начало
        elif not phone.startswith('7'):
            phone = '7' + phone
            
        # Проверяем длину номера
        if len(phone) == 11:
            return f"+{phone[0]} ({phone[1:4]}) {phone[4:7]}-{phone[7:9]}-{phone[9:11]}"
        return self.phone_number
    
    def save(self, *args, **kwargs):
        # Форматируем номер телефона перед сохранением
        self.phone_number = self.format_phone_number()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.last_name} {self.first_name}"
    
    def get_full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}"
    
    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['last_name', 'first_name']


class Order(models.Model):
    """Модель для хранения информации о заказах"""
    class Status(models.TextChoices):
        NEW = 'NEW', 'Новый'
        ASSIGNED = 'ASSIGNED', 'Назначен'
        IN_PROGRESS = 'IN_PROGRESS', 'В процессе'
        DELIVERED = 'DELIVERED', 'Доставлен'
        CANCELLED = 'CANCELLED', 'Отменен'
    
    order_number = models.CharField(max_length=50, unique=True, verbose_name='Номер заказа')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='orders', verbose_name='Клиент')
    courier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_orders'
    )
    delivery_address = models.TextField(verbose_name='Адрес доставки')
    order_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма заказа')
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Стоимость доставки')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания заказа')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления заказа')
    delivery_date = models.DateField(verbose_name='Дата доставки')
    notes = models.TextField(blank=True, verbose_name='Комментарий клиента')

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
