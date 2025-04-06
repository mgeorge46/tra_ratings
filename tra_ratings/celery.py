import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tra_ratings.settings')

app = Celery('tra_ratings')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


CELERY_BEAT_SCHEDULE = {
    'weekly_rater_notification': {
        'task': 'notifications.tasks.send_weekly_top_rater_notifications',
        'schedule': crontab(day_of_week='sunday', hour=18, minute=0),
    },
}

