from django.db import models
from django.conf import settings


class OCRExtractionLog(models.Model):
    """Log OCR extraction attempts for analytics and debugging"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Extraction results
    extracted_plate = models.CharField(max_length=20, blank=True)
    formatted_plate = models.CharField(max_length=20, blank=True)
    confidence = models.FloatField(default=0.0)
    plate_format = models.CharField(max_length=20, blank=True)

    # Was it successful?
    success = models.BooleanField(default=False)

    # What corrections were made?
    user_corrected = models.BooleanField(default=False)
    corrected_plate = models.CharField(max_length=20, blank=True)

    # Input method
    input_method = models.CharField(
        max_length=20,
        choices=[
            ('photo', 'Photo'),
            ('text', 'Text'),
            ('voice', 'Voice'),
        ],
        default='photo'
    )

    # Raw detections for debugging
    raw_detections = models.JSONField(default=list, blank=True)

    # OCR engine used
    engine_used = models.CharField(max_length=50, blank=True)

    # Timing
    processing_time_ms = models.IntegerField(default=0)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'OCR Extraction Log'
        verbose_name_plural = 'OCR Extraction Logs'

    def __str__(self):
        return f"{self.formatted_plate or 'Failed'} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"