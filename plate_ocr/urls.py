from django.urls import path
from .views import PhotoRatingWizardView, PlateOCRAPIView, voice_plate_entry

urlpatterns = [
    # Main wizard flow
    path('', PhotoRatingWizardView.as_view(), name='photo_rating_wizard'),

    # API endpoint for AJAX OCR
    path('api/extract/', PlateOCRAPIView.as_view(), name='plate_ocr_api'),

    # Voice entry fallback
    path('voice/', voice_plate_entry, name='voice_plate_entry'),
]