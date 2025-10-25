/**
 * AR Manager for Talking Orange
 * Handles augmented reality detection and 3D character projection
 */

class ARManager {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.orangeCharacter = null;
        this.isARActive = false;
        this.animationId = null;
        this.markerDetected = false;
        this.markerImage = null;
        
        this.initializeAR();
    }
    
    initializeAR() {
        console.log('🍊 Initializing AR Manager...');
        
        // Create AR.js scene
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        
        // Set up renderer
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setClearColor(0x000000, 0);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        
        // Add renderer to camera screen
        const cameraContainer = document.getElementById('camera-feed');
        if (cameraContainer) {
            cameraContainer.appendChild(this.renderer.domElement);
        }
        
        // Load the marker image
        this.loadMarkerImage();
        
        // Create the 3D orange character
        this.createOrangeCharacter();
        
        // Set up lighting
        this.setupLighting();
        
        // Start animation loop
        this.animate();
        
        console.log('✅ AR Manager initialized');
    }
    
    loadMarkerImage() {
        console.log('🖼️ Loading marker image...');
        
        this.markerImage = new Image();
        this.markerImage.onload = () => {
            console.log('✅ Marker image loaded');
            this.startMarkerDetection();
        };
        this.markerImage.onerror = () => {
            console.error('❌ Failed to load marker image');
        };
        
        // Load the transparent talking orange image
        this.markerImage.src = '/talking-orange-transparent.png';
    }
    
    startMarkerDetection() {
        console.log('🔍 Starting marker detection...');
        
        // For demo purposes, we'll simulate marker detection
        // In a real implementation, this would use computer vision
        this.simulateMarkerDetection();
    }
    
    simulateMarkerDetection() {
        // Simulate marker detection after 3 seconds
        setTimeout(() => {
            if (this.isARActive && !this.markerDetected) {
                console.log('🎯 Marker detected! Showing 3D character...');
                this.markerDetected = true;
                this.showOrangeCharacter();
            }
        }, 3000);
    }
    
    createOrangeCharacter() {
        console.log('🍊 Creating 3D Orange Character...');
        
        // Create orange body (sphere)
        const bodyGeometry = new THREE.SphereGeometry(1, 32, 32);
        const bodyMaterial = new THREE.MeshLambertMaterial({ 
            color: 0xff6b35,
            transparent: true,
            opacity: 0.9
        });
        const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
        body.position.y = 1;
        body.castShadow = true;
        body.receiveShadow = true;
        
        // Create eyes
        const eyeGeometry = new THREE.SphereGeometry(0.15, 16, 16);
        const eyeMaterial = new THREE.MeshLambertMaterial({ color: 0xffffff });
        
        const leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
        leftEye.position.set(-0.3, 1.2, 0.8);
        leftEye.castShadow = true;
        
        const rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
        rightEye.position.set(0.3, 1.2, 0.8);
        rightEye.castShadow = true;
        
        // Create pupils
        const pupilGeometry = new THREE.SphereGeometry(0.08, 16, 16);
        const pupilMaterial = new THREE.MeshLambertMaterial({ color: 0x000000 });
        
        const leftPupil = new THREE.Mesh(pupilGeometry, pupilMaterial);
        leftPupil.position.set(-0.3, 1.2, 0.9);
        
        const rightPupil = new THREE.Mesh(pupilGeometry, pupilMaterial);
        rightPupil.position.set(0.3, 1.2, 0.9);
        
        // Create mouth
        const mouthGeometry = new THREE.TorusGeometry(0.2, 0.05, 8, 16, Math.PI);
        const mouthMaterial = new THREE.MeshLambertMaterial({ color: 0x8B4513 });
        const mouth = new THREE.Mesh(mouthGeometry, mouthMaterial);
        mouth.position.set(0, 0.7, 0.8);
        mouth.rotation.x = Math.PI;
        
        // Create arms
        const armGeometry = new THREE.CylinderGeometry(0.1, 0.1, 0.8, 8);
        const armMaterial = new THREE.MeshLambertMaterial({ color: 0xff6b35 });
        
        const leftArm = new THREE.Mesh(armGeometry, armMaterial);
        leftArm.position.set(-0.8, 0.5, 0);
        leftArm.rotation.z = Math.PI / 4;
        leftArm.castShadow = true;
        
        const rightArm = new THREE.Mesh(armGeometry, armMaterial);
        rightArm.position.set(0.8, 0.5, 0);
        rightArm.rotation.z = -Math.PI / 4;
        rightArm.castShadow = true;
        
        // Create legs
        const legGeometry = new THREE.CylinderGeometry(0.15, 0.15, 0.6, 8);
        const legMaterial = new THREE.MeshLambertMaterial({ color: 0xff6b35 });
        
        const leftLeg = new THREE.Mesh(legGeometry, legMaterial);
        leftLeg.position.set(-0.3, -0.3, 0);
        leftLeg.castShadow = true;
        
        const rightLeg = new THREE.Mesh(legGeometry, legMaterial);
        rightLeg.position.set(0.3, -0.3, 0);
        rightLeg.castShadow = true;
        
        // Group all parts together
        this.orangeCharacter = new THREE.Group();
        this.orangeCharacter.add(body);
        this.orangeCharacter.add(leftEye);
        this.orangeCharacter.add(rightEye);
        this.orangeCharacter.add(leftPupil);
        this.orangeCharacter.add(rightPupil);
        this.orangeCharacter.add(mouth);
        this.orangeCharacter.add(leftArm);
        this.orangeCharacter.add(rightArm);
        this.orangeCharacter.add(leftLeg);
        this.orangeCharacter.add(rightLeg);
        
        // Position the character
        this.orangeCharacter.position.set(0, 0, 0);
        this.orangeCharacter.scale.set(0.5, 0.5, 0.5);
        
        // Add to scene
        this.scene.add(this.orangeCharacter);
        
        console.log('✅ 3D Orange Character created');
    }
    
    setupLighting() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        this.scene.add(ambientLight);
        
        // Directional light
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(5, 5, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(directionalLight);
        
        // Point light for warmth
        const pointLight = new THREE.PointLight(0xff6b35, 0.5, 10);
        pointLight.position.set(0, 2, 2);
        this.scene.add(pointLight);
    }
    
    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        
        if (this.orangeCharacter && this.isARActive) {
            // Gentle breathing animation
            const time = Date.now() * 0.001;
            this.orangeCharacter.scale.y = 0.5 + Math.sin(time * 2) * 0.02;
            
            // Gentle swaying
            this.orangeCharacter.rotation.y = Math.sin(time * 0.5) * 0.1;
            
            // Blinking animation
            const eyes = this.orangeCharacter.children.filter(child => 
                child.geometry instanceof THREE.SphereGeometry && 
                child.material.color.getHex() === 0xffffff
            );
            
            eyes.forEach(eye => {
                if (Math.random() < 0.01) { // 1% chance per frame
                    eye.scale.y = 0.1;
                    setTimeout(() => {
                        eye.scale.y = 1;
                    }, 100);
                }
            });
        }
        
        this.renderer.render(this.scene, this.camera);
    }
    
    startAR() {
        console.log('🍊 Starting AR experience...');
        this.isARActive = true;
        this.markerDetected = false;
        
        // Position camera for AR view
        this.camera.position.set(0, 1.6, 3);
        this.camera.lookAt(0, 0, 0);
        
        // Hide the 3D character until marker is detected
        if (this.orangeCharacter) {
            this.orangeCharacter.visible = false;
        }
        
        // Start marker detection
        if (this.markerImage) {
            this.startMarkerDetection();
        }
        
        console.log('✅ AR experience started - waiting for marker detection');
    }
    
    showOrangeCharacter() {
        console.log('🍊 Showing 3D Orange Character...');
        
        if (this.orangeCharacter) {
            // Animate the character appearing
            this.orangeCharacter.scale.set(0, 0, 0);
            this.orangeCharacter.visible = true;
            
            // Animate scale up
            const startTime = Date.now();
            const animate = () => {
                const elapsed = Date.now() - startTime;
                const progress = Math.min(elapsed / 1000, 1); // 1 second animation
                const scale = progress * 0.5; // Final scale of 0.5
                
                this.orangeCharacter.scale.set(scale, scale, scale);
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            };
            animate();
        }
    }
    
    stopAR() {
        console.log('🛑 Stopping AR experience...');
        this.isARActive = false;
        
        if (this.orangeCharacter) {
            this.orangeCharacter.visible = false;
        }
        
        console.log('✅ AR experience stopped');
    }
    
    // Handle window resize
    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }
    
    // Clean up
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        if (this.renderer) {
            this.renderer.dispose();
        }
        
        console.log('🧹 AR Manager cleaned up');
    }
}

// Export for use in main app
window.ARManager = ARManager;