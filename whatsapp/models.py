from django.db import models
from django.conf import settings

# Create your model

class WhatsappLog(models.Model):
    recipient = models.CharField(max_length=15)  # Adjust max_length as needed
    message = models.TextField()
    api_status_code = models.IntegerField()
    api_response = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,  # Allow null for anonymous users
        blank=True
    )

    def __str__(self):
        return f"Message to {self.recipient} - Status: {self.api_status_code}"


