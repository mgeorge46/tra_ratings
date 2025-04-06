
from django.urls import path
from .views import save_device_token


urlpatterns = [
    path('api/save-token/', save_device_token, name='save_token'),
]



