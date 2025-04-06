from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomPasswordResetForm
from django.utils import timezone
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required
def reset_password(request):
    user = request.user

    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            user.set_password(new_password)
            # Update admin_password_reset field with username and timestamp
            user.user_password_reset = f'{request.user.username} ({timezone.now()})'
            user.save()
            messages.success(request, 'Password Changed Successfully, Please Use the new Password to login')
            return redirect('profile')
        else:
            messages.error(request, 'Passwords do not match')

    else:
        form = CustomPasswordResetForm()

    return render(request, 'accounts/user_profile_preset.html', {'form': form, 'user': user})

