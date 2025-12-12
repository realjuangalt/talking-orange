# Talking Orange - Bitcoin AR Experience

An augmented reality application that brings a 3D talking orange character to life through marker-based AR and voice interaction, designed for Bitcoin education and evangelism.

## 🎯 Project Overview

This project creates an AR experience where users:
1. Point their camera at a printed talking orange marker (credit card-sized)
2. See a 3D talking orange character projected onto the marker
3. Interact with the character through voice commands about Bitcoin
4. Receive audio responses with synchronized mouth animations
5. Can stop audio playback at any time with the stop button

## 🛠️ Technology Stack

### Frontend
- **HTML5, CSS3, Vanilla JavaScript** - Web Standards
- **MindAR** - Modern marker-based AR framework (MIT License)
- **A-Frame** - Web framework for VR/AR (MIT License)
- **Three.js** - 3D rendering (MIT License)
- **Nostr Tools** - Nostr authentication and key management
- **MediaRecorder API** - Audio recording
- **Web Audio API** - Audio playback

### Backend
- **Python 3.8+** - Runtime environment
- **Flask** - Web framework (BSD License)
- **Whisper** - OpenAI's speech-to-text (MIT License)
- **Venice AI API** - LLM for Bitcoin responses
- **Text-to-Speech** - Multiple TTS engines (espeak, festival, pico2wave, Venice AI)

### AR Assets
- **Custom PNG Images** - Talking orange character with animation frames
- **MindAR Targets** - Compiled `.mind` files for marker detection
- **Frame Animations** - 145 frames for talking and thinking animations

## ✅ Current Features

### AR System
- ✅ **Marker Detection** - MindAR successfully detects credit card-sized markers
- ✅ **Image Projection** - Talking orange character projects onto marker
- ✅ **Tracking Stability** - Optimized for 1-2 feet viewing distance
- ✅ **Smoothing & Hysteresis** - Reduces wobble and maintains visibility during brief losses
- ✅ **Comprehensive Logging** - Detailed tracking, position, and rotation logs

### Voice System
- ✅ **Speech-to-Text** - Whisper integration (supports small/medium models)
- ✅ **GPU/CPU Support** - Auto-detects GPU, falls back to CPU automatically
- ✅ **GPU Memory Management** - Handles CUDA out-of-memory gracefully
- ✅ **Model Management** - Automatic model downloading to `backend/models/`
- ✅ **LLM Integration** - Venice AI for Bitcoin evangelism responses
- ✅ **Text-to-Speech** - Multiple TTS engines (espeak, festival, pico2wave) with fallback
- ✅ **Audio Playback** - MP3 audio responses with volume control and stop button
- ✅ **Error Handling** - Comprehensive error logging and user-friendly messages

### Animation System
- ✅ **Talking Animation** - 145-frame animation synchronized with audio
- ✅ **Thinking Animation** - 145-frame animation for processing state
- ✅ **Idle State** - Smile/wink states when not active
- ✅ **Frame-based Animations** - Advanced mode with texture preloading
- ✅ **Image-based Fallback** - Simple mode if frames not available

### UI Features
- ✅ **Ask Question Button** - Voice recording with visual feedback
- ✅ **Stop Button** - Interrupt audio playback (appears during speech)
- ✅ **Language Toggle** - English/Spanish support
- ✅ **Test Buttons** - Manual animation testing
- ✅ **Mobile Responsive** - Touch-friendly controls
- ✅ **Burger Menu** - Navigation and authentication

### Authentication & User Management
- ✅ **Nostr Authentication** - Secure login with Nostr private keys (nsec)
- ✅ **Key Generation** - Create new Nostr key pairs
- ✅ **Key Import** - Import existing Nostr keys
- ✅ **Secure Cookies** - httpOnly cookies for session management
- ✅ **Multi-User Support** - User-specific project directories
- ✅ **Project Management** - Create and manage multiple AR projects per user

### Debugging & Monitoring
- ✅ **Frontend Logging** - 168+ console.log statements for debugging
- ✅ **Backend Logging** - Comprehensive server-side logs
- ✅ **Tracking Debug Tools** - `window.trackingDebug` API for console
- ✅ **Animation Debug** - `window.animationModule` access
- ✅ **Health Check API** - `/api/health` for system status

## 📁 Project Structure

```
talking-orange/
├── frontend/
│   ├── index.html              # Main AR application
│   ├── user.html               # User project management page
│   ├── lib/                     # Pre-bundled libraries
│   │   ├── aframe.min.js
│   │   ├── mindar-image-aframe.prod.js
│   │   └── nostr-tools.min.js  # Nostr authentication library
│   ├── js/                      # Core JavaScript modules
│   │   ├── ar-core.js          # AR initialization and core functions
│   │   ├── camera-video.js     # Camera diagnostics
│   │   ├── tracking-system.js  # AR tracking event handlers
│   │   ├── ui-helpers.js       # UI helper functions
│   │   └── nostr-auth.js       # Nostr authentication module
│   └── media/
│       ├── targets.mind         # MindAR marker file
│       ├── talking-orange-*.png # Character images
│       └── videos/
│           ├── talking-orange-talking-animation/  # 145 frames + audio
│           └── talking-orange-thinking-animation/ # 145 frames + audio
├── backend/
│   ├── app.py                   # Flask server with API endpoints
│   ├── user_manager.py          # User and project management
│   ├── gen/                     # Voice processing modules
│   │   ├── main.py             # Main voice system
│   │   ├── voice_to_text.py    # Whisper STT
│   │   ├── text_to_voice.py    # TTS engines
│   │   └── text_generator.py   # LLM integration
│   ├── users/                   # User-specific data (created on demand)
│   │   └── {user_id}/          # User directory (npub)
│   │       └── {project_name}/ # Project directory
│   │           ├── media/      # Project media files
│   │           ├── ai/         # AI audio responses
│   │           ├── user-input/ # User audio inputs
│   │           ├── js/         # Project-specific JS modules
│   │           └── ui.html     # Project-specific UI
│   ├── models/                  # Whisper models (small.pt, medium.pt)
│   └── voices/                  # TTS voice files
├── start.sh                     # Production server script
├── start_local.sh               # Development server with options
├── start_backend.py              # Python startup script
├── install.sh                   # Installation script
├── requirements-python.txt      # Python dependencies
├── NOSTR_AUTHENTICATION_PLAN.md # Nostr auth implementation plan
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- **Linux** (Debian or Ubuntu - tested on both)
- **Python 3.8+**
- **FFmpeg** (for audio processing)
- **TTS engines** (espeak, festival, pico2wave - installed by install.sh)
- **Modern web browser** with camera/microphone support
- **HTTPS or localhost** (required for camera access)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/realjuangalt/talking-orange.git
   cd talking-orange
   ```

2. **Run installation script**
   ```bash
   chmod +x install.sh
   # If you have sudo:
   sudo ./install.sh
   # Or if you use su (switch to root first):
   su -
   ./install.sh
   # Or if already root:
   ./install.sh
   ```

   This will:
   - Install system dependencies (FFmpeg, TTS engines: espeak, festival, pico2wave)
   - Create Python virtual environment
   - Install Python packages
   - Download AR libraries
   - Create necessary directories
   - Set up `backend/models/` directory
   - Verify TTS engines are installed

   **Important:** The install script installs TTS engines (`espeak`, `festival`, `libttspico-utils`). If you see "No TTS engines available" errors, make sure you ran the full install script.

3. **Configure environment** (optional)
   ```bash
   cp env.example .env
   # Edit .env with your API keys and settings
   ```

### Running the Server

#### Development Mode (Recommended)
```bash
./start_local.sh [--device cpu|gpu] [--model small|medium]
```

**Options:**
- `--device cpu|gpu` - Force CPU or GPU mode (default: cpu)
- `--model small|medium` - Whisper model size (default: small)

**Examples:**
```bash
# Default: CPU mode, small model
./start_local.sh

# GPU mode with medium model
./start_local.sh --device gpu --model medium

# CPU mode with small model (faster startup)
./start_local.sh --device cpu --model small
```

**Features:**
- ✅ Enables Flask debug mode (`DEBUG=true`)
- ✅ Detailed logging
- ✅ Auto-reload on code changes
- ✅ Model auto-download if missing

#### Production Mode (Legacy)
```bash
./start.sh
```

**Note:** Production mode runs with `DEBUG=false` by default. Set `DEBUG=true` in `.env` for debug mode.

### Accessing the Application

1. **Open browser** to `http://localhost:3000`
2. **Login with Nostr** - Click the burger menu (☰) → "Login"
   - **Create New Account**: Generates a new Nostr key pair (save your nsec!)
   - **Import Existing Key**: Enter your existing nsec to login
3. **Grant permissions** for camera and microphone
4. **Create a Project** (optional) - Go to "User Home" to create and manage projects
5. **Print the marker** from your project's target image
6. **Point camera** at the marker (1-2 feet away)
7. **Click "Ask Question"** to start voice interaction

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Server Configuration
PORT=3000
DEBUG=true                    # Enable Flask debug mode

# Whisper Configuration
WHISPER_MODEL_NAME=small      # small or medium
WHISPER_FORCE_CPU=true        # Force CPU mode (true/false) - REQUIRED for CPU-only servers

# TTS Configuration
# TTS engines (espeak, festival, pico2wave) are CPU-based and don't need special config
# They are automatically detected and used in priority order

# Model Directory
MODEL_DIR=./backend/models    # Where Whisper models are stored

# API Keys (if using external services)
VENICE_KEY=your_key_here
```

### Whisper Models

**Model Sizes:**
- `small` - ~462MB, faster, good accuracy
- `medium` - ~1.5GB, slower, better accuracy

**Model Location:**
- Models are stored in `backend/models/`
- Automatically downloaded on first use
- Can be manually downloaded from [HuggingFace](https://huggingface.co/openai/whisper-medium)

### MindAR Configuration

AR tracking parameters in `frontend/index.html`:
```html
<a-scene mindar-image="
  imageTargetSrc: ./media/targets.mind;
  maxTrack: 1;
  missTolerance: 60;        # Frames before considering lost
  warmupTolerance: 5;       # Frames before first detection
  filterMinCF: 0.00005;     # Kalman filter minimum
  filterBeta: 5000;         # Kalman filter beta
  ...">
```

**Optimized for:**
- Credit card-sized markers
- 1-2 feet viewing distance
- Stable tracking with reduced wobble

## 🐛 Debugging

### Frontend Console

Open browser DevTools (F12) → Console tab. You'll see:
- 🍊 `[INIT]` - Application startup logs
- 🎯 `[TRACKING]` - AR marker detection events
- 📍 `[POSITION]` - Position tracking data
- 🔄 `[ROTATION]` - Rotation tracking data
- 🔊 `[AUDIO]` - Audio playback events
- ⏱️ `[TIMER]` - Uptime counter (every 10 seconds)

### Debug Tools

**In Browser Console:**
```javascript
// Get tracking statistics
window.trackingDebug.getStats()

// Get marker position
window.trackingDebug.getPosition()

// Get marker rotation
window.trackingDebug.getRotation()

// Clear tracking history
window.trackingDebug.clearHistory()

// Access animation module
window.animationModule.getStatus()

// Test animations
window.testTalkingAnimation()
window.testThinkingAnimation()
```

### Backend Logging

**Server logs show:**
- 🎤 Voice system initialization
- 🔍 Model loading (CPU/GPU, model name)
- 📊 API request/response times
- ⚠️ Errors and warnings

**Enable debug mode:**
```bash
export DEBUG=true
./start_local.sh
```

### Health Check

Check system status:
```bash
curl http://localhost:3000/api/health
```

Returns:
```json
{
  "status": "healthy",
  "whisper_device": {
    "device": "cpu",
    "use_fp16": false,
    "model_name": "small"
  },
  "voice_system": {
    "initialized": true
  }
}
```

## 📊 API Endpoints

### Authentication
- `POST /api/auth/nostr/login` - Login with Nostr private key (nsec)
- `GET /api/auth/nostr/status` - Check authentication status
- `POST /api/auth/nostr/logout` - Logout and clear session

### Voice Processing
- `POST /api/speech/process` - Full voice-to-voice pipeline
- `POST /api/speech/transcribe` - Speech-to-text only
- `POST /api/speech/synthesize` - Text-to-speech only

### User & Project Management
- `GET /api/users/<user_id>/projects` - List all projects for a user
- `POST /api/users/<user_id>/projects` - Create a new project
- `GET /api/users/<user_id>/<project_name>/files` - List files in a project
- `POST /api/users/upload` - Upload target image or media (requires projectName)
- `DELETE /api/users/<user_id>/<project_name>/media/<filename>` - Delete a file

### AR Targets
- `GET /api/targets` - Get all available AR targets from all users/projects
- `GET /api/users/<user_id>/<project_name>/media/<filename>` - Serve project media
- `GET /api/users/<user_id>/<project_name>/ui` - Serve project-specific UI
- `GET /api/users/<user_id>/<project_name>/js/<filename>` - Serve project JS modules

### System
- `GET /api/health` - System health and status
- `GET /api/voices` - Available TTS voices

### Static Files
- `GET /` - Main application
- `GET /<filename>` - Static assets from `frontend/`

## 🎨 AR Marker

**Marker File:** `frontend/media/targets.mind`

**Print Instructions:**
1. Print `frontend/media/talking-orange-card-base.pdf` at actual size
2. Ensure good lighting and contrast
3. Keep marker flat and visible
4. Optimal distance: 1-2 feet from camera

## 🔍 Server Diagnostics

### Check Audio Permissions (Run on Server)

If audio files aren't being saved, run these diagnostic commands on your server:

```bash
# Quick check
./check_server.sh

# Detailed Python diagnostic
cd backend
python3 check_audio_permissions.py
```

**Common fixes:**
```bash
# Fix permissions for user directories (new multi-user system)
chmod 755 backend/users

# Or fix ownership
chown -R $(whoami) backend/users

# Check if user directories exist
ls -la backend/users/

# For a specific user
ls -la backend/users/{user_id}/

# Legacy data directory (deprecated - kept for backward compatibility)
# New files use user-specific directories automatically
```

### Install TTS Engines (If Missing)

**If you see "No TTS engines available" error:**

```bash
# Check if TTS engines are installed
which espeak festival pico2wave

# If none are found, install them:
sudo ./install_tts_engines.sh

# Or manually:
sudo apt update
sudo apt install -y espeak festival libttspico-utils

# Verify installation
which espeak festival pico2wave
```

**After installing, restart the server:**
```bash
sudo systemctl restart talking-orange
# or restart your Flask app manually
```

## 🔍 Troubleshooting

### No Console Logs
- ✅ Check browser console filters (Info, Warnings, Errors enabled)
- ✅ Hard refresh (Ctrl+Shift+R / Cmd+Shift+R)
- ✅ Check for JavaScript errors (red messages)

### AR Marker Not Detected
- ✅ Ensure good lighting
- ✅ Hold marker 1-2 feet from camera
- ✅ Keep marker flat and in focus
- ✅ Check console for tracking logs

### Audio Not Playing
- ✅ Check browser console for audio errors
- ✅ Verify microphone permissions
- ✅ Check backend logs for API errors
- ✅ Test with stop button (should appear during playback)

### Model Not Downloading
- ✅ Check `backend/models/` directory exists
- ✅ Verify write permissions
- ✅ Check internet connection
- ✅ Review backend logs for download progress

### Slow Performance
- ✅ Use `small` model instead of `medium`
- ✅ Enable GPU mode if available: `./start_local.sh --device gpu`
- ✅ Check system resources (CPU, RAM)

## 📝 Development

### Code Structure

**Frontend Architecture:**
- **Modular JavaScript** - Core modules in `frontend/js/`
  - `ar-core.js` - AR initialization, target loading, media management
  - `tracking-system.js` - AR tracking event handlers
  - `camera-video.js` - Camera diagnostics and video stream management
  - `ui-helpers.js` - UI helper functions (burger menu, etc.)
  - `nostr-auth.js` - Nostr authentication and key management
- **Project-Specific Modules** - Loaded dynamically from `backend/users/{user_id}/{project_name}/js/`
  - `animation-module.js` - Animation controller class
  - `animation-controllers.js` - Thinking and talking animation controllers
  - `voice-processing.js` - Voice recording and processing
- **Event-driven AR tracking** - Real-time marker detection and tracking
- **Frame-based animation system** - 145-frame talking/thinking animations
- **Comprehensive logging** - Detailed console logs for debugging

**Backend Architecture:**
- **Flask REST API** - RESTful endpoints for all operations
- **User Management** (`backend/user_manager.py`) - Multi-user, multi-project system
- **Modular voice processing** (`backend/gen/`) - STT, TTS, LLM integration
- **Project-based storage** - `backend/users/{user_id}/{project_name}/`
- **Automatic model management** - Whisper model downloading and caching
- **Error handling and logging** - Comprehensive error tracking

### Adding Features

1. **New Animation States:** Add frames to project's `media/videos/` directory
2. **New TTS Voices:** Configure in `backend/gen/text_to_voice.py`
3. **New Prompts:** Add to project's `prompts/` directory
4. **Project-Specific Modules:** Add JS files to `backend/users/{user_id}/{project_name}/js/`
5. **Project-Specific UI:** Customize `backend/users/{user_id}/{project_name}/ui.html`
6. **API Endpoints:** Add routes in `backend/app.py`

## 📄 License

This project is proprietary. All rights reserved.

**Third-party Licenses:**
- **MIT License:** MindAR, A-Frame, Three.js, Whisper
- **BSD License:** Flask
- **PSF License:** Python

## 🤝 Contributing

This is a private project. For issues or questions, contact the maintainer.

## 📚 Additional Resources

- [MindAR Documentation](https://github.com/hiukim/mind-ar-js)
- [A-Frame Documentation](https://aframe.io/docs/)
- [Whisper Documentation](https://github.com/openai/whisper)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

## 🔐 Authentication & User Management

### Nostr Authentication

The application uses **Nostr** (Notes and Other Stuff Transmitted by Relays) for secure authentication:

- **Private Key (nsec)**: Your secret key - never share this!
- **Public Key (npub)**: Your user identifier - derived from nsec
- **User ID**: Your npub is used as your user ID

**Features:**
- Generate new Nostr key pairs
- Import existing keys
- Secure httpOnly cookies for session management
- npub-based user identification

**Security:**
- Private keys (nsec) are never stored on the server
- Only public keys (npub) are stored in secure cookies
- All authentication is handled client-side with Nostr tools

### Project Management

Each user can create and manage multiple AR projects:

1. **Create Project**: Go to User Home → "Create New Project"
2. **Upload Content**: 
   - AR Target Image (automatically compiled to .mind file)
   - Media files (images, videos, audio)
3. **Project Structure**: `backend/users/{npub}/{project_name}/`
   - `media/` - Target images and media files
   - `ai/` - AI-generated audio responses
   - `user-input/` - User voice recordings
   - `js/` - Project-specific JavaScript modules
   - `ui.html` - Project-specific UI

### User Directory Structure

```
backend/users/
└── {npub}/                    # User directory (Nostr public key)
    └── {project_name}/        # Project directory
        ├── media/             # Media files (targets, images, videos)
        ├── ai/                # AI audio responses
        ├── user-input/        # User audio inputs
        ├── js/                # Project-specific JS modules
        │   ├── animation-module.js
        │   ├── animation-controllers.js
        │   └── voice-processing.js
        └── ui.html            # Project-specific UI
```

## 📊 Project Status & Next Steps

### ✅ Recent Updates (2025-12-12)

1. **Nostr Authentication System**
   - Implemented Nostr-based authentication with nsec/npub keys
   - Added secure login modal with key generation and import
   - Integrated httpOnly cookie-based session management
   - Updated user management to use npub as user ID

2. **Project Management System**
   - Multi-project support per user
   - Project creation and management UI
   - Project-specific content uploads
   - Dynamic loading of project-specific modules and UI

3. **Modular Architecture**
   - Extracted core AR functions into separate modules
   - Project-specific code loaded dynamically after target detection
   - Improved code organization and maintainability

### ✅ Previous Updates (2025-12-11)

1. **Audio Playback Fixes**
   - Fixed audio not playing by adding explicit volume (1.0) and muted (false) settings
   - Enhanced audio error handling with detailed error codes and messages
   - Added comprehensive logging for audio loading, playback, and errors
   - Fixed audio playback for thinking, intro, and response audio

2. **Backend Error Handling**
   - Fixed `UnboundLocalError` for `traceback` and `time` variables
   - Improved JSON parsing with better error messages
   - Enhanced API error responses with detailed debugging information
   - Added validation for audio data before processing

3. **GPU Support & Performance**
   - Added GPU auto-detection as default in `start_local.sh`
   - Enhanced GPU memory checking and CUDA error handling
   - Added automatic fallback to CPU if GPU memory is insufficient
   - Improved logging for GPU/CPU device selection and memory status
   - Added `PYTORCH_CUDA_ALLOC_CONF` for better memory management

4. **Frontend Improvements**
   - Enhanced error messages for API failures
   - Added audio validation before sending to backend
   - Improved user feedback for microphone issues
   - Better error extraction from backend responses

### ✅ Previous Updates (2025-11-29)

1. **AR Tracking Stability Improvements**
   - Enhanced smoothing with frame averaging (5-frame buffer)
   - Added dead zone filtering (0.0005m position, 0.1° rotation)
   - Implemented velocity-based filtering to reject noise
   - Adjusted MindAR parameters for better stability

2. **TTS Engine Fixes**
   - Fixed espeak, festival, and pico2wave command execution
   - Added comprehensive error logging for TTS failures
   - Improved engine selection priority (local CPU engines first)

3. **API & Network Improvements**
   - Added 2-minute timeout to API requests (prevents hanging)
   - Enhanced error handling for network failures
   - Automatic thinking animation stop on API errors

4. **Installation & Configuration**
   - Fixed install script for Debian/Ubuntu compatibility
   - Added root/sudo/su detection for package installation
   - Fixed virtual environment path in start.sh

### 🐛 Known Issues & Limitations

#### ⚠️ Whisper Transcription Speed on CPU
**Issue:** Whisper transcription can be slow on CPU-only systems.

**Current Status:**
- ✅ GPU auto-detection enabled by default
- ✅ Automatic fallback to CPU if GPU unavailable
- ✅ Small model used by default (faster than medium)
- ⚠️ CPU transcription can take 10-30+ seconds depending on audio length

**Optimization Tips:**
- Use GPU when available: `./start_local.sh --device gpu`
- Use small model (default): `./start_local.sh --model small`
- For CPU-only: Consider using `base` model for faster responses (less accurate)

#### ⚠️ Server TTS (If Issues Occur)
**If TTS fails on server:**
1. Check TTS engines: `which espeak festival pico2wave`
2. Test manually: `echo "test" | espeak --stdout > /tmp/test.wav`
3. Check permissions: `python3 backend/check_audio_permissions.py`
4. Review server logs for detailed error messages

#### ⚠️ Browser Audio Restrictions
**Note:** Some browsers may block autoplay until user interaction. The app handles this automatically, but ensure:
- User clicks the "Ask Question" button (triggers user interaction)
- Browser tab is not muted
- Audio permissions are granted

### 📋 Future Enhancements

**Performance Improvements:**
- Add transcription progress feedback to UI
- Implement audio preprocessing (silence trimming, compression)
- Add request queuing to prevent multiple simultaneous requests
- Consider streaming transcription for faster responses

**User Experience:**
- Add "Processing audio..." message with estimated time
- Show transcription progress indicator
- Add cancel button for long-running requests
- Implement audio level visualization during recording

### 🔧 Configuration Checklist

**Server Configuration:**
- [ ] `WHISPER_FORCE_CPU=true` in .env
- [ ] `WHISPER_MODEL_NAME=small` in .env (or `base` for speed)
- [ ] TTS engines installed and in PATH
- [ ] Audio save directories have write permissions
- [ ] Backend server is running and accessible

**Performance Settings:**
- [x] GPU auto-detection enabled (default)
- [x] Small Whisper model used by default
- [x] Automatic CPU fallback if GPU unavailable
- [x] TTS using fastest local engine (espeak)
- [ ] Audio compression optimized (future enhancement)

### 📈 Performance Status

**Current Performance:**
- AR tracking: **Stable** ✅
- Audio playback: **Working** ✅
- TTS synthesis: **Working** ✅ (local engines)
- Voice input → Response: **Varies by device** ⚠️
  - GPU: **5-15 seconds** ✅
  - CPU (small model): **10-30 seconds** ⚠️
  - CPU (medium model): **30-60+ seconds** ❌

**Optimization Tips:**
- Use GPU when available for fastest transcription
- Use small model for good balance of speed/accuracy
- Use base model for fastest CPU performance (less accurate)

### 🚀 Next Development Priorities

1. **Add transcription progress feedback** (user experience)
2. **Optimize audio preprocessing** (reduce Whisper load, faster responses)
3. **Implement request queuing** (prevent multiple simultaneous requests)
4. **Add audio level visualization** (better recording feedback)
5. **Server deployment optimization** (production-ready configuration)

---

**Last Updated:** 2025-12-12
**Version:** 1.2
**Status:** ✅ Core Features Working - Nostr Auth & Project Management Added
