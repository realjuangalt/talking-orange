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
- ✅ **CPU/GPU Support** - Automatic device detection with manual override
- ✅ **Model Management** - Automatic model downloading to `backend/models/`
- ✅ **LLM Integration** - Venice AI for Bitcoin evangelism responses
- ✅ **Text-to-Speech** - Multiple TTS engines with fallback
- ✅ **Audio Playback** - MP3 audio responses with stop button

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
│   ├── lib/                     # Pre-bundled AR libraries
│   │   ├── aframe.min.js
│   │   └── mindar-image-aframe.prod.js
│   └── media/
│       ├── targets.mind         # MindAR marker file
│       ├── talking-orange-*.png # Character images
│       └── videos/
│           ├── talking-orange-talking-animation/  # 145 frames + audio
│           └── talking-orange-thinking-animation/ # 145 frames + audio
├── backend/
│   ├── app.py                   # Flask server
│   ├── gen/                     # Voice processing modules
│   │   ├── main.py             # Main voice system
│   │   ├── voice_to_text.py    # Whisper STT
│   │   ├── text_to_voice.py    # TTS engines
│   │   └── text_generator.py   # LLM integration
│   ├── models/                  # Whisper models (small.pt, medium.pt)
│   └── voices/                  # TTS voice files
├── start.sh                     # Production server script
├── start_local.sh               # Development server with options
├── install.sh                   # Installation script
├── requirements-python.txt      # Python dependencies
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

#### Production Mode
```bash
./start.sh
```

**Note:** Production mode runs with `DEBUG=false` by default. Set `DEBUG=true` in `.env` for debug mode.

### Accessing the Application

1. **Open browser** to `http://localhost:3000`
2. **Grant permissions** for camera and microphone
3. **Print the marker** from `frontend/media/talking-orange-card-base.pdf`
4. **Point camera** at the marker (1-2 feet away)
5. **Click "Ask Question"** to start voice interaction

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Server Configuration
PORT=3000
DEBUG=true                    # Enable Flask debug mode

# Whisper Configuration
WHISPER_MODEL_NAME=small      # small or medium
WHISPER_FORCE_CPU=true        # Force CPU mode (true/false)

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

### Voice Processing
- `POST /api/speech/process` - Full voice-to-voice pipeline
- `POST /api/speech/transcribe` - Speech-to-text only
- `POST /api/speech/synthesize` - Text-to-speech only

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
# Fix permissions
chmod 755 backend/data/ai
chmod 755 backend/data/user

# Or fix ownership
chown -R $(whoami) backend/data

# Check if directories exist
ls -la backend/data/
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

**Frontend (`frontend/index.html`):**
- Modular JavaScript architecture
- Event-driven AR tracking
- Frame-based animation system
- Comprehensive logging (168+ console.log statements)

**Backend (`backend/`):**
- Flask REST API
- Modular voice processing (`backend/gen/`)
- Automatic model management
- Error handling and logging

### Adding Features

1. **New Animation States:** Add frames to `frontend/media/videos/`
2. **New TTS Voices:** Configure in `backend/gen/text_to_voice.py`
3. **New Prompts:** Add to `backend/gen/prompts/`
4. **API Endpoints:** Add routes in `backend/app.py`

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

**Last Updated:** 2024
**Version:** 1.0
**Status:** ✅ Production Ready
