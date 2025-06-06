class VoiceController {
    constructor() {
        this.sessionId = null;
        this.isListening = false;
        this.currentStep = null;

        this.startBtn = document.getElementById('start-voice');
        this.stopBtn = document.getElementById('stop-voice');
        this.statusText = document.getElementById('status-text');
        this.statusMessage = document.getElementById('status-message');
        this.voiceStatus = document.getElementById('voice-status');
        this.voiceFeedback = document.getElementById('voice-feedback');

        this.initializeEventListeners();
    }

    initializeEventListeners() {
        this.startBtn.addEventListener('click', () => this.startVoiceSession());
        this.stopBtn.addEventListener('click', () => this.stopVoiceSession());

        // Check for browser support
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            this.showError('Your browser does not support speech recognition. Please use Chrome or Edge.');
            this.startBtn.disabled = true;
        }
    }

    async startVoiceSession() {
        try {
            // Request microphone permission
            await navigator.mediaDevices.getUserMedia({ audio: true });

            // Start session on backend
            const response = await fetch('/voice/api/session/start/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();

            if (data.session_id) {
                this.sessionId = data.session_id;
                this.isListening = true;
                this.updateUI('listening');

                // Start local speech recognition for wake word
                this.startWakeWordDetection();
            }
        } catch (error) {
            console.error('Error starting voice session:', error);
            this.showError('Failed to start voice session. Please check your microphone.');
        }
    }

    startWakeWordDetection() {
        // Use Web Speech API for wake word detection
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();

        this.recognition.continuous = true;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-KE'; // Kenyan English

        this.recognition.onresult = (event) => {
            const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase();
            console.log('Heard:', transcript);

            // Check for wake words
            const wakeWords = ['rating', 'rating app', 'hey rating', 'my app'];
            const detected = wakeWords.some(word => transcript.includes(word));

            if (detected) {
                this.handleWakeWordDetected();
            }
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            if (event.error === 'no-speech') {
                // Restart recognition
                this.recognition.start();
            }
        };

        this.recognition.start();
    }

    async handleWakeWordDetected() {
        // Stop wake word detection
        this.recognition.stop();

        // Notify backend
        const response = await fetch('/voice/api/session/wake/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: this.sessionId
            })
        });

        const data = await response.json();

        if (data.success) {
            this.updateUI('complete');
            this.showSuccess('Rating completed successfully!');
        } else {
            this.showError('Failed to complete rating. Please try again.');
        }

        // Restart wake word detection after a delay
        setTimeout(() => {
            if (this.isListening) {
                this.startWakeWordDetection();
            }
        }, 3000);
    }

    async stopVoiceSession() {
        this.isListening = false;

        if (this.recognition) {
            this.recognition.stop();
        }

        if (this.sessionId) {
            await fetch('/voice/api/session/end/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId
                })
            });
        }

        this.updateUI('stopped');
    }

    updateUI(state) {
        switch(state) {
            case 'listening':
                this.startBtn.style.display = 'none';
                this.stopBtn.style.display = 'inline-block';
                this.statusText.textContent = 'Listening for wake word...';
                this.statusMessage.textContent = 'Say "Rating" or "My App" to begin';
                this.voiceStatus.classList.add('voice-active');
                break;

            case 'processing':
                this.statusText.textContent = 'Processing...';
                this.statusMessage.textContent = 'Please wait';
                break;

            case 'complete':
                this.statusText.textContent = 'Rating Complete';
                this.statusMessage.textContent = 'Ready for next rating';
                break;

            case 'stopped':
                this.startBtn.style.display = 'inline-block';
                this.stopBtn.style.display = 'none';
                this.statusText.textContent = 'Click to Start Voice Rating';
                this.statusMessage.textContent = 'Say "Rating" to begin';
                this.voiceStatus.classList.remove('voice-active');
                break;
        }
    }

    showError(message) {
        this.statusMessage.innerHTML = `<span class="text-danger">${message}</span>`;
    }

    showSuccess(message) {
        this.statusMessage.innerHTML = `<span class="text-success">${message}</span>`;
    }
}

// Initialize controller when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new VoiceController();
});