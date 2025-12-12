/**
 * AR Core Module
 * 
 * Core AR initialization, target loading, media loading.
 * Foundation for everything else.
 */

// Global variables (shared with index.html)
// These will be accessible via window object after module loads
let availableTargets = [];
let currentTarget = null;
let currentTargetMedia = null;

// Helper to get current target (checks both local and window)
function getCurrentTarget() {
    return window.currentTarget || currentTarget;
}

function getCurrentTargetMedia() {
    return window.currentTargetMedia || currentTargetMedia;
}

/**
 * Load project-specific UI
 */
async function loadProjectUI(userId, projectName) {
    try {
        console.log(`📦 Loading project UI for ${userId}/${projectName}...`);
        const uiUrl = `/api/users/${userId}/${projectName}/ui`;
        const response = await fetch(uiUrl);
        
        if (!response.ok) {
            if (response.status === 404) {
                console.log(`ℹ️ No project UI file found for ${userId}/${projectName} (this is optional)`);
                return;
            }
            throw new Error(`Failed to load project UI: ${response.status}`);
        }
        
        const uiHtml = await response.text();
        const container = document.getElementById('project-ui-container');
        if (container) {
            // Extract scripts from HTML before inserting (scripts don't execute when using innerHTML)
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = uiHtml;
            const scripts = tempDiv.querySelectorAll('script');
            
            // Remove scripts from HTML before inserting
            scripts.forEach(script => script.remove());
            
            // Insert HTML without scripts
            container.innerHTML = tempDiv.innerHTML;
            container.style.display = 'block'; // Make sure it's visible
            console.log(`✅ Project UI loaded for ${userId}/${projectName}`);
            console.log(`📦 UI container is now visible: ${container.style.display}`);
            console.log(`📦 UI container innerHTML length: ${container.innerHTML.length} characters`);
            
            // Log what buttons were loaded
            const buttons = container.querySelectorAll('button');
            console.log(`🔘 Found ${buttons.length} button(s) in loaded UI:`, Array.from(buttons).map(btn => btn.id || btn.className || btn.textContent.trim().substring(0, 30)));
            
            // Execute extracted scripts
            if (scripts.length > 0) {
                console.log(`📜 Found ${scripts.length} script(s) in UI, executing...`);
                scripts.forEach((script, index) => {
                    try {
                        const newScript = document.createElement('script');
                        if (script.src) {
                            newScript.src = script.src;
                        } else {
                            newScript.textContent = script.textContent;
                        }
                        document.head.appendChild(newScript);
                        console.log(`✅ Executed script ${index + 1}/${scripts.length}`);
                    } catch (error) {
                        console.error(`❌ Error executing script ${index + 1}:`, error);
                    }
                });
            }
            
            // Update button text after UI loads (project-specific function)
            if (typeof window.updateTalkingOrangeButtonText === 'function') {
                setTimeout(() => window.updateTalkingOrangeButtonText(), 100); // Small delay to ensure DOM is ready
            }
            
            // Also check if talkingOrangeToggleLanguage is now available
            if (typeof window.talkingOrangeToggleLanguage === 'function') {
                console.log('✅ talkingOrangeToggleLanguage function is available');
            } else {
                console.warn('⚠️ talkingOrangeToggleLanguage function not found after loading UI');
            }
        } else {
            console.error('❌ Project UI container not found - element with id "project-ui-container" is missing from DOM');
        }
    } catch (error) {
        console.warn(`⚠️ Error loading project UI: ${error.message}`);
    }
}

/**
 * Load available AR targets from API
 */
async function loadAvailableTargets() {
    try {
        console.log('📡 Loading available AR targets...');
        const response = await fetch('/api/targets');
        const data = await response.json();
        
        if (response.ok && data.targets) {
            availableTargets = data.targets;
            window.availableTargets = availableTargets; // Make global
            console.log(`✅ Loaded ${availableTargets.length} AR target(s):`, availableTargets.map(t => t.targetId));
            
            // Select first target (or default talking-orange if available)
            const defaultTarget = availableTargets.find(t => t.userId === 'user-talking-orange' || t.userId === 'talking-orange' || t.isDefault) || availableTargets[0];
            if (defaultTarget) {
                currentTarget = defaultTarget;
                currentTargetMedia = defaultTarget.media || [];
                window.currentTarget = currentTarget; // Make global
                window.currentTargetMedia = currentTargetMedia; // Make global
                console.log(`🎯 Selected target: ${currentTarget.targetId} (${currentTarget.userId})`);
                console.log('🔍 [TARGET] Target structure:', {
                    userId: currentTarget.userId,
                    projectName: currentTarget.projectName,
                    targetId: currentTarget.targetId,
                    url: currentTarget.url
                });
            }
        } else {
            console.warn('⚠️ No targets found, using fallback');
            // Fallback to default
            currentTarget = {
                targetId: 'talking-orange_default',
                userId: 'talking-orange',
                filename: 'targets.mind',
                url: './media/targets.mind',
                media: [],
                isDefault: true
            };
            window.currentTarget = currentTarget;
            window.currentTargetMedia = [];
        }
    } catch (error) {
        console.error('❌ Error loading targets:', error);
        // Fallback to default
        currentTarget = {
            targetId: 'talking-orange_default',
            userId: 'talking-orange',
            filename: 'targets.mind',
            url: './media/targets.mind',
            media: [],
            isDefault: true
        };
        window.currentTarget = currentTarget;
        window.currentTargetMedia = [];
    }
}

/**
 * Initialize AR system
 */
function initializeARSystem() {
    const scene = document.querySelector('#ar-scene');
    const marker = document.querySelector('#ar-marker');
    const orangePlane = document.querySelector('#talking-orange-plane');
    const assets = document.querySelector('#ar-assets');
    
    console.log('🔍 [SCENE] Scene:', scene);
    console.log('🔍 [SCENE] Marker:', marker);
    console.log('🔍 [SCENE] Orange Plane:', orangePlane);
    
    const target = getCurrentTarget();
    if (!target) {
        console.error('❌ No target available for AR initialization');
        return;
    }
    
    // Set up MindAR with the selected target
    // MindAR will create the video element when it initializes
    const targetUrl = target.url;
    console.log(`🎯 Initializing AR with target: ${targetUrl}`);
    
    // Set up MindAR with the selected target immediately
    // Setting this attribute triggers MindAR to initialize and create the video element
    console.log(`🎯 Setting mindar-image attribute with target: ${targetUrl}`);
    scene.setAttribute('mindar-image', `imageTargetSrc: ${targetUrl}; maxTrack: 1; missTolerance: 80; warmupTolerance: 8; filterMinCF: 0.00001; filterBeta: 10000; uiLoading: yes; uiScanning: no; uiError: yes;`);
    
    // Load media assets based on current target
    loadTargetMedia(assets, orangePlane);
    
    // Ensure scene starts playing (MindAR needs scene to be playing to create video element)
    // The scene should start automatically, but we can ensure it does
    const ensureScenePlaying = () => {
        if (!scene.isPlaying) {
            console.log('▶️ [SCENE] Starting scene playback...');
            scene.play();
        }
    };
    
    // Try immediately, and also when scene loads
    ensureScenePlaying();
    scene.addEventListener('loaded', ensureScenePlaying, { once: true });
    
    // Add user interaction handler to help MindAR start (browsers require user interaction for camera)
    // This will trigger when user clicks/taps anywhere on the page
    const handleUserInteraction = () => {
        console.log('👆 [MINDAR] User interaction detected, checking MindAR...');
        ensureScenePlaying();
        
        const mindarSystem = scene.systems && scene.systems['mindar-image-system'];
        if (mindarSystem) {
            // Try to start MindAR if it hasn't started yet
            if (!mindarSystem.video && typeof mindarSystem.start === 'function') {
                console.log('🚀 [MINDAR] Attempting to start MindAR after user interaction...');
                try {
                    mindarSystem.start();
                } catch (e) {
                    console.warn('⚠️ [MINDAR] Error starting MindAR:', e);
                }
            }
        }
        
        // Remove listeners after first interaction
        document.removeEventListener('click', handleUserInteraction);
        document.removeEventListener('touchstart', handleUserInteraction);
    };
    
    // Listen for user interaction (click or touch)
    document.addEventListener('click', handleUserInteraction, { once: true });
    document.addEventListener('touchstart', handleUserInteraction, { once: true });
    
    console.log('🔍 [SCENE] All elements initialized');
    
    // Check Whisper device (CPU/GPU) on startup
    fetch('/api/health')
        .then(response => response.json())
        .then(data => {
            const deviceInfo = data.whisper_device || {};
            const device = deviceInfo.device || 'unknown';
            const useFp16 = deviceInfo.use_fp16 || false;
            const modelName = deviceInfo.model_name || 'unknown';
            
            if (device === 'cuda') {
                console.log(`🚀 [WHISPER] Running on GPU (CUDA) - Fast mode enabled`, {
                    device: device,
                    fp16: useFp16,
                    model: modelName
                });
            } else if (device === 'cpu') {
                console.warn(`⚠️ [WHISPER] Running on CPU - This may be slower`, {
                    device: device,
                    fp16: useFp16,
                    model: modelName,
                    note: 'Consider using GPU for better performance'
                });
            } else {
                console.warn(`⚠️ [WHISPER] Device status unknown`, deviceInfo);
            }
        })
        .catch(error => {
            console.warn('⚠️ [WHISPER] Could not check device status:', error);
        });
    
    // Wait for scene to be loaded before initializing
    scene.addEventListener('loaded', function() {
        console.log('✅ A-Scene loaded event fired');
        // Small delay to ensure mesh is created
        setTimeout(() => {
            const mesh = orangePlane ? orangePlane.getObject3D('mesh') : null;
            if (mesh) {
                console.log('✅ Mesh is ready');
            } else {
                console.warn('⚠️ Mesh not found after scene loaded, will retry on demand');
            }
        }, 100);
    });
    
    // Initialize immediately (mesh checks will handle readiness)
    // Add MindAR system debugging and ensure it starts
    scene.addEventListener('loaded', function() {
        console.log('✅ A-Scene loaded');
        const mindarSystem = scene.systems['mindar-image-system'];
        if (mindarSystem) {
            console.log('✅ MindAR system found:', mindarSystem);
            console.log('📊 MindAR config:', {
                imageTargetSrc: mindarSystem.imageTargetSrc,
                maxTrack: mindarSystem.maxTrack,
                missTolerance: mindarSystem.missTolerance,
                warmupTolerance: mindarSystem.warmupTolerance
            });
            
            // Try to ensure MindAR starts (some browsers require user interaction)
            // Check if MindAR has started and if not, try to start it
            setTimeout(() => {
                if (!mindarSystem.video) {
                    console.log('⚠️ [MINDAR] Video element not created yet, MindAR may need user interaction to start');
                    console.log('💡 [MINDAR] Try clicking/tapping on the page to trigger camera access');
                    
                    // Add a one-time click handler to start MindAR if needed
                    const startOnClick = () => {
                        console.log('👆 [MINDAR] User interaction detected, checking if MindAR needs to start...');
                        if (mindarSystem && typeof mindarSystem.start === 'function') {
                            try {
                                mindarSystem.start();
                                console.log('✅ [MINDAR] Attempted to start MindAR system');
                            } catch (e) {
                                console.warn('⚠️ [MINDAR] Error starting MindAR:', e);
                            }
                        }
                        // Remove listener after first click
                        document.removeEventListener('click', startOnClick);
                        document.removeEventListener('touchstart', startOnClick);
                    };
                    
                    // Listen for user interaction to start MindAR
                    document.addEventListener('click', startOnClick, { once: true });
                    document.addEventListener('touchstart', startOnClick, { once: true });
                }
            }, 1000);
        } else {
            console.error('❌ MindAR system not found!');
        }
    });
    
    // Setup camera diagnostics (from camera-video.js module)
    if (typeof setupCameraDiagnostics === 'function') {
        setupCameraDiagnostics(scene);
    } else {
        console.warn('⚠️ setupCameraDiagnostics function not found - camera-video.js module may not be loaded');
    }
    
    // Setup tracking system (from tracking-system.js module)
    // Wait for scene to be ready before setting up tracking
    scene.addEventListener('loaded', function() {
        console.log('✅ [AR-CORE] Scene loaded, setting up tracking system...');
        setTimeout(() => {
            if (typeof setupTrackingSystem === 'function') {
                console.log('✅ [AR-CORE] Calling setupTrackingSystem...');
                setupTrackingSystem(marker, orangePlane);
                console.log('✅ [AR-CORE] setupTrackingSystem called');
            } else {
                console.error('❌ setupTrackingSystem function not found - tracking-system.js module may not be loaded');
            }
        }, 500); // Small delay to ensure marker is ready
    });
    
    // Also try to set up tracking immediately if scene is already loaded
    if (scene.hasLoaded) {
        console.log('✅ [AR-CORE] Scene already loaded, setting up tracking system immediately...');
        setTimeout(() => {
            if (typeof setupTrackingSystem === 'function') {
                setupTrackingSystem(marker, orangePlane);
            }
        }, 500);
    }
    
    // Check for MindAR system (check immediately and periodically if not ready)
    const checkMindAR = () => {
        if (scene && scene.systems && scene.systems['mindar-image-system']) {
            console.log('✅ MindAR system found:', scene.systems['mindar-image-system']);
            return true;
        }
        return false;
    };
    
    // Check immediately first
    if (!checkMindAR()) {
        // If not ready, check periodically (but don't delay page load)
        const checkInterval = setInterval(() => {
            if (checkMindAR()) {
                clearInterval(checkInterval);
            }
        }, 200);
        // Stop checking after 5 seconds max
        setTimeout(() => clearInterval(checkInterval), 5000);
    }
}

/**
 * Load target media assets
 */
function loadTargetMedia(assets, orangePlane) {
    const targetMedia = getCurrentTargetMedia();
    if (!targetMedia || targetMedia.length === 0) {
        console.warn('⚠️ No media available for target, using defaults');
        // Fallback to default media paths
        loadDefaultMedia(assets);
        return;
    }
    
    // Find image files for different states
    const images = targetMedia.filter(m => m.type === 'image');
    const smileImg = images.find(m => m.filename.includes('smile')) || images[0];
    const winkImg = images.find(m => m.filename.includes('wink'));
    const thinkingImgs = images.filter(m => m.filename.includes('thinking')).sort();
    const talkingImgs = images.filter(m => m.filename.includes('talking')).sort();
    
    // Create asset elements
    if (smileImg) {
        const img = document.createElement('img');
        img.id = 'talking-orange';
        img.src = smileImg.url;
        assets.appendChild(img);
    }
    
    if (winkImg) {
        const img = document.createElement('img');
        img.id = 'talking-orange-wink';
        img.src = winkImg.url;
        assets.appendChild(img);
    }
    
    if (thinkingImgs.length > 0) {
        thinkingImgs.forEach((imgData, index) => {
            const img = document.createElement('img');
            img.id = `talking-orange-thinking-${index + 1}`;
            img.src = imgData.url;
            assets.appendChild(img);
        });
    }
    
    if (talkingImgs.length > 0) {
        talkingImgs.forEach((imgData, index) => {
            const img = document.createElement('img');
            img.id = `talking-orange-talking-${index + 1}`;
            img.src = imgData.url;
            assets.appendChild(img);
        });
    }
    
    // Find video animations and build URLs
    const videoAnimations = targetMedia.filter(m => m.type === 'video_animation');
    if (videoAnimations.length > 0) {
        window.targetVideoAnimations = videoAnimations.map(anim => {
            return {
                filename: anim.filename,
                url: anim.url
            };
        });
        console.log(`📹 Found ${videoAnimations.length} video animation(s)`);
    }
    
    // Set initial orange plane image
    if (smileImg && orangePlane) {
        orangePlane.setAttribute('src', '#talking-orange');
    }
    
    // Store current target globally for other modules
    const target = getCurrentTarget();
    window.currentTarget = target;
    window.currentTargetMedia = targetMedia;
    
    // Don't load project UI here - wait for target to be actually detected
    // Project UI will be loaded when targetFound event fires
    
    // If animation module exists, reload frame animations now that we have target info
    if (window.animationModule && typeof window.animationModule.loadFrameAnimations === 'function') {
        console.log('🔄 Reloading frame animations with target media URLs...');
        // Update paths in animation module based on current target
        if (typeof window.animationModule.updatePathsFromTarget === 'function') {
            window.animationModule.updatePathsFromTarget();
        }
        window.animationModule.loadFrameAnimations().catch(err => {
            console.warn('⚠️ Frame animation reload error (non-critical):', err);
        });
    }
    
    // Update animation controller audio URLs with correct project-based paths
    const currentTarget = getCurrentTarget();
    if (window.thinkingController && currentTarget) {
        const thinkingAudioUrl = getAudioUrl('thinking-hmm.mp3');
        if (thinkingAudioUrl && thinkingAudioUrl !== window.thinkingController.audioUrl) {
            console.log(`🔄 Updating thinking controller audio URL: ${thinkingAudioUrl}`);
            window.thinkingController.audioUrl = thinkingAudioUrl;
        }
    }
    
    if (window.talkingController && currentTarget) {
        const currentLang = window.currentLanguage || 'en';
        const introAudioUrl = currentLang === 'es' 
            ? getAudioUrl('talking-intro-es.mp3')
            : getAudioUrl('talking-intro.mp3');
        if (introAudioUrl && introAudioUrl !== window.talkingController.introAudioUrl) {
            console.log(`🔄 Updating talking controller audio URL: ${introAudioUrl}`);
            window.talkingController.introAudioUrl = introAudioUrl;
        }
    }
    
    console.log('✅ Target media loaded');
}

/**
 * Load default media (fallback)
 */
function loadDefaultMedia(assets) {
    // Fallback to default media paths - try to use API if target is available
    const target = window.currentTarget || currentTarget;
    let basePath = './media/';
    
    if (target && target.userId && target.projectName) {
        basePath = `/api/users/${target.userId}/${target.projectName}/media/`;
    } else if (target && target.userId) {
        basePath = `/api/users/${target.userId}/media/`;
    }
    
    const defaultImages = [
        { id: 'talking-orange', src: `${basePath}talking-orange-smile.png` },
        { id: 'talking-orange-wink', src: `${basePath}talking-orange-wink.png` },
        { id: 'talking-orange-thinking-1', src: `${basePath}talking-orange-thinking-1.png` },
        { id: 'talking-orange-thinking-2', src: `${basePath}talking-orange-thinking-2.png` },
        { id: 'talking-orange-talking-1', src: `${basePath}talking-orange-talking-1.png` },
        { id: 'talking-orange-talking-2', src: `${basePath}talking-orange-talking-2.png` },
        { id: 'talking-orange-talking-3', src: `${basePath}talking-orange-talking-3.png` },
        { id: 'talking-orange-talking-4', src: `${basePath}talking-orange-talking-4.png` }
    ];
    
    defaultImages.forEach(imgData => {
        const img = document.createElement('img');
        img.id = imgData.id;
        img.src = imgData.src;
        assets.appendChild(img);
    });
    
    const orangePlane = document.querySelector('#talking-orange-plane');
    if (orangePlane) {
        orangePlane.setAttribute('src', '#talking-orange');
    }
}

/**
 * Get audio URL helper (needed by loadTargetMedia)
 * This will be defined in the main index.html or voice-processing module
 */
function getAudioUrl(filename) {
    const targetMedia = getCurrentTargetMedia();
    const target = getCurrentTarget();
    
    if (targetMedia) {
        // First try to find exact match
        let audioFile = targetMedia.find(m => m.filename === filename);
        if (audioFile) return audioFile.url;
        
        // Then try partial match
        audioFile = targetMedia.find(m => m.filename.includes(filename) || filename.includes(m.filename));
        if (audioFile) return audioFile.url;
        
        // Try to construct URL from current target and video directory (project-based)
        if (target && target.userId && target.projectName) {
            // Audio files are in video directories
            if (filename.includes('thinking')) {
                return `/api/users/${currentTarget.userId}/${currentTarget.projectName}/media/videos/talking-orange-thinking-animation/thinking-hmm.mp3`;
            } else if (filename.includes('intro-es')) {
                return `/api/users/${currentTarget.userId}/${currentTarget.projectName}/media/videos/talking-orange-talking-animation/talking-intro-es.mp3`;
            } else if (filename.includes('intro') || filename.includes('talking')) {
                return `/api/users/${currentTarget.userId}/${currentTarget.projectName}/media/videos/talking-orange-talking-animation/talking-intro.mp3`;
            }
        } else if (target && target.userId) {
            // Fallback to old structure if no projectName
            if (filename.includes('thinking')) {
                return `/api/users/${currentTarget.userId}/media/videos/talking-orange-thinking-animation/thinking-hmm.mp3`;
            } else if (filename.includes('intro-es')) {
                return `/api/users/${currentTarget.userId}/media/videos/talking-orange-talking-animation/talking-intro-es.mp3`;
            } else if (filename.includes('intro') || filename.includes('talking')) {
                return `/api/users/${currentTarget.userId}/media/videos/talking-orange-talking-animation/talking-intro.mp3`;
            }
        }
    }
    // Final fallback to default frontend paths (shouldn't happen in normal operation)
    console.warn(`⚠️ [AUDIO] No target context, using fallback path for ${filename}`);
    if (filename.includes('thinking')) {
        return './media/videos/talking-orange-thinking-animation/thinking-hmm.mp3';
    } else if (filename.includes('intro-es')) {
        return './media/videos/talking-orange-talking-animation/talking-intro-es.mp3';
    } else {
        return './media/videos/talking-orange-talking-animation/talking-intro.mp3';
    }
}

// Export functions globally
if (typeof window !== 'undefined') {
    window.loadProjectUI = loadProjectUI;
    window.loadAvailableTargets = loadAvailableTargets;
    window.initializeARSystem = initializeARSystem;
    window.loadTargetMedia = loadTargetMedia;
    window.loadDefaultMedia = loadDefaultMedia;
    window.getAudioUrl = getAudioUrl;
    // Export global variables
    window.availableTargets = availableTargets;
    window.currentTarget = currentTarget;
    window.currentTargetMedia = currentTargetMedia;
}

