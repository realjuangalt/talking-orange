/**
 * Camera and Video Diagnostics Module
 * 
 * Handles all camera/video element diagnostics and management.
 * Isolates video feed logic for easier debugging.
 */

/**
 * Setup comprehensive camera and video diagnostics for the AR scene.
 * 
 * @param {HTMLElement} scene - The A-Frame scene element
 */
function setupCameraDiagnostics(scene) {
    // Comprehensive camera and video element logging
    console.log('📹 [CAMERA] Starting camera diagnostics...');
    
    // Check if mediaDevices is available
    if (!navigator.mediaDevices) {
        console.error('❌ [CAMERA] navigator.mediaDevices not available');
    } else {
        console.log('✅ [CAMERA] navigator.mediaDevices available');
    }
    
    // Test camera access (just for diagnostics - MindAR will request its own stream)
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            console.log('✅ [CAMERA] Camera access granted (test)');
            console.log('📹 [CAMERA] Stream details:', {
                id: stream.id,
                active: stream.active,
                tracks: stream.getTracks().map(t => ({
                    kind: t.kind,
                    enabled: t.enabled,
                    readyState: t.readyState,
                    settings: t.getSettings()
                }))
            });
            // Stop test stream - MindAR will request its own stream
            stream.getTracks().forEach(track => {
                track.stop();
                console.log(`🛑 [CAMERA] Stopped test track: ${track.kind} (MindAR will request its own)`);
            });
        })
        .catch(err => {
            console.error('❌ [CAMERA] Camera access denied or error:', err);
            console.error('❌ [CAMERA] Error name:', err.name);
            console.error('❌ [CAMERA] Error message:', err.message);
            alert('Camera access is required for AR. Please grant camera permissions.');
        });
    
    // Monitor video element creation and state
    const checkVideoElement = () => {
        // Check for video elements - MindAR creates them outside the scene sometimes
        // Check both inside scene and in document body, and also check all video elements in the document
        const videoElementsInScene = scene.querySelectorAll('video');
        const videoElementsInBody = document.querySelectorAll('body video');
        const allVideoElementsInDoc = document.querySelectorAll('video'); // All videos in document
        const allVideoElements = Array.from(new Set([...videoElementsInScene, ...videoElementsInBody, ...allVideoElementsInDoc]));
        
        // Also check if MindAR system has a video reference
        const mindarSystem = scene.systems && scene.systems['mindar-image-system'];
        const mindarVideo = mindarSystem && mindarSystem.video;
        if (mindarVideo && !allVideoElements.includes(mindarVideo)) {
            allVideoElements.push(mindarVideo);
        }
        
        console.log(`📹 [VIDEO] Found ${allVideoElements.length} video element(s) total (${videoElementsInScene.length} in scene, ${videoElementsInBody.length} in body, ${mindarVideo ? '1 in MindAR system' : '0 in MindAR system'})`);
        
        const videoElements = allVideoElements;
        
        videoElements.forEach((video, index) => {
            console.log(`📹 [VIDEO] Video element ${index}:`, {
                id: video.id,
                src: video.src,
                srcObject: video.srcObject ? 'has stream' : 'no stream',
                readyState: video.readyState,
                videoWidth: video.videoWidth,
                videoHeight: video.videoHeight,
                width: video.width,
                height: video.height,
                visible: video.offsetParent !== null,
                display: window.getComputedStyle(video).display,
                visibility: window.getComputedStyle(video).visibility,
                opacity: window.getComputedStyle(video).opacity,
                zIndex: window.getComputedStyle(video).zIndex,
                position: window.getComputedStyle(video).position
            });
            
            // Check if video has a stream
            if (video.srcObject) {
                const stream = video.srcObject;
                console.log(`📹 [VIDEO] Video ${index} stream:`, {
                    active: stream.active,
                    tracks: stream.getTracks().length
                });
            } else {
                console.warn(`⚠️ [VIDEO] Video element ${index} has no srcObject (no camera stream attached)`);
            }
            
            // Monitor video events
            video.addEventListener('loadedmetadata', () => {
                console.log(`✅ [VIDEO] Video ${index} metadata loaded:`, {
                    videoWidth: video.videoWidth,
                    videoHeight: video.videoHeight,
                    duration: video.duration
                });
            });
            
            video.addEventListener('playing', () => {
                console.log(`▶️ [VIDEO] Video ${index} started playing`);
            });
            
            video.addEventListener('pause', () => {
                console.warn(`⏸️ [VIDEO] Video ${index} paused`);
            });
            
            video.addEventListener('error', (e) => {
                console.error(`❌ [VIDEO] Video ${index} error:`, e);
            });
        });
        
        // Also check canvas element (A-Frame renders to canvas)
        const canvas = scene.querySelector('canvas');
        if (canvas) {
            const canvasStyle = window.getComputedStyle(canvas);
            console.log('🎨 [CANVAS] Canvas element found:', {
                width: canvas.width,
                height: canvas.height,
                visible: canvas.offsetParent !== null,
                display: canvasStyle.display,
                zIndex: canvasStyle.zIndex,
                position: canvasStyle.position,
                opacity: canvasStyle.opacity,
                backgroundColor: canvasStyle.backgroundColor
            });
        } else {
            console.warn('⚠️ [CANVAS] No canvas element found in scene');
        }
        
        // Check body and scene background
        const bodyStyle = window.getComputedStyle(document.body);
        const sceneStyle = window.getComputedStyle(scene);
        console.log('🎨 [STYLES] Body styles:', {
            backgroundColor: bodyStyle.backgroundColor,
            width: bodyStyle.width,
            height: bodyStyle.height,
            overflow: bodyStyle.overflow
        });
        console.log('🎨 [STYLES] Scene styles:', {
            backgroundColor: sceneStyle.backgroundColor,
            width: sceneStyle.width,
            height: sceneStyle.height,
            position: sceneStyle.position,
            zIndex: sceneStyle.zIndex
        });
    };
    
    // Check video element immediately and periodically
    setTimeout(checkVideoElement, 500); // Check after 500ms
    setTimeout(checkVideoElement, 1000); // Check after 1s
    setTimeout(checkVideoElement, 2000); // Check after 2s
    setTimeout(checkVideoElement, 3000); // Check after 3s
    
    // Also check when scene is loaded
    scene.addEventListener('loaded', () => {
        setTimeout(checkVideoElement, 500);
    });
    
    // Monitor MindAR video element creation
    const checkMindARVideo = () => {
        const mindarSystem = scene.systems['mindar-image-system'];
        if (mindarSystem) {
            // Check if video exists in system or in DOM
            const videoInSystem = mindarSystem.video;
            const videoInDOM = document.querySelector('video');
            
            console.log('📹 [MINDAR] MindAR system video check:', {
                hasVideoInSystem: !!videoInSystem,
                hasVideoInDOM: !!videoInDOM,
                videoElement: videoInSystem ? {
                    readyState: videoInSystem.readyState,
                    videoWidth: videoInSystem.videoWidth,
                    videoHeight: videoInSystem.videoHeight,
                    srcObject: videoInSystem.srcObject ? 'has stream' : 'no stream'
                } : (videoInDOM ? {
                    readyState: videoInDOM.readyState,
                    videoWidth: videoInDOM.videoWidth,
                    videoHeight: videoInDOM.videoHeight,
                    srcObject: videoInDOM.srcObject ? 'has stream' : 'no stream',
                    display: window.getComputedStyle(videoInDOM).display,
                    visibility: window.getComputedStyle(videoInDOM).visibility
                } : 'no video element found')
            });
            
            // If video exists but isn't visible, try to make it visible
            if (videoInDOM) {
                const videoStyle = window.getComputedStyle(videoInDOM);
                if (videoStyle.display === 'none' || videoStyle.visibility === 'hidden' || parseFloat(videoStyle.opacity) === 0) {
                    console.warn('⚠️ [VIDEO] Video element found but hidden, attempting to show...', {
                        display: videoStyle.display,
                        visibility: videoStyle.visibility,
                        opacity: videoStyle.opacity
                    });
                    videoInDOM.style.cssText = `
                        display: block !important;
                        visibility: visible !important;
                        opacity: 1 !important;
                        width: 100% !important;
                        height: 100% !important;
                        position: absolute !important;
                        top: 0 !important;
                        left: 0 !important;
                        z-index: 0 !important;
                        object-fit: cover !important;
                    `;
                }
            }
        }
    };
    
    // Check MindAR video after system is ready and periodically
    let mindarCheckCount = 0;
    const mindarCheckInterval = setInterval(() => {
        mindarCheckCount++;
        if (scene.systems && scene.systems['mindar-image-system']) {
            checkMindARVideo();
            
            // If video still doesn't exist after a few checks, try to help MindAR start
            const mindarSystem = scene.systems['mindar-image-system'];
            if (mindarSystem && !mindarSystem.video && mindarCheckCount >= 3) {
                // Check if scene is playing (required for MindAR to work)
                if (!scene.isPlaying) {
                    console.log('▶️ [MINDAR] Scene not playing, attempting to start scene...');
                    scene.play();
                }
                
                // Check if MindAR has a start method and try to start it
                if (typeof mindarSystem.start === 'function') {
                    console.log('🚀 [MINDAR] Attempting to start MindAR system...');
                    try {
                        mindarSystem.start();
                    } catch (e) {
                        console.warn('⚠️ [MINDAR] Error starting MindAR:', e);
                    }
                }
            }
        }
        
        // Stop checking after 20 attempts (10 seconds)
        if (mindarCheckCount >= 20) {
            clearInterval(mindarCheckInterval);
            if (!scene.systems || !scene.systems['mindar-image-system'] || !scene.systems['mindar-image-system'].video) {
                console.warn('⚠️ [MINDAR] Video element still not created after 10 seconds');
                console.log('💡 [MINDAR] MindAR may require user interaction (click/tap) to start the camera');
                
                // Show a user-visible message
                const messageDiv = document.createElement('div');
                messageDiv.id = 'camera-start-message';
                messageDiv.style.cssText = `
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: rgba(0, 0, 0, 0.8);
                    color: white;
                    padding: 20px 30px;
                    border-radius: 10px;
                    z-index: 10000;
                    text-align: center;
                    font-size: 18px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
                `;
                messageDiv.textContent = '👆 Tap anywhere to start camera';
                document.body.appendChild(messageDiv);
                
                // Remove message after user interaction
                const removeMessage = () => {
                    if (messageDiv.parentNode) {
                        messageDiv.parentNode.removeChild(messageDiv);
                    }
                    document.removeEventListener('click', removeMessage);
                    document.removeEventListener('touchstart', removeMessage);
                };
                document.addEventListener('click', removeMessage, { once: true });
                document.addEventListener('touchstart', removeMessage, { once: true });
            }
        }
    }, 500);
    
    // Also check periodically for video element creation in DOM
    let videoCheckCount = 0;
    const videoCheckInterval = setInterval(() => {
        videoCheckCount++;
        checkVideoElement();
        
        // If we've checked 20 times (10 seconds) and still no video, log a warning
        if (videoCheckCount >= 20) {
            console.warn('⚠️ [VIDEO] Video element still not found in DOM after 10 seconds');
            clearInterval(videoCheckInterval);
        }
    }, 500);
}

// Export functions for use in other modules
if (typeof window !== 'undefined') {
    window.setupCameraDiagnostics = setupCameraDiagnostics;
}

