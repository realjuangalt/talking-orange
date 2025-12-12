/**
 * Animation Module for Talking Orange Project
 * 
 * Handles all animation states and frame-based animations for the talking orange.
 * This is a project-specific module loaded dynamically after target detection.
 */

class TalkingAnimationModule {
    constructor(orangePlane) {
        this.orangePlane = orangePlane;
        
        // Initialize with fallback paths - will be updated when target is loaded
        this.idleState = { id: '#talking-orange', name: 'smile', src: './media/talking-orange-smile.png' };
        this.thinkingStates = [
            { id: '#talking-orange-thinking-1', name: 'thinking-1', src: './media/talking-orange-thinking-1.png' },
            { id: '#talking-orange-thinking-2', name: 'thinking-2', src: './media/talking-orange-thinking-2.png' }
        ];
        
        // Update paths based on current target if available
        this.updatePathsFromTarget();
        
        // Load talking states dynamically (sorted by number: 1, 2, 3, etc.)
        this.talkingStates = this.loadTalkingStates();
        
        // Load frame-based animations if available (advanced)
        this.talkingFrames = [];
        this.thinkingFrames = [];
        this.talkingTextures = {}; // Cache for preloaded textures
        this.thinkingTextures = {}; // Cache for preloaded textures
        this.frameMaterial = null; // Reusable material for frame animations
        this.useFrameAnimations = false;
        
        this.currentThinkingState = 0;
        this.currentTalkingState = 0;
        this.currentThinkingFrame = 0;
        this.currentTalkingFrame = 0;
        this.talkingDirection = 1; // 1 = forward (opening), -1 = backward (closing)
        this.fallbackTestMode = false; // When true, fallback animations stop after one cycle
        this.isTalking = false;
        this.isThinking = false;
        this.talkingInterval = null;
        this.thinkingInterval = null;
        this.debugMode = true;
        this.isIdle = true;
        
        this.init();
    }
    
    // Update paths based on current target (called after target is loaded)
    updatePathsFromTarget() {
        const target = window.currentTarget || currentTarget;
        if (target && target.userId && target.projectName) {
            // Update idle state path
            this.idleState.src = `/api/users/${target.userId}/${target.projectName}/media/talking-orange-smile.png`;
            // Update thinking states paths
            if (this.thinkingStates.length > 0) {
                this.thinkingStates[0].src = `/api/users/${target.userId}/${target.projectName}/media/talking-orange-thinking-1.png`;
            }
            if (this.thinkingStates.length > 1) {
                this.thinkingStates[1].src = `/api/users/${target.userId}/${target.projectName}/media/talking-orange-thinking-2.png`;
            }
        } else if (target && target.userId) {
            // Fallback to old structure
            this.idleState.src = `/api/users/${target.userId}/media/talking-orange-smile.png`;
            if (this.thinkingStates.length > 0) {
                this.thinkingStates[0].src = `/api/users/${target.userId}/media/talking-orange-thinking-1.png`;
            }
            if (this.thinkingStates.length > 1) {
                this.thinkingStates[1].src = `/api/users/${target.userId}/media/talking-orange-thinking-2.png`;
            }
        }
        // If no target, keep fallback paths
    }
    
    init() {
        console.log('🎭 Initializing Talking Animation Module');
        // Load frame animations asynchronously (non-blocking)
        // This allows MindAR to initialize immediately while frames load in background
        this.loadFrameAnimations().catch(err => {
            console.warn('⚠️ Frame animation loading error (non-critical):', err);
        });
        this.debugImageLoading();
    }
    
    async loadFrameAnimations() {
        // Try to load frame-based animations from video folders
        // Optimized: Skip slow discovery - we know there are 145 frames
        // Just check if first frame exists, then generate all paths
        try {
            // Check if target is available - if not, skip (will be called again after target loads)
            const target = window.currentTarget || currentTarget;
            if (!target || !target.userId) {
                console.log('⏳ [FRAMES] Target not loaded yet, skipping frame animation loading (will retry after target loads)');
                return;
            }
            
            // Get base URLs for video animations (will use project-based paths if available)
            const talkingBaseUrl = this.getVideoBaseUrl('talking-orange-talking-animation');
            const thinkingBaseUrl = this.getVideoBaseUrl('talking-orange-thinking-animation');
            
            console.log(`🔍 [FRAMES] Checking frame animations at:`, {
                talking: talkingBaseUrl,
                thinking: thinkingBaseUrl
            });
            
            // Quick check if talking animation exists (single HEAD request)
            try {
                const talkingResponse = await fetch(`${talkingBaseUrl}frame_00000.png`, { method: 'HEAD' });
            if (talkingResponse.ok) {
                // Generate frame paths directly (no sequential discovery needed)
                this.talkingFrames = this.generateFramePaths('talking-orange-talking-animation', 145);
                console.log(`✅ Generated ${this.talkingFrames.length} talking animation frame paths`);
                } else if (talkingResponse.status !== 404) {
                    // Only log non-404 errors (404 is expected if frames don't exist)
                    console.log(`⚠️ [FRAMES] Talking animation check failed at ${talkingBaseUrl}frame_00000.png (status: ${talkingResponse.status})`);
                }
            } catch (err) {
                // Silently handle fetch errors (network issues, CORS, etc.)
                // Don't log 404s as they're expected if frames don't exist
                if (!err.message.includes('404') && !err.message.includes('Failed to fetch')) {
                    console.warn(`⚠️ [FRAMES] Error checking talking animation:`, err.message);
                }
            }
            
            // Quick check if thinking animation exists (single HEAD request)
            try {
                const thinkingResponse = await fetch(`${thinkingBaseUrl}frame_00000.png`, { method: 'HEAD' });
            if (thinkingResponse.ok) {
                // Generate frame paths directly (no sequential discovery needed)
                this.thinkingFrames = this.generateFramePaths('talking-orange-thinking-animation', 145);
                console.log(`✅ Generated ${this.thinkingFrames.length} thinking animation frame paths`);
                } else if (thinkingResponse.status !== 404) {
                    // Only log non-404 errors (404 is expected if frames don't exist)
                    console.log(`⚠️ [FRAMES] Thinking animation check failed at ${thinkingBaseUrl}frame_00000.png (status: ${thinkingResponse.status})`);
                }
            } catch (err) {
                // Silently handle fetch errors (network issues, CORS, etc.)
                // Don't log 404s as they're expected if frames don't exist
                if (!err.message.includes('404') && !err.message.includes('Failed to fetch')) {
                    console.warn(`⚠️ [FRAMES] Error checking thinking animation:`, err.message);
                }
            }
            
            // Use frame animations if we have them
            if (this.talkingFrames.length > 0 || this.thinkingFrames.length > 0) {
                this.useFrameAnimations = true;
                console.log('🎬 Using frame-based animations (advanced mode)');
                
                // First: Preload images to browser cache (downloads all files)
                if (this.talkingFrames.length > 0) {
                    console.log('📥 Downloading talking animation images to browser cache...');
                    await this.preloadImagesToCache(this.talkingFrames, 'talking');
                }
                if (this.thinkingFrames.length > 0) {
                    console.log('📥 Downloading thinking animation images to browser cache...');
                    await this.preloadImagesToCache(this.thinkingFrames, 'thinking');
                }
                
                // Then: Preload all textures for instant display (images already in cache)
                if (this.talkingFrames.length > 0) {
                    console.log('🔄 Preloading talking animation textures...');
                    await this.preloadTextures(this.talkingFrames, this.talkingTextures, 'talking');
                }
                if (this.thinkingFrames.length > 0) {
                    console.log('🔄 Preloading thinking animation textures...');
                    await this.preloadTextures(this.thinkingFrames, this.thinkingTextures, 'thinking');
                }
                
                // Advanced animations fully loaded - show wink as confirmation
                console.log('✨ Advanced animations fully loaded!');
                this.showWinkConfirmation();
            } else {
                console.log('🖼️  Using image-based animations (fallback mode)');
            }
        } catch (error) {
            console.log('🖼️  Frame animations not found, using image-based animations');
            this.useFrameAnimations = false;
        }
    }
    
    // Generate frame paths directly (much faster than sequential discovery)
    generateFramePaths(folderName, frameCount) {
        const frames = [];
        // Use user-specific URL if available, otherwise fallback to default
        const baseUrl = this.getVideoBaseUrl(folderName);
        for (let i = 0; i < frameCount; i++) {
            const framePath = `${baseUrl}frame_${String(i).padStart(5, '0')}.png`;
            frames.push(framePath);
        }
        return frames;
    }
    
    getVideoBaseUrl(folderName) {
        // Check if we have video animations from current target (from window or global)
        const target = window.currentTarget || currentTarget;
        if (window.targetVideoAnimations && target) {
            const videoAnim = window.targetVideoAnimations.find(v => v.filename === folderName);
            if (videoAnim && videoAnim.url) {
                // Ensure URL ends with /
                return videoAnim.url.endsWith('/') ? videoAnim.url : videoAnim.url + '/';
            }
        }
        // Try to construct URL from current target if available (project-based)
        if (target && target.userId && target.projectName) {
            return `/api/users/${target.userId}/${target.projectName}/media/videos/${folderName}/`;
        } else if (target && target.userId) {
            // Fallback to old structure if no projectName
            return `/api/users/${target.userId}/media/videos/${folderName}/`;
        }
        // Final fallback to default path (shouldn't happen in normal operation)
        console.warn(`⚠️ [VIDEO] No target context, using fallback path for ${folderName}`);
        return `./media/videos/${folderName}/`;
    }
    
    // Legacy discovery method (kept for fallback if frame count is unknown)
    async discoverFrames(folderName) {
        const frames = [];
        let frameIndex = 0;
        const baseUrl = this.getVideoBaseUrl(folderName);
        
        while (true) {
            const framePath = `${baseUrl}frame_${String(frameIndex).padStart(5, '0')}.png`;
            try {
                // Use HEAD request to check if frame exists without downloading it
                // This avoids downloading full images just to check existence
                const response = await fetch(framePath, { 
                    method: 'HEAD',
                    // Suppress error logging for expected 404s
                    cache: 'no-cache'
                });
                
                if (response.ok) {
                    frames.push(framePath);
                    frameIndex++;
                } else if (response.status === 404) {
                    // Frame doesn't exist - since frames are sequential, we've reached the end
                    break;
                } else {
                    // Other error (e.g., 403, 500) - also stop
                    break;
                }
            } catch (error) {
                // Network error or other issue - stop searching
                // This is expected when we reach the end of the sequence
                break;
            }
        }
        
        return frames;
    }
    
    async preloadImagesToCache(framePaths, animationType) {
        // Preload images to browser cache using Image objects
        // This downloads all files so they're cached when we need them
        const loadPromises = framePaths.map((framePath, index) => {
            return new Promise((resolve) => {
                const img = new Image();
                img.onload = () => {
                    if ((index + 1) % 20 === 0 || index === framePaths.length - 1) {
                        console.log(`   ✅ Cached ${index + 1}/${framePaths.length} ${animationType} images`);
                    }
                    resolve();
                };
                img.onerror = (error) => {
                    console.warn(`⚠️ Failed to cache ${framePath}`);
                    resolve(); // Continue with other images
                };
                img.src = framePath; // Trigger download
            });
        });
        
        await Promise.all(loadPromises);
        console.log(`✅ All ${framePaths.length} ${animationType} images cached in browser!`);
    }
    
    async preloadTextures(framePaths, textureCache, animationType) {
        // Preload all textures in parallel for instant display
        const loader = new THREE.TextureLoader();
        const loadPromises = framePaths.map((framePath, index) => {
            return new Promise((resolve) => {
                loader.load(
                    framePath,
                    (texture) => {
                        texture.colorSpace = THREE.SRGBColorSpace;
                        texture.flipY = true;
                        
                        // Preserve aspect ratio - center the texture and maintain proportions
                        texture.center.set(0.5, 0.5);
                        // Set repeat to 1,1 to avoid tiling
                        texture.repeat.set(1, 1);
                        
                        textureCache[framePath] = texture;
                        if ((index + 1) % 20 === 0 || index === framePaths.length - 1) {
                            console.log(`✅ Preloaded ${index + 1}/${framePaths.length} ${animationType} textures`);
                        }
                        resolve();
                    },
                    undefined,
                    (error) => {
                        console.error(`❌ Error preloading ${framePath}:`, error);
                        resolve(); // Continue loading other frames
                    }
                );
            });
        });
        
        await Promise.all(loadPromises);
        console.log(`✅ All ${framePaths.length} ${animationType} textures preloaded and ready!`);
    }
    
    loadTalkingStates() {
        // Dynamically load all talking images (talking-orange-talking-N.png)
        // They're already in assets, we just need to create state objects
        const states = [];
        let index = 1;
        
        while (true) {
            const imgElement = document.querySelector(`img[id="talking-orange-talking-${index}"]`);
            if (imgElement) {
                states.push({
                    id: `#talking-orange-talking-${index}`,
                    name: `talking-${index}`,
                    src: `./media/talking-orange-talking-${index}.png`
                });
                index++;
            } else {
                break;
            }
        }
        
        console.log(`✅ Loaded ${states.length} talking animation states:`, states.map(s => s.name));
        return states;
    }
    
    setToTalkingState(stateIndex) {
        if (stateIndex < 0 || stateIndex >= this.talkingStates.length) {
            console.error(`❌ Invalid talking state index: ${stateIndex}`);
            return;
        }
        
        const state = this.talkingStates[stateIndex];
        console.log(`🗣️ Setting to talking state: ${state.name}`);
        this.applyTextureFromState(state);
    }
    
    debugImageLoading() {
        console.log('🔍 Debugging image loading...');
        
        // Check idle state
        const idleImg = document.querySelector(`img[id="${this.idleState.id.replace('#', '')}"]`);
        if (idleImg) {
            console.log(`✅ Idle image (${this.idleState.name}):`, {
                id: this.idleState.id,
                src: this.idleState.src,
                loaded: idleImg.complete
            });
        }
    }
    
    setToIdleState() {
        console.log('🎭 Setting to idle state (smile)');
        this.isIdle = true;
        
        // Show image plane
        const imageMesh = this.orangePlane.getObject3D('mesh');
        if (imageMesh) {
            imageMesh.visible = true;
        }
        
        // Force apply smile image using direct texture application (not setAttribute to avoid geometry changes)
        try {
            this.applyTextureFromState(this.idleState);
            // Ensure geometry stays at 1x1 (A-Frame's setAttribute('src') can change geometry)
            this.orangePlane.setAttribute('geometry', { width: 1, height: 1 });
            console.log('✅ Idle state applied (smile image)');
        } catch (error) {
            console.error('❌ Error setting idle state:', error);
            // Last resort: use src but immediately reset geometry
            this.orangePlane.setAttribute('src', this.idleState.id);
            // Force geometry back to 1x1 after src is set
            setTimeout(() => {
                this.orangePlane.setAttribute('geometry', { width: 1, height: 1 });
            }, 10);
        }
    }
    
    applyTextureFromState(state) {
        const img = document.querySelector(`img[id="${state.id.replace('#', '')}"]`);
        if (!img) {
            console.error(`❌ Image not found: ${state.id}`);
            return;
        }
        
        this.recreateMaterial(img);
    }
    
    recreateMaterial(img) {
        try {
            const mesh = this.orangePlane.getObject3D('mesh');
            
            // Wait for mesh to be ready if it doesn't exist yet
            if (!mesh) {
                console.warn('⚠️ Mesh not ready yet, waiting for A-Frame to initialize...');
                // Wait for next frame and try again
                setTimeout(() => {
                    this.recreateMaterial(img);
                }, 100);
                return;
            }
            
            // Keep plane geometry fixed at 1x1 (flat 2D surface)
            // Reset to 1x1 to ensure consistency
            this.orangePlane.setAttribute('geometry', { width: 1, height: 1 });
            
            const texture = new THREE.Texture(img);
            texture.needsUpdate = true;
            texture.colorSpace = THREE.SRGBColorSpace;
            texture.flipY = true;
            
            // Center the texture - always centered regardless of aspect ratio
            texture.center.set(0.5, 0.5);
            texture.repeat.set(1, 1);
            texture.offset.set(0, 0);
            
            // Use MeshBasicMaterial - doesn't respond to lighting (no shading)
            const material = new THREE.MeshBasicMaterial({
                map: texture,
                transparent: true,
                alphaTest: 0.1,
                opacity: 1.0,
                side: THREE.DoubleSide
            });
            
            // Don't dispose materials - just replace them
            // Disposal can interfere with MindAR's internal state
            mesh.material = material;
            
            // Reset frameMaterial reference since we're now using a different material
            // This ensures frame animations create a fresh material
            this.frameMaterial = null;
            
        } catch (error) {
            console.error('❌ Error recreating material:', error);
            // Last resort: use src but immediately reset geometry
            // Use the proper A-Frame asset reference format
            const imgId = img.id || img.getAttribute('id');
            if (imgId) {
                this.orangePlane.setAttribute('src', `#${imgId}`);
            // Force geometry back to 1x1 after src is set (A-Frame might change it)
            setTimeout(() => {
                this.orangePlane.setAttribute('geometry', { width: 1, height: 1 });
            }, 10);
            } else {
                console.error('❌ Cannot set src: image has no ID');
            }
        }
    }
    
    applyTextureFromFrame(framePath) {
        const mesh = this.orangePlane.getObject3D('mesh');
        
        if (!mesh) {
            console.error('❌ Mesh not found in applyTextureFromFrame');
            return;
        }
        
        // Ensure mesh is visible
        mesh.visible = true;
        
        // Check cache first (preloaded textures)
        let texture = null;
        if (this.talkingTextures[framePath]) {
            texture = this.talkingTextures[framePath];
        } else if (this.thinkingTextures[framePath]) {
            texture = this.thinkingTextures[framePath];
        }
        
        if (!texture) {
            console.warn(`⚠️ Frame texture not cached: ${framePath}`);
            return;
        }
        
        // Ensure plane geometry stays fixed at 1x1 (flat 2D surface)
        // Reset to 1x1 to ensure consistency - don't change geometry based on texture
        this.orangePlane.setAttribute('geometry', { width: 1, height: 1 });
        
        // Ensure texture mapping is correct - center and repeat
        texture.center.set(0.5, 0.5);
        texture.repeat.set(1, 1);
        texture.offset.set(0, 0);
        
        // Verify geometry stays at 1x1
        const geometry = mesh.geometry;
        if (geometry && (Math.abs(geometry.parameters.width - 1) > 0.01 || 
                         Math.abs(geometry.parameters.height - 1) > 0.01)) {
            console.warn(`⚠️ Plane geometry changed from 1x1 to ${geometry.parameters.width}x${geometry.parameters.height}, resetting`);
            // Force it back to 1x1
            this.orangePlane.setAttribute('geometry', { width: 1, height: 1 });
        }
        
        // Check if we need to recreate frameMaterial
        // This happens when we switched from image-based (smile) back to frame-based animation
        const needsNewMaterial = !this.frameMaterial || 
                                mesh.material !== this.frameMaterial ||
                                (this.frameMaterial && !this.frameMaterial.map);
        
        if (needsNewMaterial) {
            // Don't dispose materials - just replace them
            // Disposal can interfere with MindAR's internal state
            
            // Create fresh frameMaterial
            this.frameMaterial = new THREE.MeshBasicMaterial({
                map: texture,
                transparent: true,
                alphaTest: 0.1,
                opacity: 1.0,
                side: THREE.DoubleSide
            });
            mesh.material = this.frameMaterial;
        } else {
            // Just update the texture map - much more efficient!
            // All textures are preloaded and cached, so we never dispose them
            this.frameMaterial.map = texture;
            this.frameMaterial.needsUpdate = true;
        }
        
        // Force material update
        mesh.material.needsUpdate = true;
        
        // Ensure mesh is still visible (defensive check)
        if (!mesh.visible) {
            console.warn('⚠️ Mesh became invisible, re-enabling');
            mesh.visible = true;
        }
    }
    
    showWinkConfirmation() {
        // Show wink image briefly to confirm advanced animations are loaded
        // This indicates that test buttons will use frame-based animations, not fallbacks
        console.log('😉 Showing wink - advanced animations are ready!');
        
        // Wait for mesh to be ready before trying to show wink
        const checkMesh = () => {
            const mesh = this.orangePlane.getObject3D('mesh');
            if (!mesh) {
                setTimeout(checkMesh, 100);
                return;
            }
            
        const winkImg = document.querySelector('img[id="talking-orange-wink"]');
            if (winkImg && winkImg.complete) {
            this.recreateMaterial(winkImg);
            // Return to smile after 1 second
            setTimeout(() => {
                const smileImg = document.querySelector('img[id="talking-orange"]');
                    if (smileImg && smileImg.complete) {
                    this.recreateMaterial(smileImg);
                    console.log('😊 Returned to smile after wink confirmation');
                }
            }, 1000);
        } else {
                console.warn('⚠️ Wink image not found or not loaded yet');
        }
        };
        
        // Start checking after a short delay to ensure A-Frame is ready
        setTimeout(checkMesh, 500);
    }
    
    setToThinkingState(stateIndex) {
        if (stateIndex < 0 || stateIndex >= this.thinkingStates.length) {
            console.error(`❌ Invalid thinking state index: ${stateIndex}`);
            return;
        }
        
        const state = this.thinkingStates[stateIndex];
        console.log(`🤔 Setting to thinking state: ${state.name}`);
        this.applyTextureFromState(state);
    }
    
    startTalkingAnimation() {
        // Force stop any existing thinking animation first
        if (this.isThinking) {
            console.log('⚠️ Stopping existing thinking animation before starting talking');
            this.stopThinkingAnimation();
        }
        
        // Clear any stale intervals
        if (this.talkingInterval) {
            clearInterval(this.talkingInterval);
            this.talkingInterval = null;
        }
        
        // Reset state flags
        this.isTalking = true;
        this.isIdle = false;
        this.isThinking = false; // Ensure thinking is false
        
        // Ensure image plane is visible
        const imageMesh = this.orangePlane.getObject3D('mesh');
        if (imageMesh) {
            imageMesh.visible = true;
        }
        
        // Use frame-based animation if available, otherwise fall back to image-based
        if (this.useFrameAnimations && this.talkingFrames.length > 0) {
            console.log(`🎬 Starting frame-based talking animation with ${this.talkingFrames.length} frames`);
            this.currentTalkingFrame = 0;
            
            // Start with first frame
            this.applyTextureFromFrame(this.talkingFrames[this.currentTalkingFrame]);
            
            // Loop forward through frames continuously
            // 145 frames in 6 seconds = ~41.4ms per frame
            const talkingFrameInterval = Math.round(6000 / this.talkingFrames.length);
            console.log(`⏱️  Talking animation: ${this.talkingFrames.length} frames, interval=${talkingFrameInterval}ms, target duration=6s`);
            
            let talkingStartTime = performance.now();
            let talkingFrameCount = 0;
            this.talkingInterval = setInterval(() => {
                // Move to next frame
                this.currentTalkingFrame++;
                
                // Check if we've reached the last frame
                if (this.currentTalkingFrame >= this.talkingFrames.length) {
                    // Check if we're in test mode (should stop after one cycle)
                    if (this.fallbackTestMode) {
                        console.log(`✅ Talking animation completed (reached frame ${this.talkingFrames.length - 1}) - test mode`);
                        this.fallbackTestMode = false;
                        this.stopTalkingAnimation();
                        return;
                    }
                    // Normal operation: loop continuously
                    this.currentTalkingFrame = 0;
                }
                
                talkingFrameCount++;
                
                const elapsed = performance.now() - talkingStartTime;
                const expectedElapsed = talkingFrameCount * talkingFrameInterval;
                const timingDiff = (elapsed - expectedElapsed).toFixed(2);
                
                if (talkingFrameCount % 10 === 0) {
                    console.log(`🗣️ Talking frame ${this.currentTalkingFrame} requested [elapsed: ${elapsed.toFixed(0)}ms, expected: ${expectedElapsed.toFixed(0)}ms, diff: ${timingDiff}ms]`);
                }
                
                this.applyTextureFromFrame(this.talkingFrames[this.currentTalkingFrame]);
            }, talkingFrameInterval); // 6 seconds total for full cycle
        } else {
            // Fallback to image-based animation
            if (this.talkingStates.length === 0) {
                console.error('❌ No talking states available');
                return;
            }
            
            console.log(`🗣️ Starting image-based talking animation with ${this.talkingStates.length} states`);
            this.currentTalkingState = 0;
            this.talkingDirection = 1;
            
            // Start with first talking state
            this.setToTalkingState(this.currentTalkingState);
            
            // Cycle through talking images forward then backward (opening/closing mouth)
            this.talkingInterval = setInterval(() => {
                // Check boundaries before moving
                if (this.currentTalkingState >= this.talkingStates.length - 1 && this.talkingDirection === 1) {
                    this.talkingDirection = -1; // Start closing
                } else if (this.currentTalkingState <= 0 && this.talkingDirection === -1) {
                    // Completed one full cycle (forward + backward)
                    if (this.fallbackTestMode) {
                        console.log('✅ Fallback talking animation completed one cycle');
                        this.fallbackTestMode = false;
                        this.stopTalkingAnimation();
                        return;
                    }
                    // Normal operation: continue looping
                    this.talkingDirection = 1; // Start opening again
                }
                
                // Move to next state based on direction
                this.currentTalkingState += this.talkingDirection;
                this.setToTalkingState(this.currentTalkingState);
            }, 100); // Fast animation for mouth movement
        }
    }
    
    stopTalkingAnimation() {
        if (!this.isTalking) {
            console.log('⚠️ Animation not running');
            // Still reset test mode flag even if not running
            this.fallbackTestMode = false;
            return;
        }
        
        this.isTalking = false;
        console.log('🔇 Stopping talking animation, returning to idle');
        
        // Clear talking interval immediately
        if (this.talkingInterval) {
            clearInterval(this.talkingInterval);
            this.talkingInterval = null;
        }
        
        // Reset frame counters and test mode
        this.currentTalkingFrame = 0;
        this.fallbackTestMode = false;
        
        // Force return to idle state (smile) - clear any pending async texture loads first
        // Set a flag to prevent frame animations from overwriting the idle state
        const restoreIdleState = () => {
            console.log('🔄 Restoring idle state (smile)...');
            // Force apply smile immediately
            const img = document.querySelector(`img[id="${this.idleState.id.replace('#', '')}"]`);
            if (img) {
                this.recreateMaterial(img);
                // Ensure geometry stays 1x1
                this.orangePlane.setAttribute('geometry', { width: 1, height: 1 });
                console.log('✅ Smile image restored via recreateMaterial');
            } else {
                // Fallback: use src but reset geometry immediately
                this.orangePlane.setAttribute('src', this.idleState.id);
                setTimeout(() => {
                    this.orangePlane.setAttribute('geometry', { width: 1, height: 1 });
                }, 10);
                console.log('✅ Smile image restored via setAttribute (geometry reset)');
            }
        this.setToIdleState();
        };
        
        // Small delay to ensure frame animation interval is cleared
        setTimeout(restoreIdleState, 100);
    }
    
    startThinkingAnimation() {
        // Guard: if already running and interval exists, don't start again
        if (this.isThinking && this.thinkingInterval) {
            console.log('⚠️ Thinking animation already running, skipping duplicate start');
            return;
        }
        
        // Force stop any existing talking animation first
        if (this.isTalking) {
            console.log('⚠️ Stopping existing talking animation before starting thinking');
            this.stopTalkingAnimation();
        }
        
        // Clear any stale intervals - CRITICAL to prevent stacking
        if (this.thinkingInterval) {
            console.log('⚠️ Clearing existing thinking interval to prevent stacking');
            clearInterval(this.thinkingInterval);
            this.thinkingInterval = null;
        }
        
        // Reset state flags
        this.isThinking = true;
        this.isIdle = false;
        this.isTalking = false; // Ensure talking is false
        
        // Show image plane
        const imageMesh = this.orangePlane.getObject3D('mesh');
        if (imageMesh) {
            imageMesh.visible = true;
        }
        
        // Use frame-based animation if available, otherwise fall back to image-based
        if (this.useFrameAnimations && this.thinkingFrames.length > 0) {
            console.log(`🎬 Starting frame-based thinking animation with ${this.thinkingFrames.length} frames`);
            this.currentThinkingFrame = 0;
            
            // Start with first frame
            this.applyTextureFromFrame(this.thinkingFrames[this.currentThinkingFrame]);
            
            // Loop forward through frames continuously
            // 145 frames in 3 seconds = ~20.7ms per frame
            const thinkingFrameInterval = Math.round(3000 / this.thinkingFrames.length);
            console.log(`⏱️  Thinking animation: ${this.thinkingFrames.length} frames, interval=${thinkingFrameInterval}ms, target duration=3s`);
            
            // Use closure variables that persist but reset on loop
            let thinkingFrameCount = 0;
            let lastLoopTime = performance.now();
            
            this.thinkingInterval = setInterval(() => {
                // Move to next frame
                this.currentThinkingFrame++;
                thinkingFrameCount++;
                
                // Check if we've reached the last frame
                if (this.currentThinkingFrame >= this.thinkingFrames.length) {
                    // Check if we're in test mode (should stop after one cycle)
                    if (this.fallbackTestMode) {
                        console.log(`✅ Thinking animation completed (reached frame ${this.thinkingFrames.length - 1}) - test mode`);
                        this.fallbackTestMode = false;
                        this.stopThinkingAnimation();
                        return;
                    }
                    // Normal operation: loop continuously - RESET timing to prevent acceleration
                    this.currentThinkingFrame = 0;
                    thinkingFrameCount = 0;
                    lastLoopTime = performance.now();
                    console.log('🔄 Thinking animation looped, reset timing');
                }
                
                // Apply the current frame
                this.applyTextureFromFrame(this.thinkingFrames[this.currentThinkingFrame]);
            }, thinkingFrameInterval);
        } else {
            // Fallback to image-based animation
            console.log('🤔 Starting image-based thinking animation...');
            this.currentThinkingState = 0;
        
        // Cycle through thinking states
        this.thinkingInterval = setInterval(() => {
            this.setToThinkingState(this.currentThinkingState);
                this.currentThinkingState++;
                
                // Check if we've completed one full cycle
                if (this.currentThinkingState >= this.thinkingStates.length) {
                    if (this.fallbackTestMode) {
                        console.log('✅ Fallback thinking animation completed one cycle');
                        this.fallbackTestMode = false;
                        this.stopThinkingAnimation();
                        return;
                    }
                    // Normal operation: loop continuously
                    this.currentThinkingState = 0;
                }
            }, 100); // Fast animation, same speed as talking
        }
    }
    
    stopThinkingAnimation() {
        if (!this.isThinking) {
            console.log('⚠️ No thinking animation running');
            // Still reset test mode flag even if not running
            this.fallbackTestMode = false;
            return;
        }
        
        this.isThinking = false;
        console.log('🛑 Stopping thinking animation, returning to idle');
        
        // Clear thinking interval immediately
        if (this.thinkingInterval) {
            clearInterval(this.thinkingInterval);
            this.thinkingInterval = null;
        }
        
        // Reset frame counters and test mode
        this.currentThinkingFrame = 0;
        this.fallbackTestMode = false;
        
        // Force return to idle state (smile) - clear any pending async texture loads first
        const restoreIdleState = () => {
            console.log('🔄 Restoring idle state (smile)...');
            const img = document.querySelector(`img[id="${this.idleState.id.replace('#', '')}"]`);
            if (img) {
                this.recreateMaterial(img);
                // Ensure geometry stays 1x1
                this.orangePlane.setAttribute('geometry', { width: 1, height: 1 });
                console.log('✅ Smile image restored via recreateMaterial');
            } else {
                // Fallback: use src but reset geometry immediately
                this.orangePlane.setAttribute('src', this.idleState.id);
                setTimeout(() => {
                    this.orangePlane.setAttribute('geometry', { width: 1, height: 1 });
                }, 10);
                console.log('✅ Smile image restored via setAttribute (geometry reset)');
            }
        this.setToIdleState();
        };
        
        // Small delay to ensure frame animation interval is cleared
        setTimeout(restoreIdleState, 100);
        
        console.log('✅ Thinking animation stopped');
    }
    
    getStatus() {
        return {
            isTalking: this.isTalking,
            isThinking: this.isThinking,
            isIdle: this.isIdle,
            currentThinkingState: this.currentThinkingState,
            currentStateName: this.isIdle ? this.idleState.name : 
                            this.isThinking ? this.thinkingStates[this.currentThinkingState].name :
                            'talking-images',
            planeSrc: this.orangePlane.getAttribute('src')
        };
    }
}

// Export to window for global access
if (typeof window !== 'undefined') {
    // Initialize animation module when this script loads
    const orangePlane = document.querySelector('#talking-orange-plane');
    if (orangePlane) {
        window.animationModule = new TalkingAnimationModule(orangePlane);
        console.log('✅ TalkingAnimationModule initialized and exported to window.animationModule');
    } else {
        console.warn('⚠️ Orange plane not found, animation module will be initialized later');
        // Will be initialized when orangePlane is available
        window.animationModule = null;
    }
}
