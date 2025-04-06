from django.db import models
from django.db.models import CharField
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser, BaseUserManager
from .utils import normalize_phone_number, normalize_phone_number_model
from PIL import Image
from django.conf import settings
from django.utils.translation import gettext as _

USER_RIGHTS = (('Admin', 'Admin'), ('IT_Admin', 'IT Admin'), ('User', 'User'))
USER_TYPE = (('Anonymous', 'Anonymous'), ('Registered', 'Registered'), ('Verified', 'Verified'))

class CustomUserManager(BaseUserManager):
    def create_user(self, email=None, contact_number=None, password=None, **extra_fields):
        if not email and not contact_number:
            raise ValueError("The user must have either an email or a contact number.")

        email = self.normalize_email(email) if email else None
        if contact_number:
            contact_number = normalize_phone_number(contact_number)

        user = self.model(email=email, contact_number=contact_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, contact_number=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not email and not contact_number:
            raise ValueError("Superusers must have either an email or a contact number.")
        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superusers must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superusers must have is_superuser=True.")

        return self.create_user(email=email, contact_number=contact_number, password=password, **extra_fields)


class CustomUser(AbstractUser):
    username = None  # Disable username
    current_session_key = models.CharField(max_length=40, blank=True, null=True)
    other_name = models.CharField(_('Other Names'),max_length=25, null=True, blank=True)
    email = models.EmailField(_('Email'),unique=True, null=True, blank=True)
    contact_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        validators=[normalize_phone_number_model],
    )
    contact_number_sec = models.CharField(_('Second Phone Number'),max_length=20, unique=True, null=True, blank=True)
    address = models.CharField(_('Address'),max_length=100, null=True, blank=True)
    date_of_birth = models.DateField(default=timezone.now)
    is_manager = models.BooleanField(default=False)
    staff_rights = models.CharField(max_length=50, choices=USER_RIGHTS, default='User')
    user_type = models.CharField(_('User Type'),max_length=50, choices=USER_TYPE, default='Registered')
    update_comments = models.CharField(max_length=500, null=True, blank=True)
    record_date = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1, related_name='added_users')
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')

    USERNAME_FIELD = 'email'  # Use email as the primary identifier
    REQUIRED_FIELDS = []  # No additional fields are required

    objects = CustomUserManager()

    def clean(self):
        # Ensure at least one of email or contact_number is provided
        if not self.email and not self.contact_number:
            raise ValidationError("Either email or contact number must be provided.")

    def save(self, *args, **kwargs):
        # Normalize phone number before saving
        if self.contact_number:
            self.contact_number = normalize_phone_number(self.contact_number)
        super().save(*args, **kwargs)

        # Resize profile image if necessary
        if self.image:
            img = Image.open(self.image.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.image.path)

    def __str__(self):
        return self.email if self.email else self.contact_number

