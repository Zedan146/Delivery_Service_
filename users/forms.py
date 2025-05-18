from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'role', 'phone_number', 'address')
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'placeholder': 'Введите номер телефона'
            })
        }


class CustomUserChangeForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        # Русские метки
        self.fields['username'].label = 'Имя пользователя'
        self.fields['email'].label = 'Email'
        self.fields['phone_number'].label = 'Телефон'
        self.fields['address'].label = 'Адрес'
        if 'avatar' in self.fields:
            self.fields['avatar'].label = 'Аватар'
        
        # Добавляем подсказку для номера телефона
        self.fields['phone_number'].widget.attrs.update({
            'placeholder': 'Введите номер телефона'
        })
        
        # Управление полями в зависимости от роли пользователя
        if user:
            # Только админ может менять роль
            if 'role' in self.fields and not (hasattr(user, 'is_admin') and user.is_admin()):
                self.fields['role'].disabled = True

    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'role', 'phone_number', 'address', 'avatar') 
        fieldsets = (
            (None, {'fields': ('username', 'password')}),
            ('Персональная информация', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'address', 'avatar')}),
            ('Роли и разрешения', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ) 

class StaffCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'role')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Пароли не совпадают')
        return password2

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role not in [CustomUser.Role.COURIER, CustomUser.Role.LOGISTICIAN]:
            raise forms.ValidationError('Можно выбрать только роль Курьер или Логист')
        return role

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user 