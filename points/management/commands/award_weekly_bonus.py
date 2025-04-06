from django.core.management.base import BaseCommand
from points.models import Points
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = "Award weekly bonus to top 10 raters and notify them via email"

    def handle(self, *args, **kwargs):
        top_raters = Points.objects.select_related('user').order_by('-points')[:10]
        awarded_emails = []

        for profile in top_raters:
            profile.points += 20
            profile.save()

            email = profile.user.email
            if email:
                awarded_emails.append(email)
                send_mail(
                    subject="🎉 You're a Top Rater! Weekly Bonus Awarded",
                    message=(
                        f"Hi {profile.user.first_name or profile.user.email},\n\n"
                        "You've been ranked among the top 10 raters this week and earned a bonus of 20 points!\n\n"
                        "Keep rating to climb even higher!\n\n"
                        "Thank you for making our platform better."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,
                )

        self.stdout.write(
            self.style.SUCCESS(f"Weekly bonus awarded and emails sent to: {', '.join(awarded_emails)}")
        )
