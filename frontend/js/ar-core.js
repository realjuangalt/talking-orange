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
            
            // Log all targets with their media
            availableTargets.forEach(target => {
                console.log(`🎯 [TARGET] ${target.targetId}:`, {
                    userId: target.userId,
                    projectName: target.projectName,
                    url: target.url,
                    mediaCount: target.media?.length || 0,
                    media: target.media?.map(m => `${m.filename} (${m.type})`) || []
                });
            });
            
            // Artivive-style: Don't pre-select a target
            // Instead, we'll try each target until one is detected by the camera
            // Store all available targets globally for dynamic switching
            window.allAvailableTargets = availableTargets;
            console.log(`📋 [TARGET] Loaded ${availableTargets.length} target(s) - will auto-detect which one is visible`);
            
            // Initialize with first target to start detection, but we'll switch dynamically
            // when a different target is actually detected
            if (availableTargets.length > 0) {
                // Start with first target (will switch when camera detects a different one)
                currentTarget = availableTargets[0];
                currentTargetMedia = availableTargets[0].media || [];
                window.currentTarget = currentTarget;
                window.currentTargetMedia = currentTargetMedia;
                console.log(`🎯 [TARGET] Starting with first target for detection: ${currentTarget.targetId}`);
                console.log(`📋 [TARGET] All ${availableTargets.length} targets available for auto-detection`);
            } else {
                console.warn('⚠️ [TARGET] No targets available');
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

// Target scanning is now handled by target-scanner.js module
// Keep these for backward compatibility if needed, but prefer window.targetScanner

/**
 * Try next target for detection (Artivive-style auto-detection)
 * @deprecated Use window.targetScanner.tryNextTarget() instead
 */
function tryNextTarget() {
    if (window.targetScanner && typeof window.targetScanner.tryNextTarget === 'function') {
        return window.targetScanner.tryNextTarget();
    }
    console.error('❌ [AR-CORE] target-scanner.js not loaded - tryNextTarget requires scanner module');
}

/**
 * Lock onto a detected target (stop cycling)
 * @deprecated Use window.targetScanner.lockTarget() instead
 */
function lockTarget(target) {
    if (window.targetScanner && typeof window.targetScanner.lockTarget === 'function') {
        return window.targetScanner.lockTarget(target);
    }
    console.warn('⚠️ [AR-CORE] target-scanner.js not loaded, falling back to legacy function');
}

/**
 * Initialize AR system with auto-detection
 */
function initializeARSystem() {
    const scene = document.querySelector('#ar-scene');
    const marker = document.querySelector('#ar-marker');
    const orangePlane = document.querySelector('#talking-orange-plane');
    const assets = document.querySelector('#ar-assets');
    
    console.log('🔍 [SCENE] Scene:', scene);
    console.log('🔍 [SCENE] Marker:', marker);
    console.log('🔍 [SCENE] Orange Plane:', orangePlane);
    
    if (!window.allAvailableTargets || window.allAvailableTargets.length === 0) {
        console.error('❌ [TARGET] No targets available for AR initialization');
        return;
    }
    
    // Start with first target
    const target = window.allAvailableTargets[0];
    currentTarget = target;
    currentTargetMedia = target.media || [];
    window.currentTarget = currentTarget;
    window.currentTargetMedia = currentTargetMedia;
    
    const targetUrl = target.url;
    console.log(`🎯 [TARGET] Initializing AR with auto-detection mode`);
    console.log(`🎯 [TARGET] Starting with first target: ${target.targetId} (${targetUrl})`);
    console.log(`🔄 [TARGET] Will cycle through ${window.allAvailableTargets.length} target(s) until one is detected`);
    
    // Set up MindAR with the first target
    scene.setAttribute('mindar-image', `imageTargetSrc: ${targetUrl}; maxTrack: 1; missTolerance: 80; warmupTolerance: 8; filterMinCF: 0.00001; filterBeta: 10000; uiLoading: yes; uiScanning: no; uiError: yes;`);
    
    // Load media assets based on current target
    loadTargetMedia(assets, orangePlane);
    
    // Ensure scene starts playing (MindAR needs scene to be playing to create the video element)
    ensureScenePlaying(scene);
    scene.addEventListener('loaded', () => ensureScenePlaying(scene), { once: true });
    
    // Initialize target scanner
    if (window.targetScanner && typeof window.targetScanner.init === 'function') {
        window.targetScanner.init();
    }
    
    // Start cycling through targets if none detected after a delay
    // This allows time for the first target to be detected before switching
    setTimeout(() => {
        if (window.targetScanner && typeof window.targetScanner.startScanning === 'function') {
            console.log('🔄 [TARGET] Starting target scanner...');
            // Only start if not already locked (target might have been detected during the delay)
            if (!window.targetScanner.getState || !window.targetScanner.getState().targetLocked) {
                window.targetScanner.startScanning();
            } else {
                console.log('🔒 [TARGET] Target already locked, skipping scan start');
            }
        } else {
            console.warn('⚠️ [TARGET] target-scanner.js not loaded, using fallback');
            // Fallback to old method if scanner not available
            if (window.targetScanner && typeof window.targetScanner.startScanning === 'function') {
                window.targetScanner.startScanning();
            } else if (typeof startTargetDetectionCycle === 'function') {
                startTargetDetectionCycle();
            }
        }
    }, 2000); // Wait 2 seconds before starting cycle

/**
 * Start cycling through targets for detection
 * @deprecated Use window.targetScanner.startScanning() instead
 */
function startTargetDetectionCycle() {
    if (window.targetScanner && typeof window.targetScanner.startScanning === 'function') {
        return window.targetScanner.startScanning();
    }
    console.warn('⚠️ [AR-CORE] target-scanner.js not loaded, startTargetDetectionCycle cannot function without scanner module');
}

/**
 * Ensure scene is playing (needed for MindAR)
 */
function ensureScenePlaying(scene) {
    if (!scene) {
        scene = document.querySelector('#ar-scene');
    }
    if (scene && !scene.isPlaying) {
        console.log('▶️ [SCENE] Starting scene playback...');
        scene.play();
    }
}
    
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
    const target = getCurrentTarget();
    
    console.log('📦 [MEDIA] Loading target media:', {
        targetId: target?.targetId,
        userId: target?.userId,
        projectName: target?.projectName,
        mediaCount: targetMedia?.length || 0,
        media: targetMedia?.map(m => ({ filename: m.filename, type: m.type, url: m.url }))
    });
    
    if (!targetMedia || targetMedia.length === 0) {
        console.warn('⚠️ No media available for target, using defaults');
        // Fallback to default media paths
        loadDefaultMedia(assets);
        return;
    }
    
    // Filter out target source images (these are for detection, not projection)
    // Target images are in targets/ folder or have target_source_ prefix
    const isTargetImage = (filename) => {
        const lower = filename.toLowerCase();
        return lower.includes('target_source_') || 
               lower.includes('/targets/') ||
               lower.startsWith('target_');
    };
    
    // Separate media into categories
    const allImages = targetMedia.filter(m => m.type === 'image');
    const images = allImages.filter(m => !isTargetImage(m.filename)); // Exclude target images
    const targetImages = allImages.filter(m => isTargetImage(m.filename)); // Target images (for reference only)
    
    console.log(`🖼️ [MEDIA] Found ${images.length} AR content image(s):`, images.map(img => img.filename));
    if (targetImages.length > 0) {
        console.log(`🎯 [MEDIA] Found ${targetImages.length} target image(s) (excluded from projection):`, targetImages.map(img => img.filename));
    }
    
    // Find animated content (GIFs, videos) - these should be prioritized for AR projection
    const gifs = images.filter(m => m.filename.toLowerCase().endsWith('.gif'));
    const videos = targetMedia.filter(m => m.type === 'video' || m.type === 'video_animation');
    
    console.log(`🎬 [MEDIA] Found ${gifs.length} GIF(s) and ${videos.length} video(s) for AR projection`);
    
    // For most projects: prioritize animated content (GIF/video) over static images
    // For talking-orange project: use special image selection logic
    const isTalkingOrangeProject = target?.projectName?.toLowerCase() === 'talking-orange';
    
    let defaultContent = null;
    let defaultContentType = null;
    
    if (isTalkingOrangeProject) {
        // Special handling for talking-orange project (multiple state images)
        const smileImg = images.find(m => m.filename.toLowerCase().includes('smile')) 
            || images.find(m => m.filename.toLowerCase().includes('default'))
            || images.find(m => !m.filename.toLowerCase().includes('wink') && !m.filename.toLowerCase().includes('thinking') && !m.filename.toLowerCase().includes('talking'))
            || images[0];
        defaultContent = smileImg;
        defaultContentType = 'image';
    } else {
        // For other projects: prioritize animated content
        // 1. GIFs (most common AR content)
        // 2. Videos
        // 3. Static images (only if no animated content)
        if (gifs.length > 0) {
            defaultContent = gifs[0]; // Use first GIF
            defaultContentType = 'gif';
            console.log(`🎬 [MEDIA] Using GIF for AR projection: ${defaultContent.filename}`);
        } else if (videos.length > 0) {
            defaultContent = videos[0]; // Use first video
            defaultContentType = 'video';
            console.log(`🎬 [MEDIA] Using video for AR projection: ${defaultContent.filename}`);
        } else if (images.length > 0) {
            // Fallback to static image only if no animated content
            defaultContent = images[0];
            defaultContentType = 'image';
            console.log(`🖼️ [MEDIA] Using static image for AR projection (no animated content): ${defaultContent.filename}`);
        }
    }
    
    // Legacy support for talking-orange project image states
    const smileImg = isTalkingOrangeProject ? defaultContent : null;
    const winkImg = images.find(m => m.filename.toLowerCase().includes('wink'));
    const thinkingImgs = images.filter(m => m.filename.toLowerCase().includes('thinking')).sort();
    const talkingImgs = images.filter(m => m.filename.toLowerCase().includes('talking')).sort();
    
    // Create asset elements
    if (smileImg) {
        const img = document.createElement('img');
        img.id = 'talking-orange';
        img.src = smileImg.url;
        img.onload = () => console.log(`✅ [MEDIA] Loaded default image: ${smileImg.filename} (${smileImg.url})`);
        img.onerror = () => console.error(`❌ [MEDIA] Failed to load image: ${smileImg.filename} (${smileImg.url})`);
        assets.appendChild(img);
        console.log(`🖼️ [MEDIA] Added default image asset: ${smileImg.filename} -> #talking-orange`);
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
    
    // Create asset elements for all content types
    // For GIFs (non-talking-orange projects)
    if (defaultContentType === 'gif' && defaultContent) {
        const gifImg = document.createElement('img');
        gifImg.id = 'ar-content-gif';
        gifImg.src = defaultContent.url;
        gifImg.onload = () => console.log(`✅ [MEDIA] Loaded GIF for AR projection: ${defaultContent.filename}`);
        gifImg.onerror = () => console.error(`❌ [MEDIA] Failed to load GIF: ${defaultContent.filename}`);
        // Remove existing GIF if any
        const existingGif = assets.querySelector('#ar-content-gif');
        if (existingGif) {
            assets.removeChild(existingGif);
        }
        assets.appendChild(gifImg);
    }
    
    // For talking-orange project, create image assets as before
    if (smileImg) {
        // Remove existing if any
        const existing = assets.querySelector('#talking-orange');
        if (existing) {
            assets.removeChild(existing);
        }
        const img = document.createElement('img');
        img.id = 'talking-orange';
        img.src = smileImg.url;
        img.onload = () => console.log(`✅ [MEDIA] Loaded default image: ${smileImg.filename} (${smileImg.url})`);
        img.onerror = () => console.error(`❌ [MEDIA] Failed to load image: ${smileImg.filename} (${smileImg.url})`);
        assets.appendChild(img);
        console.log(`🖼️ [MEDIA] Added default image asset: ${smileImg.filename} -> #talking-orange`);
    }
    
    // Set initial AR content to display on the plane
    if (defaultContent && orangePlane) {
        if (defaultContentType === 'gif') {
            // For GIFs, use the GIF asset we just created
            orangePlane.setAttribute('src', '#ar-content-gif');
            console.log(`🎨 [MEDIA] Set AR plane source to GIF: ${defaultContent.filename}`);
        } else if (defaultContentType === 'video') {
            // For videos, we'd need to handle video elements differently
            // For now, log a warning - video projection might need special handling
            console.warn('⚠️ [MEDIA] Video AR content detected - may need special handling');
            // Fallback to first image if available
            if (images.length > 0) {
                const img = document.createElement('img');
                img.id = 'ar-content-fallback';
                img.src = images[0].url;
                assets.appendChild(img);
                orangePlane.setAttribute('src', '#ar-content-fallback');
                console.log(`🎨 [MEDIA] Using fallback image for video content: ${images[0].filename}`);
            }
        } else if (smileImg) {
            // For talking-orange project or static images
            orangePlane.setAttribute('src', '#talking-orange');
            console.log(`🎨 [MEDIA] Set AR plane source to: #talking-orange (${smileImg.filename})`);
        } else if (images.length > 0) {
            // Fallback: use first available image (non-target image)
            const img = document.createElement('img');
            img.id = 'ar-content-image';
            img.src = images[0].url;
            assets.appendChild(img);
            orangePlane.setAttribute('src', '#ar-content-image');
            console.log(`🎨 [MEDIA] Set AR plane source to image: ${images[0].filename}`);
        } else {
            console.warn('⚠️ [MEDIA] No AR content available for projection');
        }
    } else if (orangePlane) {
        console.warn('⚠️ [MEDIA] No default content available for AR plane');
    }
    
    // Store current target globally for other modules (already have target from above)
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
    if (window.thinkingController && target) {
        const thinkingAudioUrl = getAudioUrl('thinking-hmm.mp3');
        if (thinkingAudioUrl && thinkingAudioUrl !== window.thinkingController.audioUrl) {
            console.log(`🔄 Updating thinking controller audio URL: ${thinkingAudioUrl}`);
            window.thinkingController.audioUrl = thinkingAudioUrl;
        }
    }
    
    if (window.talkingController && target) {
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
    // Artivive-style target detection functions (deprecated - use window.targetScanner instead)
    window.lockTarget = lockTarget;
    window.tryNextTarget = tryNextTarget;
    // Only export startTargetDetectionCycle if it's defined (it's a wrapper that uses scanner)
    if (typeof startTargetDetectionCycle === 'function') {
        window.startTargetDetectionCycle = startTargetDetectionCycle;
    }
    window.ensureScenePlaying = ensureScenePlaying;
    // Export global variables
    window.availableTargets = availableTargets;
    window.currentTarget = currentTarget;
    window.currentTargetMedia = currentTargetMedia;
}

