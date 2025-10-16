from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from sms_app.sms_api import send_message
from django.utils import timezone
from datetime import timedelta
from rating.models import Rating
from .models import NotificationTemplate, Points, BonusAwardLog
from django.core.mail import mail_admins

@shared_task
def award_weekly_bonus():

    now = timezone.now()
    one_week_ago = now - timedelta(days=7)

    # Get users who rated this week
    active_users = Rating.objects.filter(
        created_at__gte=one_week_ago,
        user__isnull=False
    ).values_list('user_id', flat=True).distinct()

    top_raters = Points.objects.filter(user__id__in=active_users).order_by('-points')[:10]

    sms_template = NotificationTemplate.get_template("weekly_bonus_sms")
    email_template = NotificationTemplate.get_template("weekly_bonus_email")

    for profile in top_raters:
        user = profile.user

        # Check if already awarded
        if BonusAwardLog.objects.filter(user=user, week_start=one_week_ago.date()).exists():
            continue

        # Award points and log
        profile.points += 20
        profile.save()
        BonusAwardLog.objects.create(user=user, week_start=one_week_ago.date())

        context = {
            'name': user.first_name or user.email or user.contact_number,
            'points': 20
        }

        message = sms_template.format(**context)
        email_body = email_template.format(**context)

        if settings.ENABLE_BONUS_EMAIL and user.email:
            try:
                send_mail(
                    subject="🎉 You're a Top Rater!",
                    message=email_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
                continue
            except Exception as e:
                print(f"Email failed: {e}")

        if settings.ENABLE_BONUS_SMS and user.contact_number:
            try:
                send_message(None, user.contact_number, message)
            except Exception as e:
                print(f"SMS failed: {e}")

@shared_task
def check_weekly_activity_drop():
    now = timezone.now()
    this_week = Rating.objects.filter(created_at__gte=now - timedelta(days=7)).count()
    last_week = Rating.objects.filter(created_at__range=[now - timedelta(days=14), now - timedelta(days=7)]).count()

    if last_week > 0 and this_week < (0.5 * last_week):  # >50% drop
        msg = f"Ratings dropped by more than 50%.\nLast week: {last_week}, This week: {this_week}."
        mail_admins("Alert: Rating Activity Drop", msg)




