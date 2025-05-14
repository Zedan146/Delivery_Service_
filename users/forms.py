from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'role', 'phone_number', 'address')


class CustomUserChangeForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        # Русские метки
        self.fields['username'].label = 'Имя пользователя'
        self.fields['email'].label = 'Email'
        self.fields['phone_number'].label = 'Телефон'
        self.fields['address'].label = 'Адрес'
        self.fields['avatar'].label = 'Аватар'
        if 'role' in self.fields:
            self.fields['role'].label = 'Роль'
            # Только админ может менять роль
            if user and not (hasattr(user, 'is_admin') and user.is_admin()):
                self.fields['role'].disabled = True

    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'role', 'phone_number', 'address', 'avatar') 