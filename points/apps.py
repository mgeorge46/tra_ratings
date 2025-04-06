from django.apps import AppConfig
from django.db.models.signals import post_migrate

class PointsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'points'

    def ready(self):
        import points.signals  # import signals
        post_migrate.connect(create_dashboard_permission, sender=self)

def create_dashboard_permission(sender, **kwargs):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from .models import Points

    # Restrict Dashboard Access by Role/Permission
    content_type = ContentType.objects.get_for_model(Points)
    Permission.objects.get_or_create(
        codename='can_view_dashboard',
        name='Can View Admin Dashboard',
        content_type=content_type
    )
