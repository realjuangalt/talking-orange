#!/bin/bash

# Talking Orange AR Project - Bitcoin AI Setup Script
# This script sets up the Python AI content generation system

echo "₿ Talking Orange AR Project - Bitcoin AI Setup"
echo "=============================================="

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
    echo "❌ .env file not found. Please create it with VENICE_KEY and GROK_KEY"
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
    python3-dev

# Install Python packages for AI generation
echo "📚 Installing Python AI packages..."
pip3 install --user \
    aiohttp \
    python-dotenv \
    asyncio \
    json

# Install additional packages for the gen system
echo "🔧 Installing gen system dependencies..."
cd gen
pip3 install --user -r requirements-python.txt 2>/dev/null || echo "⚠️ requirements-python.txt not found, installing manually"

# Install core packages
pip3 install --user \
    aiohttp \
    python-dotenv \
    asyncio \
    json \
    pathlib \
    logging

cd ..

# Test Python installation
echo "🧪 Testing Python installation..."
python3 -c "import aiohttp; print('✅ aiohttp available')" || echo "❌ aiohttp not available"
python3 -c "import json; print('✅ json available')" || echo "❌ json not available"
python3 -c "import asyncio; print('✅ asyncio available')" || echo "❌ asyncio not available"

# Test gen system
echo "🧪 Testing gen system..."
cd gen
python3 -c "
import sys
import os
try:
    from text_generator import TextGenerator
    print('✅ TextGenerator imported successfully')
except ImportError as e:
    print(f'❌ TextGenerator import failed: {e}')
except Exception as e:
    print(f'❌ TextGenerator error: {e}')
"
cd ..

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
cat > test-bitcoin-ai.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for Bitcoin AI content generation
"""

import asyncio
import sys
import os
import json

# Add gen directory to path
gen_dir = os.path.join(os.path.dirname(__file__), 'gen')
if gen_dir not in sys.path:
    sys.path.insert(0, gen_dir)

async def test_bitcoin_ai():
    try:
        from text_generator import TextGenerator
        
        print("₿ Testing Bitcoin AI content generation...")
        
        generator = TextGenerator()
        
        # Test basic text generation
        prompt = "Explain Bitcoin in simple terms for a beginner"
        response = await generator.generate_text(prompt)
        
        if response:
            print(f"✅ AI Response: {response[:100]}...")
            return True
        else:
            print("❌ No response generated")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bitcoin_ai())
    if success:
        print("🎉 Bitcoin AI test successful!")
    else:
        print("❌ Bitcoin AI test failed!")
        sys.exit(1)
EOF

chmod +x test-bitcoin-ai.py

# Run test
echo "🧪 Running Bitcoin AI test..."
python3 test-bitcoin-ai.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Bitcoin AI setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Ensure your .env file has VENICE_KEY and GROK_KEY"
    echo "2. Start the server: npm start"
    echo "3. Test the AR experience with voice interaction"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "- If Python imports fail, check your PATH includes ~/.local/bin"
    echo "- If API calls fail, verify your API keys in .env"
    echo "- Check the server logs for detailed error messages"
    echo ""
    echo "₿ Happy Bitcoin evangelizing with your Orange!"
else
    echo ""
    echo "❌ Bitcoin AI setup failed!"
    echo "Please check the error messages above and try again."
    echo ""
    echo "Common issues:"
    echo "- Missing API keys in .env file"
    echo "- Python packages not installed correctly"
    echo "- Network connectivity issues"
fi
