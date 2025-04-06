from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['first_name','email', 'contact_number', 'is_staff', 'is_active','user_type', 'address']
    list_filter = ['is_staff', 'is_active']
    fieldsets = (
        (None, {'fields': ('first_name', 'last_name', 'other_name','email', 'contact_number', 'password','user_type', 'address')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'contact_number', 'password1', 'password2', 'is_staff', 'is_active' ,'user_type', 'address','first_name'),
        }),
    )
    search_fields = ['first_name','last_name', 'other_name','email', 'contact_number']
    ordering = ['email']  # Use 'email' or 'contact_number' instead of 'username'

admin.site.register(CustomUser, CustomUserAdmin)