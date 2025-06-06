import os
import json
from django.conf import settings
import speech_recognition as sr
from pydub import AudioSegment
from pydub.effects import normalize
import numpy as np
import webrtcvad


class AudioProcessor:
    """Process audio for better recognition with East African accents"""

    def __init__(self):
        self.vad = webrtcvad.Vad(2)  # Aggressiveness level 2

    def preprocess_audio(self, audio_data):
        """Preprocess audio for better recognition"""
        # Convert to AudioSegment
        audio = AudioSegment(
            audio_data.frame_data,
            frame_rate=audio_data.sample_rate,
            sample_width=audio_data.sample_width,
            channels=1
        )

        # Normalize audio
        normalized = normalize(audio)

        # Apply noise reduction
        cleaned = self.reduce_noise(normalized)

        return cleaned

    def reduce_noise(self, audio):
        """Simple noise reduction"""
        # Convert to numpy array
        samples = np.array(audio.get_array_of_samples())

        # Apply simple high-pass filter
        from scipy import signal
        b, a = signal.butter(4, 80.0, 'high', fs=audio.frame_rate)
        filtered = signal.filtfilt(b, a, samples)

        # Convert back to AudioSegment
        filtered_audio = audio._spawn(filtered.astype(np.int16).tobytes())

        return filtered_audio

    def detect_speech(self, audio_data, sample_rate=16000):
        """Detect if audio contains speech"""
        frames = self.frame_generator(30, audio_data, sample_rate)
        num_voiced = 0

        for frame in frames:
            is_speech = self.vad.is_speech(frame.bytes, sample_rate)
            if is_speech:
                num_voiced += 1

        # Return True if more than 30% of frames contain speech
        return num_voiced > len(list(frames)) * 0.3

    def frame_generator(self, frame_duration_ms, audio, sample_rate):
        """Generate audio frames"""
        n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
        offset = 0
        timestamp = 0.0
        duration = (1.0 / sample_rate) * n

        while offset + n < len(audio):
            yield Frame(audio[offset:offset + n], timestamp, duration)
            timestamp += duration
            offset += n


class Frame:
    """Represents an audio frame"""

    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration


class OfflineRatingStorage:
    """Store ratings offline for later sync"""

    @staticmethod
    def save_offline_rating(rating_data):
        """Save rating data locally when offline"""
        offline_dir = os.path.join(settings.MEDIA_ROOT, 'offline_ratings')
        os.makedirs(offline_dir, exist_ok=True)

        filename = f"rating_{rating_data['session_id']}_{int(time.time())}.json"
        filepath = os.path.join(offline_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(rating_data, f)

        return filepath

    @staticmethod
    def get_offline_ratings():
        """Get all offline ratings"""
        offline_dir = os.path.join(settings.MEDIA_ROOT, 'offline_ratings')
        if not os.path.exists(offline_dir):
            return []

        ratings = []
        for filename in os.listdir(offline_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(offline_dir, filename)
                with open(filepath, 'r') as f:
                    ratings.append({
                        'filename': filename,
                        'data': json.load(f)
                    })

        return ratings

    @staticmethod
    def delete_offline_rating(filename):
        """Delete synced offline rating"""
        filepath = os.path.join(settings.MEDIA_ROOT, 'offline_ratings', filename)
        if os.path.exists(filepath):
            os.remove(filepath)