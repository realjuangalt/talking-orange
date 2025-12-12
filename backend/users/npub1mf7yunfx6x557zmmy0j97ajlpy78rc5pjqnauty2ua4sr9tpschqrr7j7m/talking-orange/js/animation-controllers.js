/**
 * Animation Controllers for Talking Orange Project
 * 
 * Manages animation controllers for thinking and talking animations.
 * This is a project-specific module loaded dynamically after target detection.
 */

class ThinkingAnimationController {
    constructor(animationModule, audioUrl) {
        this.animationModule = animationModule;
        this.audioUrl = audioUrl;
        this.audio = null;
        this.isPlaying = false;
        this.loopMode = false; // false = single play, true = loop continuously
        this.lastAnimationFrame = -1; // Track animation frame to detect loops
        this.frameCheckInterval = null; // Interval to check for animation loops
    }
    
    // Start thinking animation
    start(options = {}) {
        const { loop = false, playAudio = true } = options;
        this.loopMode = loop;
        
        console.log(`🤔 Starting thinking animation (loop: ${loop}, audio: ${playAudio})`);
        
        // Set test mode based on loop mode
        this.animationModule.fallbackTestMode = !loop;
        
        // Initialize frame tracking
        this.lastAnimationFrame = -1;
        
        // Start frame monitoring immediately if in loop mode with audio
        // This will detect when animation loops and restart audio accordingly
        if (loop && playAudio) {
            this.startFrameMonitoring();
        }
        
        // Start visual animation immediately
        this.animationModule.startThinkingAnimation();
        
        // Start audio if requested (with 1 second delay)
        if (playAudio) {
            setTimeout(() => {
                this.playAudioOnce(); // Play once per cycle
                // Initialize frame tracking after audio starts
                this.lastAnimationFrame = this.animationModule.currentThinkingFrame || 0;
            }, 1000); // 1 second delay
        }
    }
    
    // Monitor animation frames to detect when animation loops (resets to 0)
    startFrameMonitoring() {
        // Clear existing interval
        if (this.frameCheckInterval) {
            clearInterval(this.frameCheckInterval);
        }
        
        console.log('👁️ Starting frame monitoring to detect animation loops');
        
        // Check every 50ms for frame resets (indicates animation looped)
        this.frameCheckInterval = setInterval(() => {
            if (!this.animationModule.isThinking) {
                // Animation stopped, stop monitoring
                this.stopFrameMonitoring();
                return;
            }
            
            const currentFrame = this.animationModule.currentThinkingFrame || 0;
            
            // Only check for loop if we have a valid last frame
            if (this.lastAnimationFrame >= 0) {
                // Detect when animation loops: frame goes from near end (>= 140) back to start (0-10)
                // This indicates the animation completed one cycle and restarted
                if (currentFrame <= 10 && this.lastAnimationFrame >= 140 && this.loopMode && !this.isPlaying) {
                    console.log(`🔄 Animation looped detected (frame ${this.lastAnimationFrame} -> ${currentFrame}), restarting audio`);
                    this.playAudioOnce();
                }
            }
            
            // Update last frame tracker (only update if we're progressing forward or looping)
            if (currentFrame > this.lastAnimationFrame || (currentFrame <= 10 && this.lastAnimationFrame >= 140)) {
                this.lastAnimationFrame = currentFrame;
            }
        }, 50); // Check more frequently for better detection
    }
    
    // Stop frame monitoring
    stopFrameMonitoring() {
        if (this.frameCheckInterval) {
            clearInterval(this.frameCheckInterval);
            this.frameCheckInterval = null;
        }
    }
    
    // Stop thinking animation
    stop() {
        console.log('🛑 Stopping thinking animation and audio...');
        
        // Clear frame check interval
        if (this.frameCheckInterval) {
            clearInterval(this.frameCheckInterval);
            this.frameCheckInterval = null;
        }
        
        this.animationModule.stopThinkingAnimation();
        this.stopAudio();
        this.lastAnimationFrame = -1;
    }
    
    // Play audio once (not looping forever)
    playAudioOnce() {
        // Stop existing audio if any
        if (this.audio) {
            try {
                this.audio.pause();
                this.audio.currentTime = 0;
                this.audio = null;
            } catch (e) {
                console.warn('⚠️ Error stopping existing audio:', e);
            }
        }
        
        if (!this.audioUrl) {
            console.warn('⚠️ No thinking audio URL configured');
            return;
        }
        
        console.log('🎵 Starting thinking audio (one play per animation cycle)...', {
            audioUrl: this.audioUrl,
            timestamp: new Date().toISOString()
        });
        
        try {
            this.audio = new Audio(this.audioUrl);
            this.audio.loop = false; // Don't loop forever
            this.audio.volume = 1.0; // Set volume to maximum
            this.audio.muted = false; // Ensure not muted
            
            console.log('🔊 [AUDIO] Audio object created', {
                volume: this.audio.volume,
                muted: this.audio.muted,
                audioUrl: this.audioUrl
            });
            
            // Log when audio is loaded
            this.audio.onloadeddata = () => {
                console.log('✅ Thinking audio data loaded', {
                    duration: this.audio.duration ? this.audio.duration.toFixed(2) + 's' : 'unknown',
                    volume: this.audio.volume,
                    muted: this.audio.muted
                });
            };
            
            // Log when audio can play
            this.audio.oncanplay = () => {
                console.log('✅ Thinking audio can play');
            };
            
            // When audio ends, just mark it as done - don't restart automatically
            this.audio.onended = () => {
                console.log('🔚 Thinking audio finished playing');
                this.audio = null;
                this.isPlaying = false;
                // Don't restart here - wait for animation loop detection
            };
            
            // Log when audio starts
            this.audio.onplay = () => {
                console.log('▶️ Thinking audio started playing');
                this.isPlaying = true;
            };
            
            // Handle errors with more detail
            this.audio.onerror = (e) => {
                console.error('❌ Thinking audio error:', {
                    error: e,
                    code: this.audio?.error?.code,
                    message: this.audio?.error?.message,
                    audioUrl: this.audioUrl
                });
                if (this.audio?.error) {
                    const errorCodes = {
                        1: 'MEDIA_ERR_ABORTED',
                        2: 'MEDIA_ERR_NETWORK',
                        3: 'MEDIA_ERR_DECODE',
                        4: 'MEDIA_ERR_SRC_NOT_SUPPORTED'
                    };
                    console.error(`   Error code: ${this.audio.error.code} (${errorCodes[this.audio.error.code] || 'UNKNOWN'})`);
                }
                this.audio = null;
                this.isPlaying = false;
            };
            
            // Start playing
            const playPromise = this.audio.play();
            if (playPromise !== undefined) {
                playPromise
                    .then(() => {
                        console.log('✅ Thinking audio playback started successfully');
                    })
                    .catch(err => {
                        console.error('❌ Failed to play thinking audio:', {
                            error: err,
                            name: err.name,
                            message: err.message,
                            audioUrl: this.audioUrl
                        });
                        if (err.name === 'NotAllowedError') {
                            console.warn('   Autoplay was blocked by browser. User interaction required.');
                        } else if (err.name === 'NotSupportedError') {
                            console.warn('   Audio format not supported by browser.');
                        }
                        this.audio = null;
                        this.isPlaying = false;
                    });
            } else {
                console.warn('⚠️ Audio.play() returned undefined - browser may not support promises');
            }
        } catch (error) {
            console.error('❌ Error creating audio object:', {
                error: error,
                audioUrl: this.audioUrl
            });
            this.audio = null;
            this.isPlaying = false;
        }
    }
    
    // Check if animation has looped (frame reset to 0) and restart audio if needed
    checkAnimationLoop() {
        if (!this.loopMode || !this.animationModule.isThinking) {
            return;
        }
        
        const currentFrame = this.animationModule.currentThinkingFrame;
        
        // Detect animation loop: frame went from last frame (or near end) back to 0
        // or frame is 0 and we were tracking a higher frame before
        if (currentFrame === 0 && this.lastAnimationFrame > 100) {
            // Animation looped! Restart audio
            console.log('🔄 Animation looped, restarting thinking audio');
            this.playAudioOnce();
        }
        
        // Update last frame tracker
        this.lastAnimationFrame = currentFrame;
    }
    
    // Stop audio
    stopAudio() {
        if (this.audio) {
            console.log('🔇 Stopping thinking audio...');
            this.audio.pause();
            this.audio.currentTime = 0;
            this.audio = null;
            this.isPlaying = false;
            console.log('✅ Thinking audio stopped');
        }
    }
}

class TalkingAnimationController {
    constructor(animationModule, introAudioUrl = null) {
        this.animationModule = animationModule;
        this.introAudioUrl = introAudioUrl;
        this.introAudio = null;
    }
    
    // Start talking animation
    start(options = {}) {
        const { loop = false, playIntro = false } = options;
        // Set test mode to stop after one cycle if not looping
        this.animationModule.fallbackTestMode = !loop;
        
        console.log(`🗣️ Starting talking animation (loop: ${loop}, intro: ${playIntro})`);
        
        // If intro audio is requested, play it first then start animation
        if (playIntro && this.introAudioUrl) {
            this.playIntroAudio();
        } else {
            // Start visual animation immediately
            this.animationModule.startTalkingAnimation();
        }
    }
    
    // Play intro audio
    playIntroAudio() {
        if (!this.introAudioUrl) {
            console.warn('⚠️ No intro audio URL configured');
            // Fallback to starting animation without intro
            this.animationModule.startTalkingAnimation();
            return;
        }
        
        console.log('🎵 Playing intro audio...');
        
        // Stop any existing intro audio
        if (this.introAudio) {
            this.introAudio.pause();
            this.introAudio = null;
        }
        
        this.introAudio = new Audio(this.introAudioUrl);
        this.introAudio.volume = 1.0; // Set volume to maximum
        this.introAudio.muted = false; // Ensure not muted
        
        console.log('🔊 [INTRO AUDIO] Audio object created', {
            volume: this.introAudio.volume,
            muted: this.introAudio.muted,
            audioUrl: this.introAudioUrl
        });
        
        // When intro audio starts, start the animation
        this.introAudio.onplay = () => {
            console.log('▶️ Intro audio started, starting talking animation');
            this.animationModule.startTalkingAnimation();
        };
        
        // When intro audio ends, animation continues
        this.introAudio.onended = () => {
            console.log('🔚 Intro audio finished');
            this.introAudio = null;
        };
        
        // Handle errors
        this.introAudio.onerror = (e) => {
            console.warn('⚠️ Intro audio error:', e);
            this.introAudio = null;
            // Fallback to starting animation without intro
            this.animationModule.startTalkingAnimation();
        };
        
        // Start playing
        const playPromise = this.introAudio.play();
        if (playPromise !== undefined) {
            playPromise
                .then(() => {
                    console.log('✅ Intro audio playback started');
                })
                .catch(err => {
                    console.warn('⚠️ Failed to play intro audio:', err);
                    this.introAudio = null;
                    // Fallback to starting animation without intro
                    this.animationModule.startTalkingAnimation();
                });
        }
    }
    
    // Stop talking animation
    stop() {
        console.log('🛑 Stopping talking animation...');
        
        // Stop intro audio if playing
        if (this.introAudio) {
            this.introAudio.pause();
            this.introAudio.currentTime = 0;
            this.introAudio = null;
        }
        
        this.animationModule.stopTalkingAnimation();
    }
}

// Export to window for global access
if (typeof window !== 'undefined') {
    // Initialize controllers when this script loads (after animation-module.js)
    if (window.animationModule) {
        // Get audio URLs helper function (from ar-core.js or global scope)
        const getAudioUrl = window.getAudioUrl || function(filename) {
            const target = window.currentTarget;
            if (target && target.userId && target.projectName) {
                if (filename.includes('thinking')) {
                    return `/api/users/${target.userId}/${target.projectName}/media/videos/talking-orange-thinking-animation/thinking-hmm.mp3`;
                } else if (filename.includes('intro-es')) {
                    return `/api/users/${target.userId}/${target.projectName}/media/videos/talking-orange-talking-animation/talking-intro-es.mp3`;
                } else if (filename.includes('intro') || filename.includes('talking')) {
                    return `/api/users/${target.userId}/${target.projectName}/media/videos/talking-orange-talking-animation/talking-intro.mp3`;
                }
            }
            return null;
        };
        
        const currentLang = window.currentLanguage || 'en';
        window.thinkingController = new ThinkingAnimationController(
            window.animationModule,
            getAudioUrl('thinking-hmm.mp3')
        );
        window.talkingController = new TalkingAnimationController(
            window.animationModule,
            currentLang === 'es' 
                ? getAudioUrl('talking-intro-es.mp3')
                : getAudioUrl('talking-intro.mp3')
        );
        
        console.log('✅ Animation controllers initialized and exported to window');
    } else {
        console.warn('⚠️ Animation module not found, controllers will be initialized later');
    }
}
