from django.contrib.auth import get_user_model
from redis import Redis
from django.conf import settings
from celery import shared_task
from firebase_admin import messaging
from points.models import Points
from tra_not.models import FirebaseDeviceToken

User = get_user_model()

r = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    ssl=True
)

@shared_task
def cache_top_contributors():
    top_users = Points.objects.order_by('-weekly_points')[:10]
    r.delete("top_contributors")

    for user_points in top_users:
        user_id = str(user_points.user_id)
        r.hset("top_contributors", user_id, user_points.weekly_points)

    print("Top contributors cached.")


@shared_task
def send_weekly_top_rater_notifications():
    cached_data = r.hgetall("top_contributors")

    for user_id, score in cached_data.items():
        user_id = int(user_id)
        tokens = FirebaseDeviceToken.objects.filter(user_id=user_id).values_list('token', flat=True)

        for token in tokens:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title="🎉 You're a Top Contributor!",
                        body=f"You earned {int(score)} points this week. Keep it up!"
                    ),
                    token=token
                )
                messaging.send(message)
            except Exception as e:
                print(f"Failed to send to {token}: {e}")
