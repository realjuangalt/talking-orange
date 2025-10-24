#!/bin/bash

# Talking Orange AR Project - Voice Processing Setup Script
# This script sets up the voice processing system with STT and TTS capabilities

echo "🎤 Talking Orange AR Project - Voice Processing Setup"
echo "===================================================="

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ This script is designed for Linux systems"
    exit 1
fi

# Check if gen directory exists
if [ ! -d "gen" ]; then
    echo "❌ Gen directory not found. Please ensure the gen folder is present."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with required API keys"
    exit 1
fi

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    ffmpeg \
    portaudio19-dev \
    python3-pyaudio \
    espeak \
    espeak-data \
    festival \
    festival-dev \
    libasound2-dev \
    libsndfile1-dev \
    libpulse-dev \
    build-essential

# Install pico2wave (lightweight TTS)
echo "🔊 Installing pico2wave TTS..."
sudo apt install -y \
    libttspico-utils \
    libttspico-data

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install --user \
    whisper \
    torch \
    torchaudio \
    pydub \
    gtts \
    pyttsx3 \
    soundfile \
    librosa \
    requests \
    python-dotenv \
    aiohttp

# Install additional packages for the gen system
echo "📚 Installing gen system dependencies..."
cd gen
pip3 install --user -r requirements-python.txt
cd ..

# Test Python installation
echo "🧪 Testing Python installation..."
python3 -c "import whisper; print('✅ whisper available')" || echo "❌ whisper not available"
python3 -c "import torch; print('✅ torch available')" || echo "❌ torch not available"
python3 -c "import pydub; print('✅ pydub available')" || echo "❌ pydub not available"
python3 -c "import gtts; print('✅ gtts available')" || echo "❌ gtts not available"
python3 -c "import soundfile; print('✅ soundfile available')" || echo "❌ soundfile not available"

# Test TTS engines
echo "🔊 Testing TTS engines..."
echo "Testing espeak..."
espeak --version || echo "❌ espeak not working"

echo "Testing festival..."
echo "Hello" | festival --tts --pipe || echo "❌ festival not working"

echo "Testing pico2wave..."
pico2wave --lang=en --wave=/tmp/test.wav "Hello" && rm -f /tmp/test.wav && echo "✅ pico2wave working" || echo "❌ pico2wave not working"

# Test API keys
echo "🔑 Testing API keys..."
if grep -q "VENICE_KEY=" .env; then
    echo "✅ VENICE_KEY found in .env"
else
    echo "❌ VENICE_KEY not found in .env"
fi

if grep -q "ELEVENLABS_API_KEY=" .env; then
    echo "✅ ELEVENLABS_API_KEY found in .env"
else
    echo "❌ ELEVENLABS_API_KEY not found in .env"
fi

if grep -q "OPENAI_API_KEY=" .env; then
    echo "✅ OPENAI_API_KEY found in .env"
else
    echo "❌ OPENAI_API_KEY not found in .env"
fi

# Create voice directories
echo "📁 Creating voice directories..."
mkdir -p voices
mkdir -p models
mkdir -p tmp

# Set permissions
chmod 755 voices models tmp

# Create test script
echo "📝 Creating test script..."
cat > test-voice-processing.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for voice processing system
"""

import sys
import os
import tempfile

# Add gen directory to path
gen_dir = os.path.join(os.path.dirname(__file__), 'gen')
if gen_dir not in sys.path:
    sys.path.insert(0, gen_dir)

def test_voice_processing():
    try:
        print("🎤 Testing voice processing system...")
        
        # Test imports
        from voice_to_text import VoiceToTextService
        from text_to_voice import TextToVoiceService
        from voice_processor import VoiceProcessor
        
        print("✅ All modules imported successfully")
        
        # Test STT service
        stt_service = VoiceToTextService()
        if stt_service.initialize():
            print("✅ STT service initialized")
        else:
            print("❌ STT service initialization failed")
        
        # Test TTS service
        tts_service = TextToVoiceService()
        print(f"✅ TTS service initialized with engines: {tts_service.available_engines}")
        
        # Test voice processor
        processor = VoiceProcessor()
        if processor.initialize():
            print("✅ Voice processor initialized")
            print(f"Status: {processor.get_status()}")
        else:
            print("❌ Voice processor initialization failed")
        
        # Test TTS synthesis
        try:
            result = tts_service.synthesize_speech("Hello, I am the Talking Orange!", "default", "en")
            print(f"✅ TTS synthesis successful: {len(result['audio_data'])} bytes")
        except Exception as e:
            print(f"⚠️ TTS synthesis test failed: {e}")
        
        print("🎉 Voice processing system test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_voice_processing()
    if success:
        print("🎉 Voice processing system test successful!")
    else:
        print("❌ Voice processing system test failed!")
        sys.exit(1)
EOF

chmod +x test-voice-processing.py

# Run test
echo "🧪 Running voice processing test..."
python3 test-voice-processing.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Voice processing setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Ensure your .env file has required API keys"
    echo "2. Start the server: npm start"
    echo "3. Test the AR experience with voice interaction"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "- If Python imports fail, check your PATH includes ~/.local/bin"
    echo "- If TTS engines fail, check system package installation"
    echo "- If API calls fail, verify your API keys in .env"
    echo "- Check the server logs for detailed error messages"
    echo ""
    echo "🎤 Voice processing features:"
    echo "- Whisper transcription with local models"
    echo "- Multiple TTS engines: espeak, festival, pico2wave, gTTS"
    echo "- Cloud TTS: Venice AI, ElevenLabs, OpenAI"
    echo "- Bitcoin-specific content generation"
    echo "- Low hardware requirements with local engines"
    echo ""
    echo "₿ Happy Bitcoin evangelizing with your enhanced Orange!"
else
    echo ""
    echo "❌ Voice processing setup failed!"
    echo "Please check the error messages above and try again."
    echo ""
    echo "Common issues:"
    echo "- Missing system packages (espeak, festival, pico2wave)"
    echo "- Python packages not installed correctly"
    echo "- Missing API keys in .env file"
    echo "- Insufficient disk space for Whisper models"
    echo "- Network connectivity issues"
fi
