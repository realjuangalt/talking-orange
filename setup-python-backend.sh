#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🐍 Setting up Python Backend for Talking Orange AR Project..."

# Check OS
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ This script is designed for Linux systems"
    exit 1
fi

# Check Python version
python3 --version || {
    echo "❌ Python 3 is required but not installed"
    exit 1
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with VENICE_KEY and other required keys"
    exit 1
fi

# Update package lists
echo "🔄 Updating package lists..."
sudo apt-get update

# Install system dependencies for audio processing and TTS
echo "🔧 Installing system dependencies..."
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    ffmpeg \
    libasound2-dev \
    espeak \
    festival \
    libttspico-utils \
    portaudio19-dev \
    python3-dev \
    libssl-dev \
    libffi-dev

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "🔧 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "🔧 Installing Python dependencies..."
pip install -r backend/requirements.txt
pip install -r gen/requirements-python.txt

# Test Python installation
echo "🧪 Testing Python installation..."
python3 -c "import flask; print('✅ Flask available')" || echo "❌ Flask not available"
python3 -c "import whisper; print('✅ whisper available')" || echo "❌ whisper not available"
python3 -c "import pydub; print('✅ pydub available')" || echo "❌ pydub not available"
python3 -c "import torch; print('✅ torch available')" || echo "❌ torch not available"
python3 -c "import requests; print('✅ requests available')" || echo "❌ requests not available"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p public/audio
mkdir -p frontend
mkdir -p gen/prompts
mkdir -p gen/voices

# Make startup script executable
chmod +x start_backend.py

# Test the backend
echo "🧪 Testing Python backend..."
python3 -c "
import sys
sys.path.insert(0, 'gen')
from main import TalkingOrangeVoiceSystem
print('✅ Main voice system imports successfully')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Python backend setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Ensure your .env file has VENICE_KEY and other required keys"
    echo "2. Start the server: python3 start_backend.py"
    echo "3. Or use: npm start"
    echo "4. Test the AR experience with voice interaction"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "- If Python imports fail, activate the virtual environment: source venv/bin/activate"
    echo "- If API calls fail, verify your API keys in .env"
    echo "- Check the server logs for detailed error messages"
    echo ""
    echo "🎭 Python backend features:"
    echo "- Flask web server with CORS support"
    echo "- Real Venice AI integration for Bitcoin responses"
    echo "- Whisper transcription with local models"
    echo "- Multiple TTS engines (espeak, festival, pico2wave, gTTS)"
    echo "- Web search capabilities for up-to-date information"
    echo ""
    echo "₿ Happy Bitcoin evangelizing with your Python-powered Orange!"
else
    echo ""
    echo "❌ Python backend setup failed!"
    echo "Please check the error messages above and try again."
    echo ""
    echo "Common issues:"
    echo "- Missing API keys in .env file"
    echo "- Python packages not installed correctly"
    echo "- Network connectivity issues"
    echo "- Insufficient disk space for Whisper models"
fi
