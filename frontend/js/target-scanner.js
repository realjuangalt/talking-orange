/**
 * Target Scanner Module
 * 
 * Handles Artivive-style target scanning and cycling logic.
 * Efficiently cycles through available targets until one is detected,
 * and resumes scanning when a target is lost.
 */

// Global state for target detection cycling
let targetScannerState = {
    currentTargetIndex: 0,
    detectionTimeout: null,
    targetLocked: false,
    detectionAttempts: 0,
    maxAttemptsPerTarget: 100, // Try each target for ~5 seconds (100 * 50ms) - MindAR needs time to load and detect
    mindarLoading: false,
    loadTimeout: null,
    unhandledRejectionHandler: null,
    isScanning: false,
    lastTargetSwitchTime: 0,
    minSwitchInterval: 3000, // Minimum 3 seconds between target switches (efficiency + MindAR load time)
    consecutiveLosses: 0, // Track consecutive target losses to optimize scanning
    lastLockedTarget: null // Remember which target was locked for resume logic
};

/**
 * Initialize the target scanner
 */
function initTargetScanner() {
    targetScannerState.isScanning = false;
    targetScannerState.targetLocked = false;
    targetScannerState.currentTargetIndex = 0;
    targetScannerState.detectionAttempts = 0;
    targetScannerState.consecutiveLosses = 0;
    targetScannerState.lastLockedTarget = null;
    
    // Clear any existing timeouts
    if (targetScannerState.detectionTimeout) {
        clearTimeout(targetScannerState.detectionTimeout);
        targetScannerState.detectionTimeout = null;
    }
    
    console.log('🎯 [SCANNER] Target scanner initialized');
}

/**
 * Lock onto a detected target (stop scanning)
 * @param {Object} target - The target object that was detected
 */
function lockTarget(target) {
    if (!target) {
        console.warn('⚠️ [SCANNER] lockTarget called without target');
        return;
    }
    
    targetScannerState.targetLocked = true;
    targetScannerState.lastLockedTarget = target;
    targetScannerState.consecutiveLosses = 0; // Reset loss counter on successful lock
    
    // Clear any pending detection timeout
    if (targetScannerState.detectionTimeout) {
        clearTimeout(targetScannerState.detectionTimeout);
        targetScannerState.detectionTimeout = null;
    }
    
    // Stop scanning
    targetScannerState.isScanning = false;
    
    console.log(`🔒 [SCANNER] Locked onto target: ${target.targetId}`);
}

/**
 * Unlock target and resume scanning
 * Called when a target is lost
 */
function unlockTarget() {
    if (!targetScannerState.targetLocked) {
        return; // Already unlocked
    }
    
    targetScannerState.targetLocked = false;
    targetScannerState.consecutiveLosses++;
    targetScannerState.detectionAttempts = 0; // Reset attempts for fresh scan
    
    console.log(`🔓 [SCANNER] Target unlocked, resuming scan (consecutive losses: ${targetScannerState.consecutiveLosses})`);
    
    // Resume scanning after a brief delay (let MindAR stabilize)
    setTimeout(() => {
        if (!targetScannerState.targetLocked) {
            startScanning();
        }
    }, 500); // 500ms delay before resuming
}

/**
 * Try the next target in the cycle
 */
function tryNextTarget() {
    if (!window.allAvailableTargets || window.allAvailableTargets.length === 0) {
        console.warn('⚠️ [SCANNER] No targets available for detection');
        return;
    }
    
    if (targetScannerState.targetLocked) {
        console.log('🔒 [SCANNER] Target already locked, not switching');
        return;
    }
    
    // Efficiency check: Don't switch too frequently
    const now = Date.now();
    const timeSinceLastSwitch = now - targetScannerState.lastTargetSwitchTime;
    if (timeSinceLastSwitch < targetScannerState.minSwitchInterval) {
        // Too soon to switch, wait a bit
        const waitTime = targetScannerState.minSwitchInterval - timeSinceLastSwitch;
        console.log(`⏳ [SCANNER] Waiting ${waitTime}ms before next switch (efficiency optimization)`);
        setTimeout(() => {
            if (!targetScannerState.targetLocked) {
                tryNextTarget();
            }
        }, waitTime);
        return;
    }
    
    const targets = window.allAvailableTargets;
    const scene = document.querySelector('#ar-scene');
    
    if (!scene) {
        console.error('❌ [SCANNER] Scene element not found');
        return;
    }
    
    // Move to next target
    targetScannerState.currentTargetIndex = (targetScannerState.currentTargetIndex + 1) % targets.length;
    const target = targets[targetScannerState.currentTargetIndex];
    
    targetScannerState.lastTargetSwitchTime = now;
    
    console.log(`🔄 [SCANNER] Trying target ${targetScannerState.currentTargetIndex + 1}/${targets.length}: ${target.targetId}`);
    
    // Update current target globally
    window.currentTarget = target;
    window.currentTargetMedia = target.media || [];
    
    // Switch MindAR to this target
    const targetUrl = target.url;
    console.log(`🎯 [SCANNER] Switching MindAR to: ${targetUrl}`);
    
    // Mark that we're loading a new target
    targetScannerState.mindarLoading = true;
    
    // Set up error handlers
    setupTargetErrorHandlers(scene, target);
    
    // Set up load timeout
    setupLoadTimeout(scene, target);
    
    // Switch the MindAR target
    switchMindARTarget(scene, targetUrl, target);
}

/**
 * Set up error handlers for target loading
 */
function setupTargetErrorHandlers(scene, target) {
    // MindAR error handler
    const mindarErrorHandler = (event) => {
        console.error(`❌ [SCANNER] MindAR error loading ${target.targetId}:`, event.detail || event);
        targetScannerState.mindarLoading = false;
        console.log(`⏭️ [SCANNER] Skipping corrupted target, trying next...`);
        targetScannerState.detectionAttempts = targetScannerState.maxAttemptsPerTarget; // Force skip
    };
    
    // MindAR loaded handler
    const mindarLoadedHandler = () => {
        console.log(`✅ [SCANNER] MindAR finished loading ${target.targetId}`);
        targetScannerState.mindarLoading = false;
        if (targetScannerState.loadTimeout) {
            clearTimeout(targetScannerState.loadTimeout);
            targetScannerState.loadTimeout = null;
        }
    };
    
    // Listen for MindAR events
    scene.addEventListener('mindar-error', mindarErrorHandler, { once: true });
    scene.addEventListener('mindar-loaded', mindarLoadedHandler, { once: true });
    
    // Unhandled promise rejection handler (for corrupted .mind files)
    const unhandledRejectionHandler = (event) => {
        const error = event.reason || event;
        const errorMessage = error?.message || error?.toString() || '';
        const errorName = error?.name || '';
        
        // Check for MindAR decode errors
        if (errorName === 'RangeError' || errorMessage.includes('Extra') || 
            errorMessage.includes('buffer') || errorMessage.includes('byte')) {
            console.error(`❌ [SCANNER] MindAR decode error (corrupted .mind file) for ${target.targetId}:`, errorMessage);
            targetScannerState.mindarLoading = false;
            console.log(`⏭️ [SCANNER] Skipping corrupted target immediately, trying next...`);
            targetScannerState.detectionAttempts = targetScannerState.maxAttemptsPerTarget;
            event.preventDefault();
            
            // Immediately try next target
            setTimeout(() => {
                if (!targetScannerState.targetLocked) {
                    tryNextTarget();
                }
            }, 100);
            return;
        }
    };
    
    // Remove existing handler if any
    if (targetScannerState.unhandledRejectionHandler) {
        window.removeEventListener('unhandledrejection', targetScannerState.unhandledRejectionHandler);
    }
    targetScannerState.unhandledRejectionHandler = unhandledRejectionHandler;
    window.addEventListener('unhandledrejection', unhandledRejectionHandler, { once: true });
}

/**
 * Set up load timeout to detect failed loads
 */
function setupLoadTimeout(scene, target) {
    if (targetScannerState.loadTimeout) {
        clearTimeout(targetScannerState.loadTimeout);
    }
    
    targetScannerState.loadTimeout = setTimeout(() => {
        if (targetScannerState.mindarLoading) {
            // Check if MindAR system has an error state
            const mindarSystem = scene.systems && scene.systems['mindar-image-system'];
            const sceneEl = scene;
            
            // Check for error indicators
            const hasError = (mindarSystem && mindarSystem.el && mindarSystem.el.classList.contains('mindar-ui-error')) ||
                            (sceneEl && sceneEl.classList.contains('mindar-ui-error')) ||
                            (document.querySelector('.mindar-ui-error') !== null);
            
            if (hasError) {
                console.error(`❌ [SCANNER] MindAR failed to load ${target.targetId} (detected error state)`);
                targetScannerState.mindarLoading = false;
                targetScannerState.detectionAttempts = targetScannerState.maxAttemptsPerTarget;
                // Try next target
                setTimeout(() => {
                    if (!targetScannerState.targetLocked) {
                        tryNextTarget();
                    }
                }, 100);
            } else {
                console.log(`⏱️ [SCANNER] MindAR load timeout for ${target.targetId}, assuming loaded`);
                targetScannerState.mindarLoading = false;
            }
        }
    }, 3000); // 3 second timeout
}

/**
 * Switch MindAR to a new target with minimal video interruption
 * 
 * MindAR doesn't support hot-swapping targets, so we need to remove/re-add the component.
 * However, we can preserve the video stream by:
 * 1. Getting a reference to the video element and its stream before removing
 * 2. Removing the attribute (this will stop MindAR but video element may persist)
 * 3. Re-adding the attribute quickly
 * 4. The video should restart automatically, but we can help it along
 */
function switchMindARTarget(scene, targetUrl, target) {
    try {
        const mindarSystem = scene.systems && scene.systems['mindar-image-system'];
        const currentTargetSrc = mindarSystem ? mindarSystem.imageTargetSrc : null;
        
        // Check if we're actually switching to a different target
        if (currentTargetSrc === targetUrl) {
            console.log('✅ [SCANNER] Target already set, skipping switch');
            targetScannerState.mindarLoading = false;
            return;
        }
        
        // If we already have MindAR running, we need to reload the target
        // Unfortunately, MindAR requires removing/re-adding the component to switch targets
        // We'll do it as quickly as possible to minimize interruption
        if (mindarSystem && scene.hasAttribute('mindar-image') && currentTargetSrc) {
            console.log('🔄 [SCANNER] Switching target (minimizing video interruption)...');
            console.log(`   Current: ${currentTargetSrc}`);
            console.log(`   New: ${targetUrl}`);
            
            // Ensure scene stays playing (critical for video continuity)
            if (scene && !scene.isPlaying) {
                scene.play();
            }
            
            // Remove attribute to force MindAR to reload
            // This will stop MindAR temporarily, but we'll restart it immediately
            scene.removeAttribute('mindar-image');
            
            // Re-add with new target after a brief delay to allow MindAR cleanup
            // MindAR will automatically restart the video when component is re-added
            setTimeout(() => {
                // Re-add with new target - this will trigger MindAR to load the new .mind file
                scene.setAttribute('mindar-image', `imageTargetSrc: ${targetUrl}; maxTrack: 1; missTolerance: 80; warmupTolerance: 8; filterMinCF: 0.00001; filterBeta: 10000; uiLoading: yes; uiScanning: no; uiError: yes;`);
                
                // Verify the switch worked by checking the system after a brief delay
                setTimeout(() => {
                    const newMindarSystem = scene.systems && scene.systems['mindar-image-system'];
                    if (newMindarSystem) {
                        const newTargetSrc = newMindarSystem.imageTargetSrc;
                        if (newTargetSrc === targetUrl) {
                            console.log(`✅ [SCANNER] Target switch verified: ${newTargetSrc}`);
                        } else {
                            console.warn(`⚠️ [SCANNER] Target switch verification failed - expected ${targetUrl}, got ${newTargetSrc}`);
                        }
                    }
                }, 100);
                
                // Ensure scene is still playing after re-adding
                if (scene && !scene.isPlaying) {
                    scene.play();
                }
                
                // Reload media for this target
                if (typeof window.loadTargetMedia === 'function') {
                    const assets = document.querySelector('#ar-assets');
                    const orangePlane = document.querySelector('#talking-orange-plane');
                    if (assets && orangePlane) {
                        window.loadTargetMedia(assets, orangePlane);
                    }
                }
            }, 100); // Small delay to allow MindAR cleanup - balance between speed and reliability
        } else {
            // First time setup or no existing system - set up normally
            console.log('🆕 [SCANNER] Setting up MindAR (first time or no existing system)...');
            setMindARTarget(scene, targetUrl, target);
        }
    } catch (error) {
        console.error(`❌ [SCANNER] Error switching to target ${target.targetId}:`, error);
        targetScannerState.mindarLoading = false;
        targetScannerState.detectionAttempts = targetScannerState.maxAttemptsPerTarget;
        
        // If it's a RangeError (corrupted file), skip immediately
        if (error.name === 'RangeError' || error.message?.includes('Extra') || error.message?.includes('buffer')) {
            console.log(`⏭️ [SCANNER] Corrupted file detected, skipping immediately...`);
            setTimeout(() => {
                if (!targetScannerState.targetLocked) {
                    tryNextTarget();
                }
            }, 100);
        }
    }
}

/**
 * Set the MindAR target attribute (initial setup only)
 */
function setMindARTarget(scene, targetUrl, target) {
    scene.setAttribute('mindar-image', `imageTargetSrc: ${targetUrl}; maxTrack: 1; missTolerance: 80; warmupTolerance: 8; filterMinCF: 0.00001; filterBeta: 10000; uiLoading: yes; uiScanning: no; uiError: yes;`);
    
    // Reload media for this target (if loadTargetMedia function is available)
    if (typeof window.loadTargetMedia === 'function') {
        const assets = document.querySelector('#ar-assets');
        const orangePlane = document.querySelector('#talking-orange-plane');
        if (assets && orangePlane) {
            window.loadTargetMedia(assets, orangePlane);
        }
    }
}

/**
 * Start scanning through targets
 */
function startScanning() {
    if (targetScannerState.targetLocked) {
        console.log('🔒 [SCANNER] Target locked, not starting scan');
        return;
    }
    
    if (targetScannerState.isScanning) {
        console.log('🔄 [SCANNER] Already scanning');
        return;
    }
    
    targetScannerState.isScanning = true;
    console.log('🔄 [SCANNER] Starting target scan cycle...');
    
    // Start the detection cycle
    startDetectionCycle();
}

/**
 * Stop scanning (but don't unlock target)
 */
function stopScanning() {
    targetScannerState.isScanning = false;
    if (targetScannerState.detectionTimeout) {
        clearTimeout(targetScannerState.detectionTimeout);
        targetScannerState.detectionTimeout = null;
    }
    console.log('⏸️ [SCANNER] Scanning stopped');
}

/**
 * Start the detection cycle (internal function)
 */
function startDetectionCycle() {
    if (targetScannerState.targetLocked) {
        stopScanning();
        return;
    }
    
    // Don't advance if MindAR is still loading
    if (targetScannerState.mindarLoading) {
        // Check again soon
        targetScannerState.detectionTimeout = setTimeout(() => {
            startDetectionCycle();
        }, 100); // Check every 100ms while loading
        return;
    }
    
    targetScannerState.detectionAttempts++;
    
    // If we've tried this target long enough, move to next
    if (targetScannerState.detectionAttempts >= targetScannerState.maxAttemptsPerTarget) {
        tryNextTarget();
        targetScannerState.detectionAttempts = 0; // Reset for new target
    }
    
    // Continue cycling (only if not locked and still scanning)
    if (!targetScannerState.targetLocked && targetScannerState.isScanning) {
        targetScannerState.detectionTimeout = setTimeout(() => {
            startDetectionCycle();
        }, 50); // Check every 50ms (efficient polling)
    }
}

/**
 * Get current scanner state (for debugging)
 */
function getScannerState() {
    return {
        ...targetScannerState,
        allTargetsCount: window.allAvailableTargets ? window.allAvailableTargets.length : 0,
        currentTarget: window.currentTarget ? window.currentTarget.targetId : null
    };
}

// Export to window
window.targetScanner = {
    init: initTargetScanner,
    lockTarget: lockTarget,
    unlockTarget: unlockTarget,
    startScanning: startScanning,
    stopScanning: stopScanning,
    tryNextTarget: tryNextTarget,
    getState: getScannerState
};

console.log('✅ [SCANNER] Target scanner module loaded');
