from django.core.management.base import BaseCommand
from voice_rating.voice_engine import VoiceEngine
from voice_rating.voice_commands import VoiceCommandProcessor
import logging

logging.basicConfig(level=logging.INFO)


class Command(BaseCommand):
    help = 'Test voice rating system'

    def handle(self, *args, **options):
        self.stdout.write('Starting voice rating test...')

        # Initialize engine
        engine = VoiceEngine()

        # Create test session
        session_id = engine.session_manager.create_session()

        # Create processor
        processor = VoiceCommandProcessor(engine, engine.session_manager)

        self.stdout.write('Voice engine initialized. Starting rating flow...')

        # Start rating flow
        success = processor.start_rating_flow(session_id)

        if success:
            self.stdout.write(self.style.SUCCESS('Voice rating completed successfully!'))
        else:
            self.stdout.write(self.style.ERROR('Voice rating failed.'))

        # Stop engine
        engine.stop_listening()