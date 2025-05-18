from django.contrib.auth.models import AbstractUser
from django.db import models
import re

class CustomUser(AbstractUser):
    """Модель пользователя с расширенными полями"""
    
    class Role(models.TextChoices):
        """Роли пользователей в системе"""
        ADMIN = 'ADMIN', 'Администратор'
        LOGISTICIAN = 'LOGISTICIAN', 'Логист'
        COURIER = 'COURIER', 'Курьер'
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ADMIN,
        verbose_name='Роль'
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )
    address = models.TextField(
        blank=True,
        verbose_name='Адрес'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )
    
    def format_phone_number(self):
        """Форматирует номер телефона в формат +7 (XXX) XXX-XX-XX"""
        if not self.phone_number:
            return ''
            
        # Убираем все кроме цифр
        phone = re.sub(r'\D', '', self.phone_number)
        
        # Корректируем начало номера
        if phone.startswith('8'):
            phone = '7' + phone[1:]
        elif not phone.startswith('7'):
            phone = '7' + phone
            
        # Форматируем номер если он правильной длины
        if len(phone) == 11:
            return f"+{phone[0]} ({phone[1:4]}) {phone[4:7]}-{phone[7:9]}-{phone[9:11]}"
        return self.phone_number
    
    def save(self, *args, **kwargs):
        """Форматирует номер телефона перед сохранением"""
        if self.phone_number:
            self.phone_number = self.format_phone_number()
        super().save(*args, **kwargs)
    
    def is_admin(self):
        """Проверяет является ли пользователь администратором"""
        return self.role == self.Role.ADMIN
    
    def is_logistician(self):
        """Проверяет является ли пользователь логистом"""
        return self.role == self.Role.LOGISTICIAN
    
    def is_courier(self):
        """Проверяет является ли пользователь курьером"""
        return self.role == self.Role.COURIER
