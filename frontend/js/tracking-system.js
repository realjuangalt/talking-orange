/**
 * Tracking System Module
 * 
 * Handles AR target tracking, position/rotation smoothing, and stability management.
 * Core AR tracking functionality.
 */

/**
 * Setup tracking system for AR marker
 * 
 * @param {HTMLElement} marker - The AR marker entity
 * @param {HTMLElement} orangePlane - The orange plane entity (or any tracked entity)
 */
function setupTrackingSystem(marker, orangePlane) {
    if (!marker) {
        console.error('❌ [TRACKING] Marker element not found');
        return;
    }
    
    // Enhanced smoothing with frame averaging and dead zone filtering
    // Much more aggressive smoothing to eliminate wobble
    let smoothingFactor = 0.05; // Very aggressive smoothing (lower = more stable, less jitter)
    let rotationSmoothing = 0.04; // Extremely aggressive rotation smoothing
    
    // Frame averaging buffers for smoother tracking
    const BUFFER_SIZE = 3; // Average over last 3 frames
    let positionBuffer = [];
    let rotationBuffer = [];
    
    // Dead zone filtering - ignore tiny movements (likely autofocus wobble)
    const POSITION_DEAD_ZONE = 0.0005; // Ignore movements smaller than this (in meters)
    const ROTATION_DEAD_ZONE = 0.1; // Ignore rotations smaller than this (in degrees)
    
    // Velocity-based filtering - filter out sudden high-velocity changes
    let lastVelocity = { x: 0, y: 0, z: 0 };
    let lastRotationVelocity = { x: 0, y: 0, z: 0 };
    const MAX_VELOCITY = 0.01; // Maximum allowed velocity per frame (m/frame)
    const MAX_ROTATION_VELOCITY = 2.0; // Maximum allowed rotation velocity (deg/frame)
    
    let trackingStability = 0; // Track how stable tracking is (0-1)
    let consecutiveFrames = 0; // Count consecutive successful tracking frames
    
    // Hysteresis: Keep entity visible for longer time after target lost for better stability
    let targetLostTimeout = null;
    let isTargetVisible = false;
    const TARGET_LOST_DELAY = 1500; // Keep visible for 1.5s after losing target (much longer for stability)
    const MIN_STABLE_FRAMES = 3; // Lower threshold - consider stable after just 3 frames
    
    // Position tracking for debugging
    let positionLogCount = 0;
    let rotationLogCount = 0;
    let lastLoggedPosition = null;
    let lastLoggedRotation = null;
    let positionDeltas = [];
    let rotationDeltas = [];
    const LOG_INTERVAL = 30; // Log every 30 frames
    const MAX_DELTA_HISTORY = 100; // Keep last 100 deltas for analysis
    
    // Tracking loss detection
    let lastPositionUpdateTime = 0;
    let lastRotationUpdateTime = 0;
    let trackingLossEvents = [];
    let lastTargetLostTime = 0;
    const POSITION_UPDATE_TIMEOUT = 200; // If no position update for 200ms, consider tracking lost
    const ROTATION_UPDATE_TIMEOUT = 200; // If no rotation update for 200ms, consider tracking lost
    
    // Position and rotation state
    let lastPosition = { x: 0, y: 0, z: 0 };
    let lastRotation = { x: 0, y: 0, z: 0 };
    
    console.log('🎯 [TRACKING] Setting up tracking event listeners...');
    console.log('🎯 [TRACKING] Marker element:', marker);
    console.log('🎯 [TRACKING] Current target at setup:', window.currentTarget);
    
    // Track if we've loaded the project UI and modules (only load once)
    let projectUILoaded = false;
    let projectModulesLoaded = false;
    
    // Log target structure immediately to debug
    if (window.currentTarget) {
        console.log('🔍 [TRACKING] Target structure at setup:', {
            userId: window.currentTarget.userId,
            projectName: window.currentTarget.projectName,
            targetId: window.currentTarget.targetId,
            hasUserId: !!window.currentTarget.userId,
            hasProjectName: !!window.currentTarget.projectName
        });
    } else {
        console.warn('⚠️ [TRACKING] No currentTarget available at setup time');
    }
    
    marker.addEventListener('targetFound', function() {
        console.log('✅ [TRACKING] Target FOUND - Marker detected!');
        console.log('✅ [TRACKING] consecutiveFrames:', consecutiveFrames);
        consecutiveFrames++;
        
        // Get current target from global (prefer window.currentTarget from ar-core.js)
        const currentTarget = window.currentTarget;
        console.log('🔍 [TRACKING] currentTarget in targetFound:', currentTarget);

        // Lock onto this target (Artivive-style: stop cycling, we found a match)
        if (window.targetScanner && typeof window.targetScanner.lockTarget === 'function') {
            window.targetScanner.lockTarget(currentTarget);
        } else if (typeof window.lockTarget === 'function') {
            // Fallback to old method
            window.lockTarget(currentTarget);
        }
        
        // Load project-specific UI and modules on first detection (only once)
        if (consecutiveFrames === 1 && currentTarget) {
            // Debug: Log target structure
            console.log('🔍 [TRACKING] Current target:', {
                userId: currentTarget.userId,
                projectName: currentTarget.projectName,
                targetId: currentTarget.targetId
            });
            
            // Check if we have userId and projectName (required for loading project UI)
            if (currentTarget.userId && currentTarget.projectName) {
                // Load project UI
                if (!projectUILoaded && typeof window.loadProjectUI === 'function') {
                    console.log(`📦 Loading project UI for ${currentTarget.userId}/${currentTarget.projectName}...`);
                    window.loadProjectUI(currentTarget.userId, currentTarget.projectName).then(() => {
                        projectUILoaded = true;
                        console.log('✅ Project UI loaded successfully');
                    }).catch(err => {
                        console.error('❌ Failed to load project UI:', err);
                    });
                } else if (!projectUILoaded) {
                    console.warn('⚠️ loadProjectUI function not available - UI may not load');
                }
                
                // Load project-specific modules (animation, controllers, voice processing)
                if (!projectModulesLoaded && typeof window.loadProjectModules === 'function') {
                    console.log(`📦 Loading project modules for ${currentTarget.userId}/${currentTarget.projectName}...`);
                    window.loadProjectModules(currentTarget.userId, currentTarget.projectName).then(() => {
                        projectModulesLoaded = true;
                        console.log('✅ Project modules loaded successfully');
                    }).catch(err => {
                        console.error('❌ Failed to load project modules:', err);
                    });
                } else if (!projectModulesLoaded) {
                    console.warn('⚠️ loadProjectModules function not available - modules may not load');
                }
            } else {
                console.warn('⚠️ [TRACKING] Target missing userId or projectName:', {
                    hasUserId: !!currentTarget.userId,
                    hasProjectName: !!currentTarget.projectName,
                    target: currentTarget
                });
            }
        } else if (consecutiveFrames === 1 && !currentTarget) {
            console.warn('⚠️ [TRACKING] Target detected but currentTarget is null/undefined');
            console.warn('⚠️ [TRACKING] window.currentTarget:', window.currentTarget);
        }
        
        // Fallback: If we have a target but UI hasn't loaded after a delay, try loading it
        // This handles cases where targetFound fires but the condition wasn't met
        if (consecutiveFrames === 1 && window.currentTarget && window.currentTarget.userId && window.currentTarget.projectName) {
            setTimeout(() => {
                if (!projectUILoaded && typeof window.loadProjectUI === 'function') {
                    console.log('🔄 [TRACKING] Fallback: Loading project UI after delay...');
                    window.loadProjectUI(window.currentTarget.userId, window.currentTarget.projectName).then(() => {
                        projectUILoaded = true;
                        console.log('✅ Project UI loaded successfully (fallback)');
                    }).catch(err => {
                        console.error('❌ Failed to load project UI (fallback):', err);
                    });
                }
                
                if (!projectModulesLoaded && typeof window.loadProjectModules === 'function') {
                    console.log('🔄 [TRACKING] Fallback: Loading project modules after delay...');
                    window.loadProjectModules(window.currentTarget.userId, window.currentTarget.projectName).then(() => {
                        projectModulesLoaded = true;
                        console.log('✅ Project modules loaded successfully (fallback)');
                    }).catch(err => {
                        console.error('❌ Failed to load project modules (fallback):', err);
                    });
                }
            }, 2000); // Wait 2 seconds after first detection
        }
        
        // Log first detection and milestones
        if (consecutiveFrames === 1) {
            console.log('🎯 MARKER DETECTED!');
        }
        
        // Increase smoothing as tracking becomes more stable
        if (consecutiveFrames > MIN_STABLE_FRAMES) {
            trackingStability = Math.min(1.0, trackingStability + 0.1);
            // Keep very aggressive smoothing even when stable to eliminate wobble
            // Only slightly reduce smoothing for minimal responsiveness
            smoothingFactor = Math.max(0.04, 0.06 - (trackingStability * 0.01));
            rotationSmoothing = Math.max(0.03, 0.05 - (trackingStability * 0.01));
        }
        
        // Less verbose logging - only log every 60 frames or milestones
        if (consecutiveFrames % 60 === 0 || consecutiveFrames === MIN_STABLE_FRAMES + 1) {
            console.log(`🎯 Tracking stable (${consecutiveFrames} frames, ${(trackingStability * 100).toFixed(0)}% stable)`);
        }
        
        isTargetVisible = true;
        
        // Clear any pending hide timeout
        if (targetLostTimeout) {
            clearTimeout(targetLostTimeout);
            targetLostTimeout = null;
        }
        
        // Ensure all child entities are visible
        const markerMesh = marker.getObject3D('mesh');
        if (markerMesh) {
            markerMesh.visible = true;
            markerMesh.traverse((child) => {
                if (child.isMesh) {
                    child.visible = true;
                }
            });
        }
        
        // Also ensure orange plane is visible
        if (orangePlane) {
            const orangePlaneMesh = orangePlane.getObject3D('mesh');
            if (orangePlaneMesh) {
                orangePlaneMesh.visible = true;
            }
        }
        
        // Show project UI when target is found (if it's been loaded)
        const projectUIContainer = document.getElementById('project-ui-container');
        if (projectUIContainer && projectUIContainer.innerHTML.trim() !== '') {
            projectUIContainer.style.display = 'block';
            console.log('👁️ Showing project UI (target found)');
        }
    });
    
    marker.addEventListener('targetLost', function() {
        console.log('❌ [TRACKING] Target LOST - Marker no longer detected!');
        
        // Unlock target and resume scanning (Artivive-style: resume when target removed)
        if (window.targetScanner && typeof window.targetScanner.unlockTarget === 'function') {
            window.targetScanner.unlockTarget();
        }
        
        // Hide project UI when target is lost (but don't remove it, just hide)
        const projectUIContainer = document.getElementById('project-ui-container');
        if (projectUIContainer && projectUIContainer.innerHTML.trim() !== '') {
            projectUIContainer.style.display = 'none';
            console.log('👁️ Hiding project UI (target lost)');
        }
        
        const now = performance.now();
        const timeSinceLastLoss = now - lastTargetLostTime;
        lastTargetLostTime = now;
        
        // Don't reset stability immediately - decay it slowly for better continuity
        // Only reset if we never got stable
        if (consecutiveFrames < MIN_STABLE_FRAMES) {
            trackingStability = Math.max(0, trackingStability - 0.2);
        } else {
            // Decay stability slowly on loss - keep some memory of stability
            trackingStability = Math.max(0, trackingStability - 0.05);
        }
        const lostFrames = consecutiveFrames;
        const wasStable = lostFrames >= MIN_STABLE_FRAMES;
        consecutiveFrames = 0;
        
        // Log ALL tracking losses with detailed information
        const lossInfo = {
            frames: lostFrames,
            wasStable: wasStable,
            stability: (trackingStability * 100).toFixed(1) + '%',
            timeSinceLastLoss: timeSinceLastLoss > 0 ? timeSinceLastLoss.toFixed(0) + 'ms' : 'first loss',
            visibilityDelay: TARGET_LOST_DELAY + 'ms',
            timestamp: new Date().toISOString()
        };
        
        // Always log tracking loss - use different log levels based on significance
        if (lostFrames === 0) {
            console.warn('❌❌❌ TRACKING LOST (0 frames - immediate loss)', lossInfo);
        } else if (lostFrames < MIN_STABLE_FRAMES) {
            console.warn(`❌ TRACKING LOST (${lostFrames} frames - unstable)`, lossInfo);
        } else if (lostFrames < 10) {
            console.warn(`⚠️ TRACKING LOST (${lostFrames} frames - brief stable)`, lossInfo);
        } else {
            console.log(`⚠️ Target lost (${lostFrames} frames - was stable)`, lossInfo);
        }
        
        // Track loss events for analysis
        if (trackingLossEvents.length >= 50) {
            trackingLossEvents.shift();
        }
        trackingLossEvents.push({
            ...lossInfo,
            time: now
        });
        
        // Schedule hide after delay (hysteresis) - longer delay for stability
        if (targetLostTimeout) {
            clearTimeout(targetLostTimeout);
            console.log('⏸️ Cancelled previous hide timeout, rescheduling...');
        }
        
        console.log(`⏳ Scheduling hide in ${TARGET_LOST_DELAY}ms if target not found...`);
        targetLostTimeout = setTimeout(() => {
            if (!isTargetVisible) {
                const markerMesh = marker.getObject3D('mesh');
                const orangePlaneMesh = orangePlane ? orangePlane.getObject3D('mesh') : null;
                const actuallyHidden = markerMesh && !markerMesh.visible;
                
                console.log('👋 Hiding entity after tracking loss timeout', {
                    markerVisible: markerMesh ? markerMesh.visible : 'no mesh',
                    orangePlaneVisible: orangePlaneMesh ? orangePlaneMesh.visible : 'no mesh',
                    wasAlreadyHidden: actuallyHidden,
                    timeSinceLoss: (performance.now() - now).toFixed(0) + 'ms'
                });
                
                if (markerMesh) {
                    markerMesh.visible = false;
                }
                if (orangePlaneMesh) {
                    orangePlaneMesh.visible = false;
                }
            } else {
                console.log('✅ Target found again before hide timeout - keeping visible');
            }
        }, TARGET_LOST_DELAY);
        
        isTargetVisible = false;
    });
    
    // Add smoothing to marker position and rotation
    // Simple direct smoothing: smoothly interpolate from last position to current position
    marker.addEventListener('componentchanged', function(event) {
        const now = performance.now();
        
        if (event.detail.name === 'position') {
            // Check if we had a gap in position updates (potential tracking loss)
            if (lastPositionUpdateTime > 0 && (now - lastPositionUpdateTime) > POSITION_UPDATE_TIMEOUT) {
                const gap = now - lastPositionUpdateTime;
                console.warn(`⚠️ Position update gap detected: ${gap.toFixed(0)}ms (possible tracking loss)`);
            }
            
            lastPositionUpdateTime = now;
            
            const currentPos = marker.getAttribute('position');
            if (currentPos) {
                const current = {
                    x: parseFloat(currentPos.x),
                    y: parseFloat(currentPos.y),
                    z: parseFloat(currentPos.z)
                };
                
                // Initialize lastPosition on first update
                if (lastPosition.x === 0 && lastPosition.y === 0 && lastPosition.z === 0) {
                    lastPosition = { ...current };
                    lastLoggedPosition = { ...current };
                    console.log('📍 Position tracking initialized:', current);
                }
                
                // Calculate raw delta (how much the raw position changed)
                const rawDelta = {
                    x: current.x - (lastLoggedPosition ? lastLoggedPosition.x : current.x),
                    y: current.y - (lastLoggedPosition ? lastLoggedPosition.y : current.y),
                    z: current.z - (lastLoggedPosition ? lastLoggedPosition.z : current.z)
                };
                const rawDeltaMagnitude = Math.sqrt(rawDelta.x**2 + rawDelta.y**2 + rawDelta.z**2);
                
                // Calculate velocity (change per frame)
                const velocity = {
                    x: current.x - lastPosition.x,
                    y: current.y - lastPosition.y,
                    z: current.z - lastPosition.z
                };
                const velocityMagnitude = Math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2);
                
                // Velocity-based filtering: reject sudden high-velocity changes (likely noise)
                let filteredCurrent = { ...current };
                if (velocityMagnitude > MAX_VELOCITY) {
                    // Clamp velocity to maximum allowed
                    const scale = MAX_VELOCITY / velocityMagnitude;
                    filteredCurrent = {
                        x: lastPosition.x + velocity.x * scale,
                        y: lastPosition.y + velocity.y * scale,
                        z: lastPosition.z + velocity.z * scale
                    };
                }
                
                // Dead zone filtering: ignore tiny movements
                const delta = {
                    x: filteredCurrent.x - lastPosition.x,
                    y: filteredCurrent.y - lastPosition.y,
                    z: filteredCurrent.z - lastPosition.z
                };
                const deltaMagnitude = Math.sqrt(delta.x**2 + delta.y**2 + delta.z**2);
                
                if (deltaMagnitude < POSITION_DEAD_ZONE) {
                    // Movement too small, ignore it
                    return;
                }
                
                // Apply smoothing: interpolate between last position and current position
                const smoothed = {
                    x: lastPosition.x + delta.x * smoothingFactor,
                    y: lastPosition.y + delta.y * smoothingFactor,
                    z: lastPosition.z + delta.z * smoothingFactor
                };
                
                // Update marker position with smoothed value
                marker.setAttribute('position', `${smoothed.x} ${smoothed.y} ${smoothed.z}`);
                
                // Update last position
                lastPosition = smoothed;
                lastVelocity = velocity;
                
                // Logging (every LOG_INTERVAL frames)
                positionLogCount++;
                if (positionLogCount >= LOG_INTERVAL) {
                    positionLogCount = 0;
                    lastLoggedPosition = { ...smoothed };
                    
                    // Track deltas for analysis
                    positionDeltas.push(deltaMagnitude);
                    if (positionDeltas.length > MAX_DELTA_HISTORY) {
                        positionDeltas.shift();
                    }
                }
            }
        } else if (event.detail.name === 'rotation') {
            // Check if we had a gap in rotation updates (potential tracking loss)
            if (lastRotationUpdateTime > 0 && (now - lastRotationUpdateTime) > ROTATION_UPDATE_TIMEOUT) {
                const gap = now - lastRotationUpdateTime;
                console.warn(`⚠️ Rotation update gap detected: ${gap.toFixed(0)}ms (possible tracking loss)`);
            }
            
            lastRotationUpdateTime = now;
            
            const currentRot = marker.getAttribute('rotation');
            if (currentRot) {
                const current = {
                    x: parseFloat(currentRot.x),
                    y: parseFloat(currentRot.y),
                    z: parseFloat(currentRot.z)
                };
                
                // Initialize lastRotation on first update
                if (lastRotation.x === 0 && lastRotation.y === 0 && lastRotation.z === 0) {
                    lastRotation = { ...current };
                    lastLoggedRotation = { ...current };
                    console.log('🔄 Rotation tracking initialized:', current);
                }
                
                // Calculate rotation velocity
                const rotationVelocity = {
                    x: current.x - lastRotation.x,
                    y: current.y - lastRotation.y,
                    z: current.z - lastRotation.z
                };
                
                // Normalize rotation differences (handle 360-degree wrap)
                const normalizeAngle = (angle) => {
                    while (angle > 180) angle -= 360;
                    while (angle < -180) angle += 360;
                    return angle;
                };
                
                rotationVelocity.x = normalizeAngle(rotationVelocity.x);
                rotationVelocity.y = normalizeAngle(rotationVelocity.y);
                rotationVelocity.z = normalizeAngle(rotationVelocity.z);
                
                const rotationVelocityMagnitude = Math.sqrt(rotationVelocity.x**2 + rotationVelocity.y**2 + rotationVelocity.z**2);
                
                // Velocity-based filtering: reject sudden high-velocity rotations
                let filteredCurrent = { ...current };
                if (rotationVelocityMagnitude > MAX_ROTATION_VELOCITY) {
                    const scale = MAX_ROTATION_VELOCITY / rotationVelocityMagnitude;
                    filteredCurrent = {
                        x: normalizeAngle(lastRotation.x + rotationVelocity.x * scale),
                        y: normalizeAngle(lastRotation.y + rotationVelocity.y * scale),
                        z: normalizeAngle(lastRotation.z + rotationVelocity.z * scale)
                    };
                }
                
                // Dead zone filtering: ignore tiny rotations
                const rotationDelta = {
                    x: normalizeAngle(filteredCurrent.x - lastRotation.x),
                    y: normalizeAngle(filteredCurrent.y - lastRotation.y),
                    z: normalizeAngle(filteredCurrent.z - lastRotation.z)
                };
                const rotationDeltaMagnitude = Math.sqrt(rotationDelta.x**2 + rotationDelta.y**2 + rotationDelta.z**2);
                
                if (rotationDeltaMagnitude < ROTATION_DEAD_ZONE) {
                    // Rotation too small, ignore it
                    return;
                }
                
                // Apply smoothing: interpolate between last rotation and current rotation
                const smoothed = {
                    x: normalizeAngle(lastRotation.x + rotationDelta.x * rotationSmoothing),
                    y: normalizeAngle(lastRotation.y + rotationDelta.y * rotationSmoothing),
                    z: normalizeAngle(lastRotation.z + rotationDelta.z * rotationSmoothing)
                };
                
                // Update marker rotation with smoothed value
                marker.setAttribute('rotation', `${smoothed.x} ${smoothed.y} ${smoothed.z}`);
                
                // Update last rotation
                lastRotation = smoothed;
                lastRotationVelocity = rotationVelocity;
                
                // Logging (every LOG_INTERVAL frames)
                rotationLogCount++;
                if (rotationLogCount >= LOG_INTERVAL) {
                    rotationLogCount = 0;
                    lastLoggedRotation = { ...smoothed };
                    
                    // Track deltas for analysis
                    rotationDeltas.push(rotationDeltaMagnitude);
                    if (rotationDeltas.length > MAX_DELTA_HISTORY) {
                        rotationDeltas.shift();
                    }
                }
            }
        }
    });
    
    console.log('✅ [TRACKING] Tracking system initialized');
}

// Helper function to get current target (from ar-core.js)
function getCurrentTarget() {
    return window.currentTarget || null;
}

// Export function globally
if (typeof window !== 'undefined') {
    window.setupTrackingSystem = setupTrackingSystem;
    console.log('✅ [TRACKING] setupTrackingSystem exported to window');
}

