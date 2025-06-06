from django.urls import path
from .views import VoiceInterfaceView, VoiceSessionAPIView, VoiceHistoryView

app_name = 'voice_rating'

urlpatterns = [
    path('', VoiceInterfaceView.as_view(), name='voice_interface'),
    path('api/session/<str:action>/', VoiceSessionAPIView.as_view(), name='voice_session_api'),
    path('history/', VoiceHistoryView.as_view(), name='voice_history'),
]