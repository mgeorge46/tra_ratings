from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _
from points.models import Points
from .utils import validate_ug_plate_format

MOTOR_TYPES = [
    ('motorcycle', 'Boda Boda'),
    ('car', 'Car'),
    ('bus', 'Bus'),
    ('truck', 'Truck'),
    ('taxi', 'Taxi'),
    ('tuku', 'Tuku Tuku'),
    ('coaster', 'Coaster'),
]


class MotorCar(models.Model):
    motor_car_number = models.CharField(
        max_length=12,  # Enough to store 'UMA 1234L' (9 chars total)
        unique=True,
        validators=[validate_ug_plate_format],
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,  # Allow null for anonymous users
        blank=True
    )
    is_conflicted = models.BooleanField(default=False)
    motor_type = models.CharField(max_length=50, choices=MOTOR_TYPES, blank=False, null=False)

    def clean(self):
        super().clean()
        # Optionally re-format using the central validator
        self.motor_car_number = validate_ug_plate_format(self.motor_car_number)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.motor_car_number} ({self.motor_type})"


class Rating(models.Model):
    motor_car = models.ForeignKey('MotorCar', on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    user_type = models.CharField(max_length=50, default="Anonymous")
    ip_address = models.GenericIPAddressField(_('User IP Address'), null=True, blank=True)
    score = models.DecimalField(_('Rating Score'), max_digits=3, decimal_places=1, default=0.0)
    motor_type = models.CharField(_('Motor Type'), max_length=50, choices=MOTOR_TYPES)
    system_comments = models.TextField(_('System Comment'))
    comment = models.TextField(_('Comments'), null=True, blank=True)
    location = models.CharField(_('Location'), max_length=255)
    rate_method = models.CharField(_('Method Used'), max_length=25, default='Text')
    device_id = models.CharField(_('Device ID'), max_length=255, null=True, blank=True)
    is_anonymous = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating for {self.motor_car.motor_car_number} - {self.score} stars"

    def save(self, *args, **kwargs):
        # Set user_type
        if self.user and hasattr(self.user, 'user_type'):
            self.user_type = self.user.user_type
        else:
            self.user_type = "Anonymous"

        if not self.location:
            print("NO LOCATION - not saving rating or awarding points.")
            return  # or set a default for now: self.location = "Unknown"

        super().save(*args, **kwargs)

        # Award points only for Registered or Verified users
        valid_user = self.user and self.user.user_type in ["Registered", "Verified"]
        if valid_user and not self.is_anonymous:
            points, _ = Points.objects.get_or_create(user=self.user)
            points.award_points_for_rating()


class MotorCarConflict(models.Model):
    motor_car = models.ForeignKey('MotorCar', on_delete=models.CASCADE, related_name='conflicts')
    reported_type = models.CharField(max_length=50, choices=MOTOR_TYPES, blank=False, null=False)
    timestamp = models.DateTimeField(auto_now_add=True)  # When the conflict was recorded
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,  # Allow null for anonymous users
        blank=True
    )

    def __str__(self):
        return f"Conflict for {self.motor_car.motor_car_number}: {self.reported_type} at {self.timestamp}"


class AverageRating(models.Model):
    motor_car = models.OneToOneField('MotorCar', on_delete=models.CASCADE, related_name='average_rating')
    average_score_anonymous = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    average_score_registered = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    average_score_verified = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    top_three_system_comments_anonymous = models.TextField(null=True, blank=True)
    top_three_system_comments_registered = models.TextField(null=True, blank=True)
    top_three_system_comments_verified = models.TextField(null=True, blank=True)
    number_of_ratings_anonymous = models.PositiveBigIntegerField(default=0)
    number_of_ratings_registered = models.PositiveBigIntegerField(default=0)
    number_of_ratings_verified = models.PositiveBigIntegerField(default=0)
    last_comments_anonymous = models.TextField(null=True, blank=True)
    last_comments_registered = models.TextField(null=True, blank=True)
    last_comments_verified = models.TextField(null=True, blank=True)
    date_last_comments_anonymous = models.DateTimeField(null=True, blank=True)
    date_last_comments_registered = models.DateTimeField(null=True, blank=True)
    date_last_comments_verified = models.DateTimeField(null=True, blank=True)
    frequent_location_anonymous = models.CharField(_('Frequent Location Anonymous'), max_length=255, null=True, blank=True)
    frequent_location_registered = models.CharField(_('Frequent Location Registered'), max_length=255, null=True, blank=True)
    frequent_location_verified = models.CharField(_('Frequent Location Verified'), max_length=255, null=True, blank=True)
    last_location_anonymous = models.CharField(_('Last Location Anonymous'), max_length=255, null=True, blank=True)
    last_location_registered = models.CharField(_('Last Location Registered'), max_length=255, null=True, blank=True)
    last_location_verified = models.CharField(_('Last Location Verified'), max_length=255, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (f"Average for {self.motor_car.motor_car_number} - "
                f"Anonymous: {self.average_score_anonymous}, "
                f"Registered: {self.average_score_registered}, "
                f"Verified: {self.average_score_verified}")


class ArchivedRating(models.Model):
    motor_car = models.ForeignKey('MotorCar', on_delete=models.CASCADE, related_name='archived_ratings')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    user_type = models.CharField(max_length=50, default="Anonymous")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    score = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    motor_type = models.CharField(max_length=50, choices=MOTOR_TYPES, blank=False, null=False)
    system_comments = models.CharField(max_length=50, blank=False, null=False)
    comment = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=255, null=False, blank=False)
    device_id = models.CharField(max_length=255, null=True, blank=True)
    is_anonymous = models.BooleanField(default=True)
    created_at = models.DateTimeField()  # Keep original timestamp
    archived_at = models.DateTimeField(auto_now_add=True)  # Timestamp for when it was archived

    def __str__(self):
        return f"Archived Rating for {self.motor_car.motor_car_number} - {self.score} stars"
