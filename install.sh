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

# Detect distribution (Debian or Ubuntu)
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    DISTRO_VERSION=$VERSION_ID
    echo "🔍 Detected distribution: $DISTRO $DISTRO_VERSION"
else
    echo "⚠️  Could not detect distribution, assuming Debian/Ubuntu"
    DISTRO="debian"
fi

# Verify it's Debian or Ubuntu
if [[ "$DISTRO" != "debian" && "$DISTRO" != "ubuntu" ]]; then
    echo "⚠️  This script is optimized for Debian/Ubuntu"
    echo "   Detected: $DISTRO"
    echo "   Continuing anyway, but some packages might not be available..."
fi

# Detect if running as root (no sudo/su needed) or regular user (need sudo or su)
if [ "$EUID" -eq 0 ]; then
    SUDO_CMD=""
    echo "🔑 Running as root - no sudo/su needed"
else
    # Check if sudo is available
    if command -v sudo &> /dev/null; then
        SUDO_CMD="sudo"
        echo "🔑 Running as regular user - will use sudo"
    elif command -v su &> /dev/null; then
        echo "⚠️  sudo not found, but su is available"
        echo "   This script needs root privileges to install packages"
        echo "   Please run as root using: su -"
        echo "   Or install sudo first"
        exit 1
    else
        echo "❌ Neither sudo nor su found"
        echo "   This script needs root privileges to install packages"
        exit 1
    fi
fi

# Update package list
echo "📦 Updating package list..."
$SUDO_CMD apt update

# Install MINIMAL system dependencies for runtime
echo "🔧 Installing core system dependencies..."
$SUDO_CMD apt install -y \
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

# Install canvas system dependencies (needed for AR target compilation)
echo "🎨 Installing canvas system dependencies (for AR target compilation)..."
$SUDO_CMD apt install -y \
    libcairo2-dev \
    libpango1.0-dev \
    libjpeg-dev \
    libgif-dev \
    librsvg2-dev \
    libpixman-1-dev

# Audio processing dependencies (for TTS and audio conversion)
echo "🔊 Installing audio processing dependencies..."
# Install common TTS engines (package names may differ between Debian/Ubuntu)
if $SUDO_CMD apt install -y libsndfile1-dev espeak festival; then
    echo "  ✅ Core TTS dependencies installed"
else
    echo "  ⚠️  Warning: Some TTS packages may have failed to install"
fi

# Try to install pico2wave - package name differs between Debian versions
# Note: This package may not be available in all Debian/Ubuntu repositories
echo "🔊 Installing pico2wave TTS engine (optional)..."
if $SUDO_CMD apt install -y libttspico-utils >/dev/null 2>&1; then
    echo "  ✅ libttspico-utils installed"
elif $SUDO_CMD apt install -y tts-pico-utils >/dev/null 2>&1; then
    echo "  ✅ tts-pico-utils installed"
elif $SUDO_CMD apt install -y pico2wave >/dev/null 2>&1; then
    echo "  ✅ pico2wave installed"
else
    echo "  ⚠️  pico2wave not available in current repositories"
    echo "  ℹ️  This is optional - espeak and festival should still work"
    echo "  ℹ️  If needed, you can try manually: apt install -y libttspico-utils"
fi

# OpenSSL and security libraries (required for building Python packages like torch)
echo "🔒 Installing security libraries..."
$SUDO_CMD apt install -y \
    libssl-dev \
    libffi-dev

# Additional dependencies that might be needed
echo "📦 Installing additional runtime dependencies..."
$SUDO_CMD apt install -y \
    ca-certificates \
    gnupg \
    lsb-release

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

# Install Node.js and npm (needed for AR target compilation)
echo ""
echo "📦 Checking Node.js (needed for AR target compilation)..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "   ✅ Node.js already installed: $NODE_VERSION"
else
    echo "   📦 Installing Node.js (needed for compiling AR targets)..."
    # Install Node.js 18.x LTS (stable and widely supported)
    curl -fsSL https://deb.nodesource.com/setup_18.x | $SUDO_CMD bash -
    if $SUDO_CMD apt install -y nodejs; then
        NODE_VERSION=$(node --version)
        NPM_VERSION=$(npm --version)
        echo "   ✅ Node.js installed: $NODE_VERSION"
        echo "   ✅ npm installed: $NPM_VERSION"
    else
        echo "   ⚠️  Failed to install Node.js"
        echo "   ℹ️  AR target compilation will not work without Node.js"
        echo "   ℹ️  You can install manually: https://nodejs.org/"
    fi
fi

# Install npm packages (for AR target compilation)
if command -v node &> /dev/null; then
    echo "   📦 Installing npm packages for AR target compilation..."
    
    # Install all dependencies from package.json
    if npm install; then
        echo "   ✅ npm packages installed successfully"
        echo "   📦 Installed packages:"
        echo "      - puppeteer (for browser-based compilation)"
        echo "      - canvas (for image processing)"
        echo "      - jsdom (for browser API emulation)"
        echo "      - mind-ar (AR library)"
    else
        echo "   ⚠️  Some npm packages may have failed to install"
        echo "   ℹ️  AR target compilation may not work properly"
        echo "   ℹ️  Try running manually: npm install"
    fi
    
    # Verify critical packages
    if npm list puppeteer &>/dev/null; then
        echo "   ✅ puppeteer installed (for web compiler automation)"
    else
        echo "   ⚠️  puppeteer not found - AR compilation will fail"
    fi
    
    if npm list canvas &>/dev/null; then
        echo "   ✅ canvas installed"
    else
        echo "   ⚠️  canvas not found"
        echo "   ℹ️  Make sure system dependencies are installed:"
        echo "      sudo apt install -y libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev libpixman-1-dev"
    fi
fi

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
mkdir -p backend/models
mkdir -p backend/users  # User-specific directories will be created on-demand when users log in and create projects
# Note: Project-specific folders (media, videos, etc.) are now created per-user/per-project in backend/users/{npub}/{project_name}/
# Note: Legacy backend/data/ directories are deprecated but kept for backward compatibility

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

# Verify installation
echo "✅ Verifying installation..."
echo "Python version: $(python3 --version)"
echo "FFmpeg version: $(ffmpeg -version 2>/dev/null | head -n 1 || echo 'Not found')"
echo "espeak version: $(espeak --version 2>/dev/null || echo 'Not found')"
echo "festival: $(which festival >/dev/null 2>&1 && echo 'Found' || echo 'Not found')"
echo "pico2wave: $(which pico2wave >/dev/null 2>&1 && echo 'Found' || echo 'Not found')"

# Verify TTS engines are installed
echo ""
echo "🔊 Verifying TTS engines..."
TTS_MISSING=0
if ! which espeak >/dev/null 2>&1; then
    echo "  ❌ espeak NOT found"
    TTS_MISSING=1
else
    echo "  ✅ espeak found"
fi
if ! which festival >/dev/null 2>&1; then
    echo "  ❌ festival NOT found"
    TTS_MISSING=1
else
    echo "  ✅ festival found"
fi
if ! which pico2wave >/dev/null 2>&1; then
    echo "  ❌ pico2wave NOT found"
    TTS_MISSING=1
else
    echo "  ✅ pico2wave found"
fi

if [ $TTS_MISSING -eq 1 ]; then
    echo ""
    echo "⚠️  WARNING: Some TTS engines are missing!"
    echo "   The installation may have failed. Try running manually:"
    echo "   Run as root: apt install -y espeak festival"
    echo "   For pico2wave, try: apt install -y libttspico-utils"
    echo "   Or: apt install -y tts-pico-utils"
    echo "   Or: apt install -y pico2wave"
    echo ""
    echo "   Note: At least one TTS engine (espeak, festival, or pico2wave) is required"
    echo "   The system will work with just espeak or festival if pico2wave is unavailable"
fi

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
