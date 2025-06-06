from django.apps import AppConfig
import logging

logger = logging.getLogger('voice_rating')


class VoiceRatingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'voice_rating'

    def ready(self):
        # Don't initialize voice engine during migrations
        import sys
        if 'makemigrations' in sys.argv or 'migrate' in sys.argv:
            return

        try:
            from .voice_engine import VoiceEngine
            VoiceEngine.initialize()
        except ImportError:
            logger.info("Voice dependencies not installed yet")
        except Exception as e:
            logger.error(f"Voice engine initialization error: {e}")