from django.conf import settings
from django.db import models
from datetime import date
from django.utils.translation import gettext as _

class Points(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="points")
    points = models.IntegerField(default=0)
    level = models.CharField(max_length=50, default="Novice Rater")
    registration_awarded = models.BooleanField(default=False)
    verification_awarded = models.BooleanField(default=False)
    last_rating_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True)

    LEVELS = [
        (0, "Novice Rater"), (104, "Junior Rater"), (251, "Intermediate Rater"),
        (456, "Advanced Rater"), (893, "Expert Rater"), (1557, "Master Rater")
    ]

    def update_level(self):
        for point_threshold, level_name in self.LEVELS:
            if self.points >= point_threshold:
                self.level = level_name
        if self.user.user_type != "Verified" and self.points >= 101:
            self.level = "Intermediate Rater"
        self.save()
        

    def get_next_level_info(self):
        for i in range(len(self.LEVELS) - 1):
            if self.points < self.LEVELS[i + 1][0]:
                return {
                    "next_level": self.LEVELS[i + 1][1],
                    "points_needed": self.LEVELS[i + 1][0] - self.points,
                }
        return {"next_level": "Max Level Reached", "points_needed": 0}

    def check_daily_bonus(self):
        if self.last_rating_date != date.today():
            self.points += 5
            self.last_rating_date = date.today()

    def award_points_for_rating(self):
        user_type = self.user.user_type
        print(f"Awarding points to {self.user} ({user_type})")
        if user_type == "Verified":
            base = 3
        elif user_type == "Registered":
            base = 2
        else:
            base = 0
        self.points += base
        self.check_daily_bonus()
        self.update_level()
        self.save()



class BonusAwardLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    week_start = models.DateField()
    awarded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - Week of {self.week_start}"

class NotificationTemplate(models.Model):

    TEMPLATE_TYPES = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
    )

    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=10, choices=TEMPLATE_TYPES)
    content = models.TextField(help_text="Use placeholders like {name}, {points}")
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True)

    def __str__(self):
        return f"{self.name} ({self.type})"

    @staticmethod
    def get_template(name):
        try:
            return NotificationTemplate.objects.get(name=name, is_active=True).content
        except NotificationTemplate.DoesNotExist:
            return "Hi {name}, you've earned {points} bonus points this week!"


class NotificationLog(models.Model):
    CHANNEL_CHOICES = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    recipient = models.CharField(max_length=100)
    message = models.TextField()
    status = models.CharField(max_length=50)
    response = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.channel} - {self.status}"



