/**
 * Voice Processing Module for Talking Orange Project
 * 
 * Handles voice recording, STT, TTS, and LLM interaction.
 * This is a project-specific module loaded dynamically after target detection.
 */

// Voice recording and processing system
// Declare variables first to avoid temporal dead zone issues
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let recordingTimer = null;
let recordingStartTime = null;
let currentAudio = null; // Global audio object to track current playback

// Helper functions that reference global animation functions
function startThinkingAnimation() {
    if (window.thinkingController) {
        window.thinkingController.start({ loop: true, playAudio: true });
    } else if (window.animationModule) {
        window.animationModule.startThinkingAnimation();
    } else {
        console.warn('⚠️ Animation module not available');
    }
}

function stopThinkingAnimation() {
    if (window.thinkingController) {
        window.thinkingController.stop();
    } else if (window.animationModule) {
        window.animationModule.stopThinkingAnimation();
    } else {
        console.warn('⚠️ Animation module not available');
    }
}

function startTalkingAnimation() {
    if (window.talkingController) {
        window.talkingController.start({ loop: true, playIntro: false });
    } else if (window.animationModule) {
        window.animationModule.startTalkingAnimation();
    } else {
        console.warn('⚠️ Animation module not available');
    }
}

function stopTalkingAnimation() {
    if (window.talkingController) {
        window.talkingController.stop();
    } else if (window.animationModule) {
        window.animationModule.stopTalkingAnimation();
    } else {
        console.warn('⚠️ Animation module not available');
    }
}

function updateButtonText() {
    // Use project-specific button text update if available
    if (typeof window.updateTalkingOrangeButtonText === 'function') {
        window.updateTalkingOrangeButtonText();
    } else {
        // Fallback to simple text update
        const button = document.getElementById('ask-question-btn');
        if (button) {
            const currentLang = window.currentLanguage || 'en';
            button.textContent = currentLang === 'es' ? 'Hacer Pregunta' : 'Ask Question';
        }
    }
}

// Make askQuestion available on window immediately
window.askQuestion = async function askQuestion() {
    if (isRecording) {
        console.log('Stopping recording...');
        stopRecording();
        return;
    }
    
    try {
        console.log('🎤 Starting voice recording...');
        
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Set up MediaRecorder
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = function(event) {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
                console.log(`📦 Collected audio chunk: ${event.data.size} bytes`);
            }
        };
        
        mediaRecorder.onstop = async function() {
            const recordingDuration = recordingStartTime ? (Date.now() - recordingStartTime) : 0;
            console.log('🔊 [RECORDING STOPPED] Processing audio...', {
                duration: recordingDuration + 'ms (' + (recordingDuration / 1000).toFixed(2) + 's)',
                chunks: audioChunks.length,
                timestamp: new Date().toISOString()
            });
            
            // Check if we actually recorded any audio
            if (audioChunks.length === 0 || audioChunks.every(chunk => chunk.size === 0)) {
                console.error('❌ [RECORDING ERROR] No audio data recorded - microphone may be off or not working');
                stopThinkingAnimation();
                alert('⚠️ No audio recorded. Please check your microphone and try again.');
                return;
            }
            
            const blobStartTime = performance.now();
            // Create audio blob
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            const blobDuration = (performance.now() - blobStartTime).toFixed(0);
            console.log(`📊 [AUDIO BLOB] Created in ${blobDuration}ms`, {
                size: audioBlob.size + ' bytes',
                sizeKB: (audioBlob.size / 1024).toFixed(2) + ' KB',
                chunks: audioChunks.length
            });
            
            // Validate audio blob size
            if (audioBlob.size < 100) {
                console.error('❌ [RECORDING ERROR] Audio blob too small - microphone may not be working');
                stopThinkingAnimation();
                alert('⚠️ Audio recording is too short or empty. Please check your microphone and try again.');
                return;
            }
            
            // Convert to base64
            const base64StartTime = performance.now();
            const reader = new FileReader();
            reader.onloadend = async function() {
                const base64Duration = (performance.now() - base64StartTime).toFixed(0);
                const base64Audio = reader.result.split(',')[1]; // Remove data:audio/webm;base64, prefix
                console.log(`📤 [BASE64 CONVERSION] Completed in ${base64Duration}ms`, {
                    base64Length: base64Audio.length + ' characters',
                    estimatedSize: (base64Audio.length * 3 / 4).toFixed(0) + ' bytes',
                    timestamp: new Date().toISOString()
                });
                
                // Send to backend for processing
                await processVoiceInput(base64Audio);
            };
            reader.onerror = function(error) {
                console.error('❌ [BASE64 ERROR] FileReader error:', error);
            };
            reader.readAsDataURL(audioBlob);
            
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
        };
        
        // Start recording with timeslice to ensure we capture all data
        mediaRecorder.start(1000); // Request data every 1 second
        isRecording = true;
        recordingStartTime = Date.now();
        
        // Show recording indicator
        const button = document.getElementById('ask-question-btn');
        const currentLang = window.currentLanguage || 'en';
        button.textContent = currentLang === 'es' ? 'Detener Grabación (0s)' : 'Stop Recording (0s)';
        button.style.background = '#f44336';
        
        // Update timer every second
        recordingTimer = setInterval(() => {
            if (isRecording) {
                const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
                button.textContent = currentLang === 'es' ? `Detener Grabación (${elapsed}s)` : `Stop Recording (${elapsed}s)`;
                
                // Auto-stop after 1 minute (60 seconds)
                if (elapsed >= 60) {
                    console.log('⏰ Auto-stopping recording after 1 minute');
                    stopRecording();
                }
            }
        }, 1000);
        
    } catch (error) {
        console.error('❌ Error accessing microphone:', error);
        alert('Error accessing microphone. Please check permissions.');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        console.log('🛑 Stopping recording...');
        isRecording = false;
        
        // Clear the timer
        if (recordingTimer) {
            clearInterval(recordingTimer);
            recordingTimer = null;
        }
        
        // Request final data before stopping
        mediaRecorder.requestData();
        
        // Stop the recorder (this will trigger onstop)
        mediaRecorder.stop();
        
        // Reset button
        const button = document.getElementById('ask-question-btn');
        updateButtonText(); // Use the dynamic text function
        button.style.background = '#2196F3';
        
        // Start thinking animation while processing
        console.log('🤔 Starting thinking animation...');
        startThinkingAnimation();
    }
}

async function processVoiceInput(audioData) {
    const requestStartTime = performance.now();
    const requestTimestamp = new Date().toISOString();
    const sessionId = 'web_session_' + Date.now();
    const currentLang = window.currentLanguage || 'en';
    
    // Get user_id and project_name from current target
    const currentTarget = window.currentTarget;
    const userId = currentTarget && currentTarget.userId ? currentTarget.userId : null;
    const projectName = currentTarget && currentTarget.projectName ? currentTarget.projectName : null;
    
    // Log target info for debugging
    console.log('🔍 [VOICE] Current target info:', {
        hasTarget: !!currentTarget,
        userId: userId,
        projectName: projectName,
        targetId: currentTarget ? currentTarget.targetId : null
    });
    
    // Check Whisper device status before processing
    let whisperDevice = 'unknown';
    try {
        const healthResponse = await fetch('/api/health');
        const healthData = await healthResponse.json();
        const deviceInfo = healthData.whisper_device || {};
        whisperDevice = deviceInfo.device || 'unknown';
        const useFp16 = deviceInfo.use_fp16 || false;
        const modelName = deviceInfo.model_name || 'unknown';
        
        if (whisperDevice === 'cuda') {
            console.log(`🚀 [WHISPER DEVICE] GPU (CUDA) - Fast processing expected`, {
                device: whisperDevice,
                fp16: useFp16,
                model: modelName
            });
        } else if (whisperDevice === 'cpu') {
            console.warn(`⚠️ [WHISPER DEVICE] CPU - Processing may be slower`, {
                device: whisperDevice,
                fp16: useFp16,
                model: modelName
            });
        }
    } catch (error) {
        console.warn('⚠️ Could not check Whisper device status:', error);
    }
    
    try {
        console.log('📤 [API REQUEST START] Sending audio to backend...', {
            timestamp: requestTimestamp,
            sessionId: sessionId,
            audioDataLength: audioData.length,
            audioDataSize: (audioData.length * 3 / 4).toFixed(0) + ' bytes (approx)',
            language: currentLang,
            whisperDevice: whisperDevice,
            userId: userId,
            projectName: projectName
        });
        
        const fetchStartTime = performance.now();
        
        // Add timeout to prevent hanging
        const timeoutMs = 120000; // 2 minutes timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            controller.abort();
            console.error('❌ [API TIMEOUT] Request timed out after ' + timeoutMs + 'ms');
        }, timeoutMs);
        
        let response;
        try {
            response = await fetch('/api/speech/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    audioData: audioData,
                    sessionId: sessionId,
                    language: currentLang,
                    ttsVoice: 'default',
                    ttsEngine: 'auto',
                    userId: userId,  // Include actual user_id from current target
                    projectName: projectName  // Include project_name from current target
                }),
                signal: controller.signal
            });
            clearTimeout(timeoutId);
        } catch (fetchError) {
            clearTimeout(timeoutId);
            if (fetchError.name === 'AbortError') {
                throw new Error('Request timed out after ' + timeoutMs + 'ms - backend may be unresponsive');
            }
            throw new Error('Network error: ' + fetchError.message);
        }
        
        const fetchEndTime = performance.now();
        const fetchDuration = (fetchEndTime - fetchStartTime).toFixed(0);
        console.log(`📡 [API FETCH COMPLETE] Response received in ${fetchDuration}ms`, {
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries())
        });
        
        if (!response.ok) {
            let errorMessage = `HTTP error! status: ${response.status}`;
            let errorDetails = null;
            
            // Clone response to read it multiple times if needed
            const responseClone = response.clone();
            
            try {
                // Try to parse as JSON first (Flask returns JSON errors)
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
                errorDetails = errorData;
                console.error('❌ [API ERROR] HTTP error response (JSON):', {
                    status: response.status,
                    statusText: response.statusText,
                    error: errorMessage,
                    details: errorDetails,
                    fetchDuration: fetchDuration + 'ms'
                });
            } catch (jsonError) {
                // If JSON parsing fails, try to get text from clone
                try {
                    const errorText = await responseClone.text();
                    console.error('❌ [API ERROR] HTTP error response (text):', {
                        status: response.status,
                        statusText: response.statusText,
                        body: errorText.substring(0, 500), // First 500 chars
                        fetchDuration: fetchDuration + 'ms'
                    });
                    // Try to extract error message from HTML if it's an HTML error page
                    const errorMatch = errorText.match(/KeyError: '([^']+)'/);
                    if (errorMatch) {
                        errorMessage = `KeyError: Missing key '${errorMatch[1]}' in request data`;
                    } else {
                        errorMessage = errorText.substring(0, 200) || errorMessage;
                    }
                } catch (textError) {
                    console.error('❌ [API ERROR] Could not read error response:', textError);
                }
            }
            
            throw new Error(errorMessage);
        }
        
        const parseStartTime = performance.now();
        const result = await response.json();
        const parseEndTime = performance.now();
        const parseDuration = (parseEndTime - parseStartTime).toFixed(0);
        
        const totalDuration = (performance.now() - requestStartTime).toFixed(0);
        console.log(`✅ [API RESPONSE PARSED] Voice processing complete in ${totalDuration}ms total`, {
            fetchDuration: fetchDuration + 'ms',
            parseDuration: parseDuration + 'ms',
            result: result,
            hasAudioUrl: !!result.audioUrl,
            hasTranscription: !!result.transcription,
            hasResponse: !!result.response
        });
        
        // Log detailed timing breakdown
        console.log('⏱️ [TIMING BREAKDOWN]', {
            totalTime: totalDuration + 'ms',
            fetchTime: fetchDuration + 'ms',
            parseTime: parseDuration + 'ms',
            timestamp: new Date().toISOString()
        });
        
        // Play the audio response
        if (result.audioUrl) {
            const audioStartTime = performance.now();
            console.log('🔊 [AUDIO PLAYBACK START] Starting audio playback...', {
                audioUrl: result.audioUrl,
                timestamp: new Date().toISOString()
            });
            await playAudioResponse(result.audioUrl);
            const audioEndTime = performance.now();
            console.log(`🔊 [AUDIO PLAYBACK INITIATED] Audio playback started in ${(audioEndTime - audioStartTime).toFixed(0)}ms`);
        } else {
            console.warn('⚠️ [AUDIO MISSING] No audioUrl in response');
        }
        
        // Show transcription and response
        console.log('📝 [TRANSCRIPTION]', result.transcription || '(none)');
        console.log('💬 [RESPONSE TEXT]', result.response || '(none)');
        
    } catch (error) {
        const errorDuration = (performance.now() - requestStartTime).toFixed(0);
        console.error('❌ [API ERROR] Voice processing failed after ' + errorDuration + 'ms', {
            error: error,
            errorMessage: error.message,
            errorName: error.name,
            errorStack: error.stack,
            timestamp: new Date().toISOString(),
            sessionId: sessionId
        });
        
        // Stop thinking animation on error
        stopThinkingAnimation();
        alert('Error processing voice input: ' + error.message);
    }
}

async function playAudioResponse(audioUrl) {
    const audioStartTime = performance.now();
    const audioTimestamp = new Date().toISOString();
    
    try {
        console.log('🔊 [AUDIO] Starting audio playback...', {
            audioUrl: audioUrl,
            timestamp: audioTimestamp
        });
        
        // Stop any existing audio first
        if (currentAudio) {
            try {
                currentAudio.pause();
                currentAudio.currentTime = 0;
                console.log('🔄 [AUDIO] Stopped previous audio playback');
            } catch (error) {
                console.warn('⚠️ [AUDIO] Error stopping previous audio:', error);
            }
        }
        
        // Stop thinking animation and start talking animation
        const animStartTime = performance.now();
        stopThinkingAnimation();
        startTalkingAnimation();
        const animDuration = (performance.now() - animStartTime).toFixed(0);
        console.log(`🎭 [ANIMATION] Switched to talking animation in ${animDuration}ms`);
        
        // Show stop button
        const stopBtn = document.getElementById('stop-audio-btn');
        if (stopBtn) {
            stopBtn.style.display = 'block';
        }
        
        const audioLoadStartTime = performance.now();
        
        // Validate audio URL
        if (!audioUrl) {
            throw new Error('Audio URL is empty or undefined');
        }
        
        console.log('🔊 [AUDIO] Creating audio object...', {
            audioUrl: audioUrl,
            urlType: typeof audioUrl
        });
        
        const audio = new Audio(audioUrl);
        audio.volume = 1.0; // Set volume to maximum
        audio.muted = false; // Ensure not muted
        
        console.log('🔊 [AUDIO] Audio object created', {
            volume: audio.volume,
            muted: audio.muted,
            audioUrl: audioUrl
        });
        
        // Store audio globally so we can stop it
        currentAudio = audio;
        
        // Track audio loading with error handling
        audio.addEventListener('loadstart', () => {
            console.log('📥 [AUDIO] Load started', {
                audioUrl: audioUrl,
                timeSinceRequest: (performance.now() - audioLoadStartTime).toFixed(0) + 'ms'
            });
        });
        
        // Track errors during loading
        audio.addEventListener('error', (e) => {
            console.error('❌ [AUDIO] Error loading audio:', {
                error: e,
                code: audio.error?.code,
                message: audio.error?.message,
                audioUrl: audioUrl
            });
            if (audio.error) {
                const errorCodes = {
                    1: 'MEDIA_ERR_ABORTED',
                    2: 'MEDIA_ERR_NETWORK',
                    3: 'MEDIA_ERR_DECODE',
                    4: 'MEDIA_ERR_SRC_NOT_SUPPORTED'
                };
                console.error(`   Error code: ${audio.error.code} (${errorCodes[audio.error.code] || 'UNKNOWN'})`);
            }
        });
        
        audio.addEventListener('loadeddata', () => {
            console.log('✅ [AUDIO] Data loaded', {
                duration: audio.duration ? audio.duration.toFixed(2) + 's' : 'unknown',
                timeSinceRequest: (performance.now() - audioLoadStartTime).toFixed(0) + 'ms'
            });
        });
        
        audio.addEventListener('canplay', () => {
            console.log('▶️ [AUDIO] Can play', {
                timeSinceRequest: (performance.now() - audioLoadStartTime).toFixed(0) + 'ms'
            });
        });
        
        // Stop animation when audio ends
        audio.onended = function() {
            const totalDuration = (performance.now() - audioStartTime).toFixed(0);
            console.log(`✅ [AUDIO] Playback completed in ${totalDuration}ms, stopping talking animation`, {
                timestamp: new Date().toISOString()
            });
            stopTalkingAnimation();
            
            // Clear audio reference and hide stop button
            currentAudio = null;
            const stopBtn = document.getElementById('stop-audio-btn');
            if (stopBtn) {
                stopBtn.style.display = 'none';
            }
        };
        
        // Also handle errors
        audio.onerror = function(e) {
            const errorDuration = (performance.now() - audioStartTime).toFixed(0);
            console.error(`❌ [AUDIO ERROR] Playback error after ${errorDuration}ms`, {
                error: e,
                audioUrl: audioUrl,
                timestamp: new Date().toISOString()
            });
            stopTalkingAnimation();
            
            // Clear audio reference and hide stop button
            currentAudio = null;
            const stopBtn = document.getElementById('stop-audio-btn');
            if (stopBtn) {
                stopBtn.style.display = 'none';
            }
        };
        
        const playStartTime = performance.now();
        await audio.play();
        const playDuration = (performance.now() - playStartTime).toFixed(0);
        console.log(`▶️ [AUDIO] Play started in ${playDuration}ms`, {
            audioUrl: audioUrl,
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        const errorDuration = (performance.now() - audioStartTime).toFixed(0);
        console.error(`❌ [AUDIO ERROR] Playback failed after ${errorDuration}ms`, {
            error: error,
            errorMessage: error.message,
            audioUrl: audioUrl,
            timestamp: new Date().toISOString()
        });
        // Stop animation on error
        stopTalkingAnimation();
        
        // Clear audio reference and hide stop button
        currentAudio = null;
        const stopBtn = document.getElementById('stop-audio-btn');
        if (stopBtn) {
            stopBtn.style.display = 'none';
        }
    }
}

// Export stopAudio function for global access
window.stopAudio = function() {
    console.log('⏹️ [STOP] User requested to stop audio playback');
    
    // Stop current audio if playing
    if (currentAudio) {
        try {
            currentAudio.pause();
            currentAudio.currentTime = 0;
            console.log('✅ [STOP] Audio playback stopped');
        } catch (error) {
            console.warn('⚠️ [STOP] Error stopping audio:', error);
        }
        currentAudio = null;
    }
    
    // Stop talking animation
    stopTalkingAnimation();
    
    // Hide stop button
    const stopBtn = document.getElementById('stop-audio-btn');
    if (stopBtn) {
        stopBtn.style.display = 'none';
    }
    
    console.log('✅ [STOP] All playback stopped, ready for new question');
};

console.log('✅ Voice processing module loaded');
