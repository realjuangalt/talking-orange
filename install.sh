#!/bin/bash

# Talking Orange AR Project - MINIMAL Server Installation Script
# This script installs ONLY runtime dependencies needed for production server
# 
# REMOVED (not needed for runtime):
# - Node.js/npm: Frontend uses pre-bundled libraries (aframe.min.js, mindar)
# - OpenCV: Only needed for pre-processing videos locally (extract_frames, etc.)
# - Blender: Not used in runtime
# - ImageMagick: Not used in code
# - portaudio/pyaudio: Browser uses MediaRecorder API instead
# - Multiple TTS engines: Only install what's actually used (espeak, festival, pico)
#
# Video processing scripts (extract_video_frames.py, remove_green_from_frames.py, 
# resize_animation_frames.py) should be run locally BEFORE deploying to server.

echo "🍊 Talking Orange AR Project - Minimal Server Installation"
echo "========================================================"
echo "📋 Installing ONLY runtime dependencies (minimal resource footprint)"
echo ""

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ This script is designed for Linux systems"
    exit 1
fi

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install MINIMAL system dependencies for runtime
echo "🔧 Installing core system dependencies..."
sudo apt install -y \
    curl \
    wget \
    git \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    sqlite3 \
    ffmpeg \
    nginx

# Audio processing dependencies (for TTS and audio conversion)
echo "🔊 Installing audio processing dependencies..."
sudo apt install -y \
    libsndfile1-dev \
    espeak \
    festival \
    libttspico-utils

# OpenSSL and security libraries (required for building Python packages like torch)
echo "🔒 Installing security libraries..."
sudo apt install -y \
    libssl-dev \
    libffi-dev

# Create Python virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Created Python virtual environment"
else
    echo "✅ Python virtual environment already exists"
fi

# Activate virtual environment and install Python dependencies
echo "📦 Installing Python runtime dependencies..."
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install Python requirements for runtime
if [ -f "requirements-python.txt" ]; then
    pip install -r requirements-python.txt
    echo "✅ Installed Python dependencies from requirements-python.txt"
else
    # Fallback: install only what's needed for runtime
    echo "⚠️  No requirements-python.txt found, installing minimal runtime packages..."
    pip install Flask Flask-CORS python-dotenv requests aiohttp \
        openai-whisper torch torchaudio pydub gtts \
        soundfile numpy jsonschema
    echo "✅ Installed core runtime Python dependencies"
fi

deactivate

# Download AR libraries if missing
echo ""
echo "📦 Checking AR libraries..."
mkdir -p frontend/lib

if [ ! -f "frontend/lib/aframe.min.js" ]; then
    echo "   Downloading A-Frame library..."
    wget -q -O frontend/lib/aframe.min.js https://cdn.jsdelivr.net/npm/aframe@1.4.2/dist/aframe.min.js
    if [ $? -eq 0 ]; then
        echo "   ✅ Downloaded aframe.min.js"
    else
        echo "   ⚠️  Failed to download aframe.min.js - AR may not work"
    fi
else
    echo "   ✅ aframe.min.js already exists"
fi

if [ ! -f "frontend/lib/mindar-image-aframe.prod.js" ]; then
    echo "   Downloading MindAR library..."
    wget -q -O frontend/lib/mindar-image-aframe.prod.js https://cdn.jsdelivr.net/npm/mind-ar@1.2.4/dist/mindar-image-aframe.prod.js
    if [ $? -eq 0 ]; then
        echo "   ✅ Downloaded mindar-image-aframe.prod.js"
    else
        echo "   ⚠️  Failed to download mindar-image-aframe.prod.js - AR may not work"
    fi
else
    echo "   ✅ mindar-image-aframe.prod.js already exists"
fi

echo "📝 Frontend note: AR libraries are in frontend/lib/ (aframe.min.js, mindar-image-aframe.prod.js)"
echo "   - No Node.js/npm needed - frontend uses pre-bundled libraries"
echo "   - No build process required, just serve the static HTML file"

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p uploads
mkdir -p frontend/media/videos/talking-orange-talking-animation
mkdir -p frontend/media/videos/talking-orange-thinking-animation
mkdir -p backend/data/user
mkdir -p backend/data/ai
mkdir -p backend/models

# Set up environment file
echo "⚙️ Setting up environment..."
if [ ! -f .env ]; then
    cp env.example .env
    echo "✅ Created .env file from template"
else
    echo "✅ .env file already exists"
fi

# Set permissions
echo "🔐 Setting permissions..."
chmod +x install.sh
chmod 755 uploads/

# Verify installation
echo "✅ Verifying installation..."
echo "Python version: $(python3 --version)"
echo "FFmpeg version: $(ffmpeg -version 2>/dev/null | head -n 1 || echo 'Not found')"
echo "espeak version: $(espeak --version 2>/dev/null || echo 'Not found')"

# Test Python backend (if available)
echo "🚀 Testing Python backend setup..."
if [ -f "start_backend.py" ] || [ -f "backend/app.py" ]; then
    source venv/bin/activate
    python3 -c "import flask; import whisper; print('✅ All core Python dependencies imported successfully')" 2>/dev/null && \
        echo "✅ Python backend dependencies verified" || \
        echo "⚠️  Some Python dependencies may be missing (this is okay for production if they're installed via requirements)"
    deactivate
fi

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📋 Next steps for SERVER DEPLOYMENT:"
echo ""
echo "1. Configure environment variables:"
echo "   - Copy env.example to .env if needed"
echo "   - Set VENICE_KEY and other required variables"
echo ""
echo "2. Start the backend server:"
echo "   source venv/bin/activate"
echo "   python start_backend.py"
echo "   # Or use systemd service (see below)"
echo ""
echo "3. Set up nginx reverse proxy (recommended for production):"
echo "   - Edit /etc/nginx/sites-available/talking-orange"
echo "   - Point proxy_pass to http://127.0.0.1:3000"
echo "   - Enable: sudo ln -s /etc/nginx/sites-available/talking-orange /etc/nginx/sites-enabled/"
echo "   - Restart: sudo systemctl restart nginx"
echo ""
echo "4. Optional - Set up systemd service for auto-start:"
echo "   - Create /etc/systemd/system/talking-orange.service"
echo "   - Enable: sudo systemctl enable talking-orange"
echo "   - Start: sudo systemctl start talking-orange"
echo ""
echo "🔧 Python backend commands:"
echo "- source venv/bin/activate    # Activate virtual environment"
echo "- python start_backend.py    # Start Flask server"
echo "- python backend/app.py       # Alternative start method"
echo ""
echo "📱 Access your site:"
echo "- Direct: http://YOUR_IP:3000"
echo "- Via nginx: http://YOUR_IP (port 80)"
echo ""
echo "🍊 Happy deployment with Talking Orange!"
