// Voice Manager - Handles Web Speech API
class VoiceManager {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.isInitialized = false;
        this.callbacks = {
            onSpeechResult: [],
            onListeningStart: [],
            onListeningEnd: [],
            onError: []
        };
    }

    async initialize() {
        try {
            console.log('🎤 Initializing Voice Manager...');
            
            // Check for speech recognition support
            if (!this.isSpeechRecognitionSupported()) {
                throw new Error('Speech recognition not supported in this browser');
            }
            
            // Initialize speech recognition
            this.setupSpeechRecognition();
            
            this.isInitialized = true;
            console.log('✅ Voice Manager initialized');
            
        } catch (error) {
            console.error('❌ Voice Manager initialization failed:', error);
            throw error;
        }
    }

    isSpeechRecognitionSupported() {
        return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
    }

    setupSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        // Configure recognition
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';
        this.recognition.maxAlternatives = 1;
        
        // Set up event listeners
        this.recognition.onstart = () => {
            console.log('🎤 Speech recognition started');
            this.isListening = true;
            this.triggerCallbacks('onListeningStart');
        };
        
        this.recognition.onresult = (event) => {
            console.log('🎤 Speech recognition result:', event);
            this.handleSpeechResult(event);
        };
        
        this.recognition.onend = () => {
            console.log('🎤 Speech recognition ended');
            this.isListening = false;
            this.triggerCallbacks('onListeningEnd');
        };
        
        this.recognition.onerror = (event) => {
            console.error('❌ Speech recognition error:', event.error);
            this.isListening = false;
            this.triggerCallbacks('onError', event.error);
            this.triggerCallbacks('onListeningEnd');
        };
    }

    handleSpeechResult(event) {
        const result = event.results[event.results.length - 1];
        const transcript = result[0].transcript;
        const confidence = result[0].confidence;
        
        console.log('🎤 Speech result:', { transcript, confidence });
        
        // Only process if confidence is high enough
        if (confidence > 0.5) {
            this.triggerCallbacks('onSpeechResult', transcript);
        } else {
            console.log('🎤 Low confidence, ignoring result');
        }
    }

    async startListening() {
        if (!this.isInitialized) {
            throw new Error('Voice Manager not initialized');
        }
        
        if (this.isListening) {
            console.log('🎤 Already listening');
            return;
        }
        
        try {
            console.log('🎤 Starting speech recognition...');
            this.recognition.start();
        } catch (error) {
            console.error('❌ Failed to start speech recognition:', error);
            throw error;
        }
    }

    stopListening() {
        if (this.recognition && this.isListening) {
            console.log('🎤 Stopping speech recognition...');
            this.recognition.stop();
        }
    }

    // Event listener registration
    onSpeechResult(callback) {
        this.callbacks.onSpeechResult.push(callback);
    }

    onListeningStart(callback) {
        this.callbacks.onListeningStart.push(callback);
    }

    onListeningEnd(callback) {
        this.callbacks.onListeningEnd.push(callback);
    }

    onError(callback) {
        this.callbacks.onError.push(callback);
    }

    triggerCallbacks(eventType, data = null) {
        if (this.callbacks[eventType]) {
            this.callbacks[eventType].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Callback error for ${eventType}:`, error);
                }
            });
        }
    }

    // Get current status
    getStatus() {
        return {
            initialized: this.isInitialized,
            listening: this.isListening,
            supported: this.isSpeechRecognitionSupported()
        };
    }

    // Set language
    setLanguage(lang) {
        if (this.recognition) {
            this.recognition.lang = lang;
        }
    }

    // Set continuous listening
    setContinuous(continuous) {
        if (this.recognition) {
            this.recognition.continuous = continuous;
        }
    }

    // Set interim results
    setInterimResults(interim) {
        if (this.recognition) {
            this.recognition.interimResults = interim;
        }
    }

    // Get available languages (if supported)
    getAvailableLanguages() {
        // This would need to be implemented based on browser support
        return ['en-US', 'en-GB', 'es-ES', 'fr-FR', 'de-DE'];
    }

    // Check if microphone is available
    async checkMicrophoneAccess() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            return true;
        } catch (error) {
            console.error('Microphone access denied:', error);
            return false;
        }
    }

    // Get speech recognition capabilities
    getCapabilities() {
        return {
            supported: this.isSpeechRecognitionSupported(),
            continuous: this.recognition ? this.recognition.continuous : false,
            interimResults: this.recognition ? this.recognition.interimResults : false,
            language: this.recognition ? this.recognition.lang : 'en-US'
        };
    }
}
