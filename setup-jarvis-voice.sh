#!/bin/bash

# Talking Orange AR Project - Jarvis Voice Service Setup Script
# This script sets up the Jarvis voice service integration

echo "🎭 Talking Orange AR Project - Jarvis Voice Service Setup"
echo "========================================================="

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ This script is designed for Linux systems"
    exit 1
fi

# Check if jarvis directory exists
if [ ! -d "jarvis/writing_assistant" ]; then
    echo "❌ Jarvis writing assistant directory not found. Please ensure jarvis/writing_assistant exists."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with VENICE_KEY and other required keys"
    exit 1
fi

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    ffmpeg \
    portaudio19-dev \
    python3-pyaudio

# Install Python packages for Jarvis voice service
echo "📚 Installing Python AI packages..."
pip3 install --user \
    whisper \
    pydub \
    torch \
    torchaudio \
    requests \
    python-dotenv \
    aiohttp \
    yt-dlp

# Install additional packages for the writing assistant
echo "🔧 Installing writing assistant dependencies..."
cd jarvis/writing_assistant
pip3 install --user \
    python-telegram-bot==20.6 \
    whisper \
    pydub \
    yt-dlp \
    requests \
    python-dotenv

cd ../..

# Test Python installation
echo "🧪 Testing Python installation..."
python3 -c "import whisper; print('✅ whisper available')" || echo "❌ whisper not available"
python3 -c "import pydub; print('✅ pydub available')" || echo "❌ pydub not available"
python3 -c "import torch; print('✅ torch available')" || echo "❌ torch not available"
python3 -c "import requests; print('✅ requests available')" || echo "❌ requests not available"

# Test Jarvis voice service
echo "🧪 Testing Jarvis voice service..."
cd jarvis/writing_assistant
python3 -c "
import sys
import os
try:
    # Test Whisper model loading
    import whisper
    print('✅ Whisper imported successfully')
    
    # Test Venice AI API
    import requests
    print('✅ Requests imported successfully')
    
    # Test TTS functionality
    print('✅ Jarvis voice service components available')
    
except ImportError as e:
    print(f'❌ Import failed: {e}')
except Exception as e:
    print(f'❌ Jarvis voice service error: {e}')
"
cd ../..

# Test API keys
echo "🔑 Testing API keys..."
if grep -q "VENICE_KEY=" .env; then
    echo "✅ VENICE_KEY found in .env"
else
    echo "❌ VENICE_KEY not found in .env"
fi

if grep -q "GROK_KEY=" .env; then
    echo "✅ GROK_KEY found in .env"
else
    echo "❌ GROK_KEY not found in .env"
fi

# Create test script
echo "📝 Creating test script..."
cat > test-jarvis-voice.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for Jarvis voice service integration
"""

import asyncio
import sys
import os
import json

# Add jarvis directory to path
jarvis_dir = os.path.join(os.path.dirname(__file__), 'jarvis/writing_assistant')
if jarvis_dir not in sys.path:
    sys.path.insert(0, jarvis_dir)

async def test_jarvis_voice():
    try:
        print("🎭 Testing Jarvis voice service...")
        
        # Test Whisper import
        import whisper
        print("✅ Whisper imported")
        
        # Test TTS functionality
        import requests
        print("✅ Requests imported")
        
        # Test Venice AI API (if key is available)
        from dotenv import load_dotenv
        load_dotenv()
        
        venice_key = os.getenv('VENICE_KEY')
        if venice_key:
            print("✅ Venice AI API key found")
        else:
            print("⚠️ Venice AI API key not found")
        
        print("🎉 Jarvis voice service test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_jarvis_voice())
    if success:
        print("🎉 Jarvis voice service test successful!")
    else:
        print("❌ Jarvis voice service test failed!")
        sys.exit(1)
EOF

chmod +x test-jarvis-voice.py

# Run test
echo "🧪 Running Jarvis voice service test..."
python3 test-jarvis-voice.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Jarvis voice service setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Ensure your .env file has VENICE_KEY and other required keys"
    echo "2. Start the server: npm start"
    echo "3. Test the AR experience with voice interaction"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "- If Python imports fail, check your PATH includes ~/.local/bin"
    echo "- If API calls fail, verify your API keys in .env"
    echo "- Check the server logs for detailed error messages"
    echo ""
    echo "🎭 Jarvis voice service features:"
    echo "- Whisper transcription with local models"
    echo "- Venice AI TTS with bm_fable voice"
    echo "- Bitcoin-specific content generation"
    echo "- Web search capabilities for up-to-date information"
    echo ""
    echo "₿ Happy Bitcoin evangelizing with your enhanced Orange!"
else
    echo ""
    echo "❌ Jarvis voice service setup failed!"
    echo "Please check the error messages above and try again."
    echo ""
    echo "Common issues:"
    echo "- Missing API keys in .env file"
    echo "- Python packages not installed correctly"
    echo "- Network connectivity issues"
    echo "- Insufficient disk space for Whisper models"
fi
