from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from accounts.models import CustomUser
from .models import Points
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps

# 🔹 1. Create Points object when user is created
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_points(sender, instance, created, **kwargs):
    if created:
        points, _ = Points.objects.get_or_create(user=instance)
        if not points.registration_awarded:
            points.points += 2
            points.registration_awarded = True
            points.update_level()

# 🔹 2. Award 10 bonus points when user_type changes to Verified
@receiver(pre_save, sender=CustomUser)
def handle_user_type_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        previous = CustomUser.objects.get(pk=instance.pk)
    except CustomUser.DoesNotExist:
        return

    if previous.user_type != instance.user_type and instance.user_type == "Verified":
        points, _ = Points.objects.get_or_create(user=instance)
        if not points.verification_awarded:
            points.points += 10
            points.verification_awarded = True
            points.update_level()









