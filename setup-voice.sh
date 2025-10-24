#!/bin/bash

# Talking Orange AR Project - Voice Setup Script
# This script installs Whisper, TTS engines, and Python dependencies

echo "🍊 Talking Orange AR Project - Voice Setup"
echo "=========================================="

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ This script is designed for Linux systems"
    exit 1
fi

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install system dependencies for audio processing
echo "🔧 Installing audio processing dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libssl-dev \
    libffi-dev \
    portaudio19-dev \
    libsndfile1-dev \
    libasound2-dev \
    libpulse-dev \
    ffmpeg \
    espeak \
    festival \
    pico2wave \
    build-essential

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install --user -r requirements-python.txt

# Install Whisper
echo "🎤 Installing OpenAI Whisper..."
pip3 install --user openai-whisper

# Install additional audio libraries
echo "🔊 Installing additional audio libraries..."
pip3 install --user \
    torch \
    torchaudio \
    numpy \
    scipy \
    librosa \
    soundfile \
    pyaudio \
    pydub

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p temp/audio
mkdir -p public/audio
mkdir -p models/whisper

# Set up environment variables
echo "⚙️ Setting up environment..."
if [ ! -f .env ]; then
    cp env.example .env
    echo "✅ Created .env file from template"
fi

# Add Whisper to PATH (if needed)
echo "🔧 Setting up Whisper..."
if ! command -v whisper &> /dev/null; then
    echo "⚠️ Whisper not found in PATH. You may need to add Python user bin to PATH:"
    echo "export PATH=\$PATH:~/.local/bin"
    echo "Add this to your ~/.bashrc or ~/.profile"
fi

# Test installations
echo "🧪 Testing installations..."

# Test espeak
if command -v espeak &> /dev/null; then
    echo "✅ espeak installed"
    espeak "Hello, this is a test" --stdout > /dev/null 2>&1 && echo "✅ espeak working"
else
    echo "❌ espeak not working"
fi

# Test festival
if command -v festival &> /dev/null; then
    echo "✅ festival installed"
else
    echo "❌ festival not working"
fi

# Test pico2wave
if command -v pico2wave &> /dev/null; then
    echo "✅ pico2wave installed"
    pico2wave -l en-US -w /tmp/test.wav "Hello test" 2>/dev/null && echo "✅ pico2wave working"
else
    echo "❌ pico2wave not working"
fi

# Test Python packages
echo "🐍 Testing Python packages..."
python3 -c "import whisper; print('✅ Whisper imported successfully')" 2>/dev/null || echo "❌ Whisper import failed"
python3 -c "import torch; print('✅ PyTorch imported successfully')" 2>/dev/null || echo "❌ PyTorch import failed"
python3 -c "import librosa; print('✅ Librosa imported successfully')" 2>/dev/null || echo "❌ Librosa import failed"

# Set permissions
echo "🔐 Setting permissions..."
chmod 755 temp/
chmod 755 public/
chmod 755 models/

echo ""
echo "🎉 Voice setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Add your OpenAI API key to .env file:"
echo "   OPENAI_API_KEY=your_api_key_here"
echo ""
echo "2. Test the voice features:"
echo "   npm start"
echo "   # Then test the AR experience with voice"
echo ""
echo "3. Optional: Download Whisper models:"
echo "   whisper --model base"
echo ""
echo "🔧 Troubleshooting:"
echo "- If Whisper is not found, add ~/.local/bin to your PATH"
echo "- If TTS engines fail, check system audio configuration"
echo "- For better quality, consider using cloud TTS services (ElevenLabs, OpenAI)"
echo ""
echo "🍊 Happy talking with your Orange!"
