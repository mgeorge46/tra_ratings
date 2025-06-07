import speech_recognition as sr
import pyttsx3
import threading
import queue
import time
import json
import uuid
from django.conf import settings
import pvporcupine
import numpy as np
import struct
import pyaudio
import logging

logger = logging.getLogger('voice_rating')


class VoiceEngine:
    """Core voice processing engine"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            self.tts_engine = None
            self.tts_lock = threading.Lock()  # Add lock for TTS operations
            self.command_queue = queue.Queue()
            self.is_listening = False
            self.wake_word_detector = None
            self.session_manager = SessionManager()

            # Initialize TTS in a thread-safe way
            self._init_tts()

            # Configure recognizer for better accuracy with accents
            self.recognizer.energy_threshold = 4000
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8

            self.initialized = True

    def _init_tts(self):
        """Initialize TTS engine in a thread-safe way"""
        try:
            self.tts_engine = pyttsx3.init()

            # Configure TTS for East African accent compatibility
            voices = self.tts_engine.getProperty('voices')
            # Try to find an English voice that works well with East African accents
            for voice in voices:
                if 'english' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break

            self.tts_engine.setProperty('rate', 150)  # Slower for better understanding
            self.tts_engine.setProperty('volume', 0.9)

            logger.info("TTS engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.tts_engine = None

    @classmethod
    def initialize(cls):
        """Initialize the voice engine"""
        instance = cls()
        instance.setup_wake_word_detection()
        return instance

    def setup_wake_word_detection(self):
        """Setup Porcupine wake word detection"""
        try:
            # Get wake phrases from settings
            wake_phrases = settings.VOICE_RATING.get('WAKE_PHRASE', 'my app').lower().split(',')

            # For production, you would train custom wake words
            # For now, we'll use a simpler approach with continuous listening
            self.wake_phrases = [phrase.strip() for phrase in wake_phrases]
            logger.info(f"Wake phrases configured: {self.wake_phrases}")

        except Exception as e:
            logger.error(f"Error setting up wake word detection: {e}")

    def speak(self, text, wait=True):
        """Convert text to speech in a thread-safe way"""
        if not self.tts_engine:
            logger.warning("TTS engine not available")
            return

        def _speak():
            with self.tts_lock:
                try:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                except Exception as e:
                    logger.error(f"TTS Error: {e}")
                    # Try to reinitialize TTS engine if it fails
                    try:
                        self.tts_engine.stop()
                        self._init_tts()
                    except:
                        pass

        if wait:
            _speak()
        else:
            threading.Thread(target=_speak, daemon=True).start()

    def listen_for_wake_word(self):
        """Listen for wake word in background"""

        def _listen():
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
            except Exception as e:
                logger.error(f"Error adjusting microphone: {e}")
                return

            while self.is_listening:
                try:
                    with self.microphone as source:
                        # Listen for short duration to check for wake word
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)

                    # Try to recognize the wake word
                    text = self.recognizer.recognize_google(audio).lower()

                    # Check if any wake phrase was spoken
                    for wake_phrase in self.wake_phrases:
                        if wake_phrase in text:
                            logger.info(f"Wake word detected: {text}")
                            self.command_queue.put(('wake_word', text))
                            break

                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except Exception as e:
                    logger.error(f"Wake word detection error: {e}")
                    time.sleep(0.5)

        if not self.is_listening:
            self.is_listening = True
            self.listen_thread = threading.Thread(target=_listen, daemon=True)
            self.listen_thread.start()
            logger.info("Started listening for wake word")

    def listen_for_command(self, timeout=10, prompt=None):
        """Listen for a specific command after wake word"""
        if prompt:
            self.speak(prompt)

        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)

            # Use Google's speech recognition with language hint
            text = self.recognizer.recognize_google(
                audio,
                language=settings.VOICE_RATING.get('LANGUAGE', 'en-KE')
            )

            logger.info(f"Recognized: {text}")
            return text

        except sr.WaitTimeoutError:
            self.speak("I didn't hear anything. Please try again.")
            return None
        except sr.UnknownValueError:
            self.speak("I couldn't understand that. Please speak clearly.")
            return None
        except Exception as e:
            logger.error(f"Recognition error: {e}")
            self.speak("Sorry, there was an error. Please try again.")
            return None

    def stop_listening(self):
        """Stop the wake word listener"""
        self.is_listening = False
        if hasattr(self, 'listen_thread') and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=2)
        logger.info("Stopped listening for wake word")

    def cleanup(self):
        """Clean up resources"""
        self.stop_listening()
        with self.tts_lock:
            if self.tts_engine:
                try:
                    self.tts_engine.stop()
                except:
                    pass


class SessionManager:
    """Manage voice rating sessions"""

    def __init__(self):
        self.sessions = {}

    def create_session(self, user=None):
        """Create a new voice session"""
        from .models import VoiceSession

        session_id = str(uuid.uuid4())
        session = VoiceSession.objects.create(
            session_id=session_id,
            user=user,
            state='waiting_motor_type'
        )

        self.sessions[session_id] = {
            'session': session,
            'data': {},
            'step': 'motor_type'
        }

        logger.info(f"Created voice session: {session_id}")
        return session_id

    def get_session(self, session_id):
        """Get active session"""
        if session_id in self.sessions:
            return self.sessions[session_id]

        # Try to load from database
        from .models import VoiceSession
        try:
            session = VoiceSession.objects.get(session_id=session_id, is_active=True)
            self.sessions[session_id] = {
                'session': session,
                'data': session.session_data,
                'step': session.current_step or 'motor_type'
            }
            return self.sessions[session_id]
        except VoiceSession.DoesNotExist:
            return None

    def update_session(self, session_id, data=None, step=None, state=None):
        """Update session data"""
        session_data = self.get_session(session_id)
        if not session_data:
            return False

        if data:
            session_data['data'].update(data)
        if step:
            session_data['step'] = step

        # Update database
        session = session_data['session']
        session.session_data = session_data['data']
        session.current_step = session_data['step']
        if state:
            session.state = state
        session.save()

        logger.info(f"Updated session {session_id}: step={step}, state={state}")
        return True

    def close_session(self, session_id):
        """Close a session"""
        session_data = self.get_session(session_id)
        if session_data:
            session = session_data['session']
            session.is_active = False
            session.save()

            if session_id in self.sessions:
                del self.sessions[session_id]

            logger.info(f"Closed session {session_id}")