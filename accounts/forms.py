from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordResetForm
from .models import CustomUser
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from .utils import normalize_phone_number
from django.contrib.auth.forms import AuthenticationForm

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Email or Phone",
        widget=forms.TextInput(attrs={'autofocus': True}),
        help_text="Enter your email or phone number).",
    )

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=False, help_text="Optional. Enter a valid email address.")
    contact_number = forms.CharField(required=False, help_text="Optional. Enter a valid phone number.")

    class Meta:
        model = CustomUser
        fields = ['email', 'contact_number', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        contact_number = cleaned_data.get('contact_number')

        # Ensure at least one of email or contact_number is provided
        if not email and not contact_number:
            raise forms.ValidationError("Either email or contact number must be provided.")

        # Normalize phone number
        if contact_number:
            cleaned_data['contact_number'] = normalize_phone_number(contact_number)

        return cleaned_data


class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'other_name','email','contact_number', 'address', 'date_of_birth','image')


class CustomPasswordResetForm(forms.Form):
    new_password1 = forms.CharField(label='New Password', widget=forms.PasswordInput)
    new_password2 = forms.CharField(label='Confirm New Password', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("New passwords do not match.")
