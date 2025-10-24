// Talking Orange AR Project - Main Application
class TalkingOrangeApp {
    constructor() {
        this.isInitialized = false;
        this.sessionId = this.generateSessionId();
        this.apiBaseUrl = window.location.origin + '/api';
        
        this.init();
    }

    async init() {
        try {
            console.log('🍊 Initializing Talking Orange AR App...');
            
            // Show loading screen
            this.showScreen('loading-screen');
            
            // Wait for DOM to be ready
            await this.waitForDOM();
            
            // Initialize components
            await this.initializeComponents();
            
            // Check for permissions
            await this.checkPermissions();
            
            this.isInitialized = true;
            console.log('✅ Talking Orange AR App initialized successfully');
            
        } catch (error) {
            console.error('❌ Failed to initialize app:', error);
            this.showError('Failed to initialize the application');
        }
    }

    async waitForDOM() {
        return new Promise((resolve) => {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', resolve);
            } else {
                resolve();
            }
        });
    }

    async initializeComponents() {
        // Initialize AR Manager
        this.arManager = new ARManager();
        
        // Initialize Voice Manager
        this.voiceManager = new VoiceManager();
        
        // Initialize QR Manager
        this.qrManager = new QRManager();
        
        // Set up event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Permission buttons
        document.getElementById('grant-permissions').addEventListener('click', () => {
            this.requestPermissions();
        });
        
        document.getElementById('deny-permissions').addEventListener('click', () => {
            this.showError('Camera and microphone access is required for the AR experience');
        });
        
        // Retry button
        document.getElementById('retry-btn').addEventListener('click', () => {
            this.init();
        });
        
        // Voice button
        document.getElementById('start-listening').addEventListener('click', () => {
            this.startVoiceInteraction();
        });
    }

    async checkPermissions() {
        try {
            // Check if we're in a secure context (HTTPS or localhost)
            if (!this.isSecureContext()) {
                throw new Error('AR experience requires HTTPS or localhost');
            }
            
            // Check for required APIs
            if (!('mediaDevices' in navigator)) {
                throw new Error('Camera access not supported');
            }
            
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                throw new Error('Speech recognition not supported');
            }
            
            // Hide loading screen and show permission screen
            this.hideScreen('loading-screen');
            this.showScreen('permission-screen');
            
        } catch (error) {
            console.error('Permission check failed:', error);
            this.showError(error.message);
        }
    }

    async requestPermissions() {
        try {
            console.log('🎤 Requesting camera and microphone permissions...');
            
            // Request camera access
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'user' },
                audio: true
            });
            
            console.log('✅ Permissions granted');
            
            // Stop the stream (we'll start it again in AR)
            stream.getTracks().forEach(track => track.stop());
            
            // Hide permission screen and show AR experience
            this.hideScreen('permission-screen');
            this.showScreen('ar-experience');
            
            // Initialize AR experience
            await this.initializeARExperience();
            
        } catch (error) {
            console.error('❌ Permission request failed:', error);
            this.showError('Permission denied. Please allow camera and microphone access to continue.');
        }
    }

    async initializeARExperience() {
        try {
            console.log('🚀 Initializing AR experience...');
            
            // Initialize AR manager
            await this.arManager.initialize();
            
            // Initialize voice manager
            await this.voiceManager.initialize();
            
            // Set up AR event listeners
            this.arManager.onMarkerDetected(() => {
                console.log('🎯 AR marker detected');
                this.onMarkerDetected();
            });
            
            this.arManager.onMarkerLost(() => {
                console.log('❌ AR marker lost');
                this.onMarkerLost();
            });
            
            // Set up voice event listeners
            this.voiceManager.onSpeechResult((text) => {
                console.log('🎤 Speech recognized:', text);
                this.processSpeechInput(text);
            });
            
            this.voiceManager.onListeningStart(() => {
                this.showListeningIndicator();
            });
            
            this.voiceManager.onListeningEnd(() => {
                this.hideListeningIndicator();
            });
            
            console.log('✅ AR experience initialized');
            
        } catch (error) {
            console.error('❌ AR initialization failed:', error);
            this.showError('Failed to initialize AR experience');
        }
    }

    async onMarkerDetected() {
        // Show welcome message
        this.showOrangeResponse('Hello! I\'m the Talking Orange! 🍊 Ask me anything about Bitcoin!');
        
        // Enable voice interaction
        this.enableVoiceInteraction();
    }

    async onMarkerLost() {
        // Hide response area
        this.hideOrangeResponse();
        
        // Disable voice interaction
        this.disableVoiceInteraction();
    }

    async startVoiceInteraction() {
        try {
            await this.voiceManager.startListening();
        } catch (error) {
            console.error('Voice interaction failed:', error);
            this.showOrangeResponse('Sorry, I couldn\'t hear you. Please try again.');
        }
    }

    async processSpeechInput(text) {
        try {
            console.log('🤖 Processing speech input:', text);
            
            // Show loading state
            this.showOrangeResponse('Let me think about that...');
            
            // Send to backend for processing
            const response = await this.sendSpeechToBackend(text);
            
            // Show response
            this.showOrangeResponse(response.response);
            
            // Play audio response if available
            if (response.audioUrl) {
                await this.playAudioResponse(response.audioUrl);
            } else {
                // Fallback to browser TTS
                this.speakText(response.response);
            }
            
            // Log analytics
            this.logAnalytics('speech_processed', {
                input: text,
                response: response.response,
                audioUrl: response.audioUrl,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            console.error('Speech processing failed:', error);
            this.showOrangeResponse('Sorry, I had trouble understanding that. Can you try asking about Bitcoin?');
        }
    }

    async sendSpeechToBackend(text) {
        const response = await fetch(`${this.apiBaseUrl}/speech/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text,
                sessionId: this.sessionId
            })
        });
        
        if (!response.ok) {
            throw new Error('Backend request failed');
        }
        
        return await response.json();
    }

    showOrangeResponse(text) {
        const responseElement = document.getElementById('orange-response');
        const textElement = responseElement.querySelector('.response-text');
        
        textElement.textContent = text;
        responseElement.classList.remove('hidden');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.hideOrangeResponse();
        }, 5000);
    }

    hideOrangeResponse() {
        document.getElementById('orange-response').classList.add('hidden');
    }

    showListeningIndicator() {
        document.getElementById('listening-indicator').classList.remove('hidden');
        document.getElementById('start-listening').classList.add('voice-active');
    }

    hideListeningIndicator() {
        document.getElementById('listening-indicator').classList.add('hidden');
        document.getElementById('start-listening').classList.remove('voice-active');
    }

    enableVoiceInteraction() {
        document.getElementById('start-listening').disabled = false;
        document.getElementById('start-listening').textContent = '🎤 Ask about Bitcoin';
    }

    disableVoiceInteraction() {
        document.getElementById('start-listening').disabled = true;
        document.getElementById('start-listening').textContent = '🎤 Point at marker to talk';
    }

    async logAnalytics(eventType, data) {
        try {
            await fetch(`${this.apiBaseUrl}/analytics`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sessionId: this.sessionId,
                    eventType: eventType,
                    data: data
                })
            });
        } catch (error) {
            console.error('Analytics logging failed:', error);
        }
    }

    showScreen(screenId) {
        document.getElementById(screenId).classList.remove('hidden');
    }

    hideScreen(screenId) {
        document.getElementById(screenId).classList.add('hidden');
    }

    showError(message) {
        document.getElementById('error-message').textContent = message;
        this.hideScreen('loading-screen');
        this.hideScreen('permission-screen');
        this.hideScreen('ar-experience');
        this.showScreen('error-screen');
    }

    isSecureContext() {
        return window.isSecureContext || window.location.hostname === 'localhost';
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Audio response methods
    async playAudioResponse(audioUrl) {
        try {
            const audio = new Audio(audioUrl);
            audio.preload = 'auto';
            
            return new Promise((resolve, reject) => {
                audio.onended = () => resolve();
                audio.onerror = (error) => reject(error);
                audio.play().catch(reject);
            });
        } catch (error) {
            console.error('Audio playback failed:', error);
            // Fallback to browser TTS
            this.speakText('Sorry, I had trouble playing the audio response.');
        }
    }

    speakText(text) {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 0.9;
            utterance.pitch = 1.1;
            utterance.volume = 1.0;
            
            // Try to find a good voice
            const voices = speechSynthesis.getVoices();
            const preferredVoice = voices.find(voice => 
                voice.name.includes('Google') || 
                voice.name.includes('Microsoft') ||
                voice.lang.startsWith('en')
            );
            
            if (preferredVoice) {
                utterance.voice = preferredVoice;
            }
            
            speechSynthesis.speak(utterance);
        } else {
            console.warn('Speech synthesis not supported');
        }
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.talkingOrangeApp = new TalkingOrangeApp();
});
