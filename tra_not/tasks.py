from django.contrib.auth import get_user_model
from django.core.cache import cache
from celery import shared_task
from firebase_admin import messaging
from points.models import Points
from tra_not.models import FirebaseDeviceToken

User = get_user_model()

TOP_CONTRIBUTORS_CACHE_KEY = "top_contributors"
TOP_CONTRIBUTORS_LIMIT = 10

@shared_task
def cache_top_contributors():
    top_users = Points.objects.order_by('-points')[:TOP_CONTRIBUTORS_LIMIT]

    # Use Django cache framework
    contributors = {
        str(user_points.user_id): user_points.points
        for user_points in top_users
    }
    cache.set(TOP_CONTRIBUTORS_CACHE_KEY, contributors, timeout=None)  # No expiry
    print("Top contributors cached.")


@shared_task
def send_weekly_top_rater_notifications():
    cached_data = cache.get(TOP_CONTRIBUTORS_CACHE_KEY, {})

    for user_id_str, score in cached_data.items():
        user_id = int(user_id_str)
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
