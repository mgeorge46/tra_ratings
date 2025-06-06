from django.db import models
from django.conf import settings
from rating.models import Rating


class VoiceSession(models.Model):
    """Track voice rating sessions"""
    session_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    state = models.CharField(max_length=50, default='waiting_wake_word')
    current_step = models.CharField(max_length=50, null=True, blank=True)
    session_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Voice Session {self.session_id} - {self.state}"


class VoiceCommand(models.Model):
    """Log voice commands for analytics"""
    session = models.ForeignKey(VoiceSession, on_delete=models.CASCADE, related_name='commands')
    command_text = models.TextField()
    confidence = models.FloatField(default=0.0)
    timestamp = models.DateTimeField(auto_now_add=True)
    command_type = models.CharField(max_length=50)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.command_type}: {self.command_text[:50]}"