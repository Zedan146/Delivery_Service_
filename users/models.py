from django.contrib.auth.models import AbstractUser
from django.db import models

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
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Аватар')
    
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    def is_logistician(self):
        return self.role == self.Role.LOGISTICIAN
    
    def is_courier(self):
        return self.role == self.Role.COURIER
