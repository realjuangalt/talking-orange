/**
 * AR Manager for Talking Orange
 * Handles augmented reality marker detection and 3D character projection
 */

class ARManager {
    constructor() {
        this.isARActive = false;
        this.markerDetected = false;
        this.orangeCharacter = null;
        this.animationId = null;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        
        console.log('🍊 AR Manager initialized');
    }
    
    initializeAR() {
        console.log('🍊 Initializing AR with marker detection...');
        
        // Create A-Frame scene for AR.js
        this.createARScene();
        
        // Set up marker detection
        this.setupMarkerDetection();
    }
    
    createARScene() {
        // Create A-Frame scene element
        const arScene = document.createElement('a-scene');
        arScene.setAttribute('vr-mode-ui', 'enabled: false');
        arScene.setAttribute('renderer', 'logarithmicDepthBuffer: true');
        arScene.setAttribute('embedded', '');
        arScene.setAttribute('arjs', 'trackingMethod: best; sourceType: webcam; debugUIEnabled: false');
        
        // Add camera
        const arCamera = document.createElement('a-camera');
        arCamera.setAttribute('gps-camera', '');
        arCamera.setAttribute('rotation-reader', '');
        arScene.appendChild(arCamera);
        
        // Add marker - using Hiro pattern for better detection
        const marker = document.createElement('a-marker');
        marker.setAttribute('type', 'pattern');
        marker.setAttribute('preset', 'hiro');
        marker.setAttribute('smooth', 'true');
        marker.setAttribute('smoothCount', '10');
        marker.setAttribute('smoothTolerance', '0.01');
        marker.setAttribute('smoothThreshold', '5');
        
        // Add 3D orange character to marker
        this.createOrangeForMarker(marker);
        
        arScene.appendChild(marker);
        
        // Add to camera container
        const cameraContainer = document.getElementById('camera-feed');
        if (cameraContainer) {
            cameraContainer.appendChild(arScene);
        }
        
        this.arScene = arScene;
        this.marker = marker;
        
        console.log('🍊 AR scene created with marker detection');
    }
    
    createOrangeForMarker(marker) {
        // Create 3D orange character using A-Frame entities
        const orangeEntity = document.createElement('a-entity');
        orangeEntity.setAttribute('geometry', 'primitive: sphere; radius: 0.5');
        orangeEntity.setAttribute('material', 'color: #ff8c00; transparent: true; opacity: 0.9');
        orangeEntity.setAttribute('position', '0 0.5 0');
        orangeEntity.setAttribute('animation__rotate', 'property: rotation; to: 0 360 0; loop: true; dur: 10000');
        
        // Add face features as child entities
        this.addFaceFeatures(orangeEntity);
        
        marker.appendChild(orangeEntity);
        
        // Add event listeners for marker detection
        marker.addEventListener('markerFound', () => {
            console.log('🍊 Marker detected! Orange character is now visible');
            this.markerDetected = true;
            this.onMarkerDetected();
        });
        
        marker.addEventListener('markerLost', () => {
            console.log('🍊 Marker lost');
            this.markerDetected = false;
            this.onMarkerLost();
        });
        
        this.orangeCharacter = orangeEntity;
    }
    
    addFaceFeatures(orangeEntity) {
        // Add left eye
        const leftEye = document.createElement('a-entity');
        leftEye.setAttribute('geometry', 'primitive: sphere; radius: 0.05');
        leftEye.setAttribute('material', 'color: black');
        leftEye.setAttribute('position', '-0.15 0.1 0.4');
        orangeEntity.appendChild(leftEye);
        
        // Add right eye
        const rightEye = document.createElement('a-entity');
        rightEye.setAttribute('geometry', 'primitive: sphere; radius: 0.05');
        rightEye.setAttribute('material', 'color: black');
        rightEye.setAttribute('position', '0.15 0.1 0.4');
        orangeEntity.appendChild(rightEye);
        
        // Add mouth
        const mouth = document.createElement('a-entity');
        mouth.setAttribute('geometry', 'primitive: sphere; radius: 0.08');
        mouth.setAttribute('material', 'color: black');
        mouth.setAttribute('position', '0 -0.1 0.4');
        mouth.setAttribute('scale', '1 0.5 1');
        orangeEntity.appendChild(mouth);
    }
    
    setupMarkerDetection() {
        console.log('🍊 Setting up marker detection for talking orange image');
        
        // The marker detection is handled by AR.js automatically
        // We just need to make sure the marker image is accessible
        this.ensureMarkerImage();
    }
    
    ensureMarkerImage() {
        // Check if marker image exists
        const markerImg = new Image();
        markerImg.onload = () => {
            console.log('✅ Marker image loaded successfully');
        };
        markerImg.onerror = () => {
            console.error('❌ Marker image not found. Please ensure talking-orange-transparent.png is in the root directory');
        };
        markerImg.src = 'talking-orange-transparent.png';
    }
    
    onMarkerDetected() {
        console.log('🎉 Orange character is now visible in AR!');
        
        // Add breathing animation
        if (this.orangeCharacter) {
            this.orangeCharacter.setAttribute('animation__breathe', 
                'property: scale; to: 1.1 1.1 1.1; dir: alternate; loop: true; dur: 2000');
        }
        
        // Show AR instructions
        this.showARInstructions();
    }
    
    onMarkerLost() {
        console.log('👋 Orange character is no longer visible');
        
        // Remove breathing animation
        if (this.orangeCharacter) {
            this.orangeCharacter.removeAttribute('animation__breathe');
        }
    }
    
    showARInstructions() {
        // Create overlay with AR instructions
        const overlay = document.createElement('div');
        overlay.id = 'ar-instructions';
        overlay.style.cssText = `
            position: fixed;
            top: 20px;
            left: 20px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 15px;
            border-radius: 10px;
            z-index: 1000;
            font-family: Arial, sans-serif;
            max-width: 300px;
        `;
        overlay.innerHTML = `
            <h3>🍊 Orange Detected!</h3>
            <p>The talking orange is now visible in AR. Use the microphone button to talk to it!</p>
        `;
        
        document.body.appendChild(overlay);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
        }, 5000);
    }
    
    
    startAR() {
        console.log('🍊 Starting AR experience...');
        this.isARActive = true;
        this.initializeAR();
    }
    
    stopAR() {
        console.log('🍊 Stopping AR experience...');
        this.isARActive = false;
        
        if (this.arScene && this.arScene.parentNode) {
            this.arScene.parentNode.removeChild(this.arScene);
        }
        
        // Remove AR instructions
        const instructions = document.getElementById('ar-instructions');
        if (instructions) {
            instructions.remove();
        }
    }
    
    isMarkerVisible() {
        return this.markerDetected;
    }
    
    getOrangeCharacter() {
        return this.orangeCharacter;
    }
}

// Export for use in main app
window.ARManager = ARManager;