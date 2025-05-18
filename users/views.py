from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserChangeForm


@login_required
def profile(request):
    """Представление для просмотра профиля пользователя"""
    return render(request, 'users/profile.html')


@login_required
def profile_edit(request):
    """Представление для редактирования профиля пользователя"""
    # Проверяем, что пользователь редактирует свой профиль
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            # Проверяем права доступа
            if not request.user.is_admin() and 'password' in form.cleaned_data:
                messages.error(request, 'У вас нет прав для изменения пароля')
                return redirect('users:profile')
            
            form.save()
            messages.success(request, 'Профиль успешно обновлен')
            return redirect('users:profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    
    return render(request, 'users/profile_edit.html', {'form': form})
