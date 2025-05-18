from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator, EmailValidator
import re

class Client(models.Model):
    """Модель для хранения информации о клиентах"""
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name='Отчество')
    phone_number = models.CharField(
        max_length=20,
        verbose_name='Телефон',
        db_index=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Номер телефона должен быть в формате: +7XXXXXXXXXX'
            )
        ]
    )
    email = models.EmailField(
        blank=True,
        verbose_name='Email',
        db_index=True,
        validators=[EmailValidator()]
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания', db_index=True)
    updated_at = models.DateTimeField(default=timezone.now, verbose_name='Дата обновления')
    
    def format_phone_number(self):
        """Форматирует номер телефона в формат +7 (XXX) XXX-XX-XX"""
        phone = re.sub(r'\D', '', self.phone_number)
        if phone.startswith('8'):
            phone = '7' + phone[1:]
        elif not phone.startswith('7'):
            phone = '7' + phone
        if len(phone) == 11:
            return f"+{phone[0]} ({phone[1:4]}) {phone[4:7]}-{phone[7:9]}-{phone[9:11]}"
        return self.phone_number
    
    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
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


class ClientAddress(models.Model):
    """Модель для хранения адресов клиентов"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='addresses', verbose_name='Клиент')
    address = models.TextField(verbose_name='Адрес')
    is_default = models.BooleanField(default=False, verbose_name='Адрес по умолчанию')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')
    updated_at = models.DateTimeField(default=timezone.now, verbose_name='Дата обновления')
    
    def save(self, *args, **kwargs):
        # Если этот адрес становится адресом по умолчанию,
        # сбрасываем флаг is_default у других адресов этого клиента
        if self.is_default:
            ClientAddress.objects.filter(
                client=self.client,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Адрес {self.client}: {self.address}"
    
    class Meta:
        verbose_name = 'Адрес клиента'
        verbose_name_plural = 'Адреса клиентов'
        ordering = ['-is_default', '-created_at']
