from django.contrib.auth.models import AbstractUser
from django.db import models
import re

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Администратор'
        LOGISTICIAN = 'LOGISTICIAN', 'Логист'
        COURIER = 'COURIER', 'Курьер'
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.COURIER
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )
    address = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Аватар')
    
    def format_phone_number(self):
        """Форматирует номер телефона в формат +7 (XXX) XXX-XX-XX"""
        if not self.phone_number:
            return ''
            
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
        if self.phone_number:
            self.phone_number = self.format_phone_number()
        super().save(*args, **kwargs)
    
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    def is_logistician(self):
        return self.role == self.Role.LOGISTICIAN
    
    def is_courier(self):
        return self.role == self.Role.COURIER
