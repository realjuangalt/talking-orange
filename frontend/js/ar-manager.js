// AR Manager - Handles AR.js functionality
class ARManager {
    constructor() {
        this.isInitialized = false;
        this.markerDetected = false;
        this.callbacks = {
            onMarkerDetected: [],
            onMarkerLost: []
        };
    }

    async initialize() {
        try {
            console.log('🎯 Initializing AR Manager...');
            
            // Wait for A-Frame to be ready
            await this.waitForAFrame();
            
            // Set up AR scene
            this.setupARScene();
            
            // Set up marker detection
            this.setupMarkerDetection();
            
            this.isInitialized = true;
            console.log('✅ AR Manager initialized');
            
        } catch (error) {
            console.error('❌ AR Manager initialization failed:', error);
            throw error;
        }
    }

    async waitForAFrame() {
        return new Promise((resolve) => {
            if (window.AFRAME) {
                resolve();
            } else {
                const checkAFrame = () => {
                    if (window.AFRAME) {
                        resolve();
                    } else {
                        setTimeout(checkAFrame, 100);
                    }
                };
                checkAFrame();
            }
        });
    }

    setupARScene() {
        const scene = document.querySelector('a-scene');
        if (!scene) {
            throw new Error('AR scene not found');
        }

        // Configure AR.js
        scene.setAttribute('arjs', {
            trackingMethod: 'best',
            debugUIEnabled: false,
            detectionMode: 'mono_and_matrix',
            matrixCodeType: '3x3'
        });

        // Set up camera
        const camera = scene.querySelector('a-marker-camera');
        if (camera) {
            camera.setAttribute('arjs', {
                trackingMethod: 'best'
            });
        }
    }

    setupMarkerDetection() {
        const scene = document.querySelector('a-scene');
        if (!scene) return;

        // Listen for marker events
        scene.addEventListener('markerFound', (event) => {
            console.log('🎯 Marker found:', event.detail);
            this.onMarkerFound(event.detail);
        });

        scene.addEventListener('markerLost', (event) => {
            console.log('❌ Marker lost:', event.detail);
            this.onMarkerLost(event.detail);
        });
    }

    onMarkerFound(marker) {
        this.markerDetected = true;
        
        // Trigger callbacks
        this.callbacks.onMarkerDetected.forEach(callback => {
            try {
                callback(marker);
            } catch (error) {
                console.error('Marker detected callback error:', error);
            }
        });
    }

    onMarkerLost(marker) {
        this.markerDetected = false;
        
        // Trigger callbacks
        this.callbacks.onMarkerLost.forEach(callback => {
            try {
                callback(marker);
            } catch (error) {
                console.error('Marker lost callback error:', error);
            }
        });
    }

    // Event listener registration
    onMarkerDetected(callback) {
        this.callbacks.onMarkerDetected.push(callback);
    }

    onMarkerLost(callback) {
        this.callbacks.onMarkerLost.push(callback);
    }

    // Get current marker state
    isMarkerDetected() {
        return this.markerDetected;
    }

    // Get marker position if available
    getMarkerPosition() {
        const orange = document.getElementById('talking-orange');
        if (orange && this.markerDetected) {
            return orange.getAttribute('position');
        }
        return null;
    }

    // Animate the orange character
    animateOrange(animationType) {
        const orange = document.getElementById('talking-orange');
        if (!orange) return;

        // Remove existing animations
        const existingAnimations = orange.querySelectorAll('a-animation');
        existingAnimations.forEach(anim => anim.remove());

        switch (animationType) {
            case 'talking':
                this.addTalkingAnimation(orange);
                break;
            case 'excited':
                this.addExcitedAnimation(orange);
                break;
            case 'idle':
                this.addIdleAnimation(orange);
                break;
        }
    }

    addTalkingAnimation(orange) {
        // Mouth movement animation
        const mouthAnimation = document.createElement('a-animation');
        mouthAnimation.setAttribute('attribute', 'rotation');
        mouthAnimation.setAttribute('to', '0 0 5');
        mouthAnimation.setAttribute('direction', 'alternate');
        mouthAnimation.setAttribute('dur', '200');
        mouthAnimation.setAttribute('repeat', 'indefinite');
        orange.appendChild(mouthAnimation);

        // Slight bounce
        const bounceAnimation = document.createElement('a-animation');
        bounceAnimation.setAttribute('attribute', 'position');
        bounceAnimation.setAttribute('to', '0 0.1 0');
        bounceAnimation.setAttribute('direction', 'alternate');
        bounceAnimation.setAttribute('dur', '300');
        bounceAnimation.setAttribute('repeat', 'indefinite');
        orange.appendChild(bounceAnimation);
    }

    addExcitedAnimation(orange) {
        // Bigger bounce
        const excitedAnimation = document.createElement('a-animation');
        excitedAnimation.setAttribute('attribute', 'position');
        excitedAnimation.setAttribute('to', '0 0.2 0');
        excitedAnimation.setAttribute('direction', 'alternate');
        excitedAnimation.setAttribute('dur', '500');
        excitedAnimation.setAttribute('repeat', 'indefinite');
        orange.appendChild(excitedAnimation);

        // Rotation
        const rotationAnimation = document.createElement('a-animation');
        rotationAnimation.setAttribute('attribute', 'rotation');
        rotationAnimation.setAttribute('to', '0 10 0');
        rotationAnimation.setAttribute('direction', 'alternate');
        rotationAnimation.setAttribute('dur', '1000');
        rotationAnimation.setAttribute('repeat', 'indefinite');
        orange.appendChild(rotationAnimation);
    }

    addIdleAnimation(orange) {
        // Gentle breathing
        const breathingAnimation = document.createElement('a-animation');
        breathingAnimation.setAttribute('attribute', 'scale');
        breathingAnimation.setAttribute('to', '1.05 1.05 1.05');
        breathingAnimation.setAttribute('direction', 'alternate');
        breathingAnimation.setAttribute('dur', '2000');
        breathingAnimation.setAttribute('repeat', 'indefinite');
        orange.appendChild(breathingAnimation);

        // Slight floating
        const floatAnimation = document.createElement('a-animation');
        floatAnimation.setAttribute('attribute', 'position');
        floatAnimation.setAttribute('to', '0 0.05 0');
        floatAnimation.setAttribute('direction', 'alternate');
        floatAnimation.setAttribute('dur', '3000');
        floatAnimation.setAttribute('repeat', 'indefinite');
        orange.appendChild(floatAnimation);
    }

    // Reset to idle animation
    resetToIdle() {
        this.animateOrange('idle');
    }

    // Get AR scene status
    getStatus() {
        return {
            initialized: this.isInitialized,
            markerDetected: this.markerDetected,
            sceneReady: !!document.querySelector('a-scene')
        };
    }
}
