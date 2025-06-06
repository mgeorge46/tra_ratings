from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import logging

from .voice_engine import VoiceEngine
from .voice_commands import VoiceCommandProcessor
from .models import VoiceSession
from django.conf import settings

logger = logging.getLogger('voice_rating')


class VoiceInterfaceView(LoginRequiredMixin, View):
    """Main voice interface view"""

    def get(self, request):
        """Render voice interface"""
        context = {
            'wake_phrases': settings.VOICE_RATING.get('WAKE_PHRASE', 'my app'),
            'user': request.user
        }
        return render(request, 'voice_rating/voice_interface.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class VoiceSessionAPIView(View):
    """API endpoints for voice session management"""

    def post(self, request, action):
        """Handle voice session actions"""
        try:
            data = json.loads(request.body) if request.body else {}

            if action == 'start':
                return self.start_session(request, data)
            elif action == 'wake':
                return self.handle_wake_word(request, data)
            elif action == 'command':
                return self.process_command(request, data)
            elif action == 'end':
                return self.end_session(request, data)
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)

        except Exception as e:
            logger.error(f"Voice API error: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    def start_session(self, request, data):
        """Start a new voice session"""
        engine = VoiceEngine()
        session_id = engine.session_manager.create_session(
            user=request.user if request.user.is_authenticated else None
        )

        # Start listening for wake word
        engine.listen_for_wake_word()

        return JsonResponse({
            'session_id': session_id,
            'status': 'listening',
            'message': 'Listening for wake word...'
        })

    def handle_wake_word(self, request, data):
        """Handle wake word detection"""
        session_id = data.get('session_id')
        if not session_id:
            return JsonResponse({'error': 'Session ID required'}, status=400)

        engine = VoiceEngine()
        processor = VoiceCommandProcessor(engine, engine.session_manager)

        # Update session state
        engine.session_manager.update_session(session_id, state='active')

        # Start rating flow
        success = processor.start_rating_flow(session_id)

        return JsonResponse({
            'success': success,
            'status': 'complete' if success else 'error'
        })

    def process_command(self, request, data):
        """Process a voice command"""
        session_id = data.get('session_id')
        command = data.get('command')

        if not session_id or not command:
            return JsonResponse({'error': 'Session ID and command required'}, status=400)

        # Process the command based on current session state
        # This would be implemented based on your specific command structure

        return JsonResponse({'status': 'processed'})

    def end_session(self, request, data):
        """End a voice session"""
        session_id = data.get('session_id')
        if not session_id:
            return JsonResponse({'error': 'Session ID required'}, status=400)

        engine = VoiceEngine()
        engine.stop_listening()
        engine.session_manager.close_session(session_id)

        return JsonResponse({'status': 'closed'})


class VoiceHistoryView(LoginRequiredMixin, View):
    """View voice rating history"""

    def get(self, request):
        """Show user's voice rating history"""
        sessions = VoiceSession.objects.filter(
            user=request.user
        ).prefetch_related('commands').order_by('-created_at')[:20]

        context = {
            'sessions': sessions
        }
        return render(request, 'voice_rating/history.html', context)