import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tra_ratings.settings')

app = Celery('tra_ratings')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
