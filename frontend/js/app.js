/**
 * Talking Orange - Bitcoin AR Experience
 * Main application logic for camera and microphone permissions
 */

class TalkingOrangeApp {
    constructor() {
        this.camera = null;
        this.microphone = null;
        this.isActive = false;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.arManager = null;
        
        this.initializeElements();
        this.attachEventListeners();
    }
    
    initializeElements() {
        // Screens
        this.welcomeScreen = document.getElementById('welcome-screen');
        this.cameraScreen = document.getElementById('camera-screen');
        this.errorScreen = document.getElementById('error-screen');
        
        // Buttons
        this.startButton = document.getElementById('start-button');
        this.stopButton = document.getElementById('stop-button');
        this.retryButton = document.getElementById('retry-button');
        this.microphoneButton = document.getElementById('microphone-button');
        
        // Camera elements
        this.cameraFeed = document.getElementById('camera-feed');
        this.cameraStatus = document.getElementById('camera-status');
        this.microphoneStatus = document.getElementById('microphone-status');
        
        // Error message
        this.errorMessage = document.getElementById('error-message');
    }
    
    attachEventListeners() {
        this.startButton.addEventListener('click', () => this.startExperience());
        this.stopButton.addEventListener('click', () => this.stopExperience());
        this.retryButton.addEventListener('click', () => this.startExperience());
        this.microphoneButton.addEventListener('click', () => this.toggleRecording());
    }
    
    async startExperience() {
        try {
            console.log('🍊 Starting Talking Orange experience...');
            
            // Show loading state
            this.startButton.disabled = true;
            this.startButton.innerHTML = '<span class="btn-text">Starting...</span><span class="btn-icon">⏳</span>';
            
            // Request camera and microphone permissions
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            console.log('✅ Camera and microphone access granted');
            
            // Set up camera feed
            this.cameraFeed.srcObject = stream;
            this.camera = stream.getVideoTracks()[0];
            this.microphone = stream.getAudioTracks()[0];
            
            // Update status indicators
            this.updateStatusIndicators();
            
            // Switch to camera screen
            this.showScreen('camera');
            this.isActive = true;
            
            // Initialize AR Manager
            this.initializeAR();
            
            // Set up track event listeners
            this.setupTrackListeners();
            
            console.log('🎉 Talking Orange experience started successfully!');
            
        } catch (error) {
            console.error('❌ Failed to start experience:', error);
            this.handlePermissionError(error);
        }
    }
    
    setupTrackListeners() {
        if (this.camera) {
            this.camera.addEventListener('ended', () => {
                console.log('📹 Camera track ended');
                this.updateCameraStatus(false);
            });
        }
        
        if (this.microphone) {
            this.microphone.addEventListener('ended', () => {
                console.log('🎤 Microphone track ended');
                this.updateMicrophoneStatus(false);
            });
        }
    }
    
    updateStatusIndicators() {
        this.updateCameraStatus(this.camera && this.camera.readyState === 'live');
        this.updateMicrophoneStatus(this.microphone && this.microphone.readyState === 'live');
    }
    
    updateCameraStatus(isActive) {
        if (isActive) {
            this.cameraStatus.classList.add('active');
        } else {
            this.cameraStatus.classList.remove('active');
        }
    }
    
    updateMicrophoneStatus(isActive) {
        if (isActive) {
            this.microphoneStatus.classList.add('active');
        } else {
            this.microphoneStatus.classList.remove('active');
        }
    }
    
    handlePermissionError(error) {
        console.error('Permission error:', error);
        
        let errorMsg = 'We need camera and microphone access to provide the AR experience.';
        
        if (error.name === 'NotAllowedError') {
            errorMsg = 'Permission denied. Please allow camera and microphone access and try again.';
        } else if (error.name === 'NotFoundError') {
            errorMsg = 'Camera or microphone not found. Please check your device.';
        } else if (error.name === 'NotSupportedError') {
            errorMsg = 'Your browser does not support camera or microphone access.';
        } else if (error.name === 'NotReadableError') {
            errorMsg = 'Camera or microphone is being used by another application.';
        }
        
        this.errorMessage.textContent = errorMsg;
        this.showScreen('error');
        
        // Reset start button
        this.startButton.disabled = false;
        this.startButton.innerHTML = '<span class="btn-text">Let\'s Do It!</span><span class="btn-icon">🚀</span>';
    }
    
    initializeAR() {
        try {
            console.log('🍊 Initializing AR Manager...');
            this.arManager = new ARManager();
            this.arManager.startAR();
            console.log('✅ AR Manager initialized');
        } catch (error) {
            console.error('❌ Failed to initialize AR:', error);
        }
    }
    
    stopExperience() {
        console.log('🛑 Stopping Talking Orange experience...');
        
        // Stop recording if active
        if (this.isRecording) {
            this.stopRecording();
        }
        
        // Stop AR
        if (this.arManager) {
            this.arManager.stopAR();
            this.arManager.destroy();
            this.arManager = null;
        }
        
        // Stop all tracks
        if (this.camera) {
            this.camera.stop();
            this.camera = null;
        }
        
        if (this.microphone) {
            this.microphone.stop();
            this.microphone = null;
        }
        
        // Clear camera feed
        if (this.cameraFeed.srcObject) {
            this.cameraFeed.srcObject = null;
        }
        
        // Reset status
        this.isActive = false;
        this.isRecording = false;
        this.updateCameraStatus(false);
        this.updateMicrophoneStatus(false);
        this.updateMicrophoneButton();
        
        // Return to welcome screen
        this.showScreen('welcome');
        
        console.log('✅ Experience stopped');
    }
    
    showScreen(screenName) {
        // Hide all screens
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });
        
        // Show target screen
        const targetScreen = document.getElementById(`${screenName}-screen`);
        if (targetScreen) {
            targetScreen.classList.add('active');
        }
    }
    
    // Check if browser supports required features
    checkBrowserSupport() {
        const hasGetUserMedia = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
        const hasWebRTC = !!(window.RTCPeerConnection || window.webkitRTCPeerConnection);
        
        if (!hasGetUserMedia || !hasWebRTC) {
            console.warn('⚠️ Browser may not support required features');
            return false;
        }
        
        return true;
    }
    
    // Recording functionality
    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }
    
    async startRecording() {
        try {
            console.log('🎤 Starting audio recording...');
            
            if (!this.microphone || this.microphone.readyState !== 'live') {
                throw new Error('Microphone not available');
            }
            
            // Create MediaRecorder for audio only
            const audioStream = new MediaStream([this.microphone]);
            this.mediaRecorder = new MediaRecorder(audioStream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.processRecording();
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            this.updateMicrophoneButton();
            
            console.log('✅ Recording started');
            
        } catch (error) {
            console.error('❌ Failed to start recording:', error);
            this.showRecordingError('Failed to start recording. Please check microphone permissions.');
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            console.log('🛑 Stopping audio recording...');
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.updateMicrophoneButton();
            console.log('✅ Recording stopped');
        }
    }
    
    async processRecording() {
        try {
            console.log('🔄 Processing recorded audio...');
            
            // Create audio blob
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            
            if (audioBlob.size === 0) {
                console.warn('⚠️ No audio recorded');
                this.showRecordingError('No audio was recorded. Please try again.');
                return;
            }
            
            console.log(`📊 Audio blob size: ${audioBlob.size} bytes`);
            
            // Convert to base64 for server transmission
            const base64Audio = await this.blobToBase64(audioBlob);
            
            // Send to server
            await this.sendAudioToServer(base64Audio);
            
        } catch (error) {
            console.error('❌ Error processing recording:', error);
            this.showRecordingError('Error processing audio. Please try again.');
        }
    }
    
    async sendAudioToServer(audioData) {
        try {
            console.log('📤 Sending audio to server...');
            
            const response = await fetch('/api/speech/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    audioData: audioData,
                    sessionId: this.getSessionId(),
                    language: 'en'
                })
            });
            
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            
            const result = await response.json();
            console.log('✅ Server response received:', result);
            
            // Play the response audio
            if (result.audioUrl) {
                await this.playResponseAudio(result.audioUrl);
            }
            
            // Show response text (for debugging)
            this.showResponseText(result.response);
            
        } catch (error) {
            console.error('❌ Error sending audio to server:', error);
            this.showRecordingError('Failed to send audio to server. Please try again.');
        }
    }
    
    async playResponseAudio(audioUrl) {
        try {
            console.log('🔊 Playing response audio...');
            const audio = new Audio(audioUrl);
            audio.play();
        } catch (error) {
            console.error('❌ Error playing audio:', error);
        }
    }
    
    showResponseText(text) {
        // Create a temporary overlay to show the response
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 1rem 2rem;
            border-radius: 10px;
            z-index: 1000;
            max-width: 80%;
            text-align: center;
            font-size: 1.1rem;
        `;
        overlay.textContent = text;
        document.body.appendChild(overlay);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
        }, 5000);
    }
    
    showRecordingError(message) {
        console.error('🎤 Recording error:', message);
        // You could show a toast notification here
        alert(message);
    }
    
    updateMicrophoneButton() {
        if (this.isRecording) {
            this.microphoneButton.classList.add('recording');
            this.microphoneButton.querySelector('.mic-text').textContent = 'Recording...';
        } else {
            this.microphoneButton.classList.remove('recording');
            this.microphoneButton.querySelector('.mic-text').textContent = 'Tap to Talk';
        }
    }
    
    getSessionId() {
        // Generate or retrieve session ID
        let sessionId = sessionStorage.getItem('talkingOrangeSessionId');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('talkingOrangeSessionId', sessionId);
        }
        return sessionId;
    }
    
    blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }
    
    // Initialize the app
    init() {
        console.log('🍊 Talking Orange app initializing...');
        
        if (!this.checkBrowserSupport()) {
            console.warn('⚠️ Browser support check failed, but continuing...');
        }
        
        console.log('✅ Talking Orange app ready!');
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new TalkingOrangeApp();
    app.init();
    
    // Make app globally available for debugging
    window.talkingOrangeApp = app;
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden && window.talkingOrangeApp && window.talkingOrangeApp.isActive) {
        console.log('📱 Page hidden, but keeping camera active');
    }
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.talkingOrangeApp && window.talkingOrangeApp.isActive) {
        window.talkingOrangeApp.stopExperience();
    }
});