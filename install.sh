#!/bin/bash

# Talking Orange AR Project - Installation Script
# This script installs all required dependencies for local development

echo "🍊 Talking Orange AR Project - Installation Script"
echo "=================================================="

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ This script is designed for Linux systems"
    exit 1
fi

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    curl \
    wget \
    git \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    sqlite3 \
    imagemagick \
    libmagick++-dev \
    ffmpeg \
    libasound2-dev \
    nginx

# Install Node.js (LTS version)
echo "📦 Installing Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt-get install -y nodejs
else
    echo "✅ Node.js already installed"
fi

# Install Blender (via snap)
echo "🎨 Installing Blender..."
if ! command -v blender &> /dev/null; then
    sudo snap install blender --classic
else
    echo "✅ Blender already installed"
fi

# Install project dependencies
echo "📦 Installing project dependencies..."
npm install

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p uploads
mkdir -p frontend/assets
mkdir -p 3d-assets

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
echo "Node.js version: $(node --version)"
echo "npm version: $(npm --version)"
echo "Python version: $(python3 --version)"

# Test server startup
echo "🚀 Testing server startup..."
if npm run start &> /dev/null & then
    SERVER_PID=$!
    sleep 2
    if curl -s http://localhost:3000/api/health > /dev/null; then
        echo "✅ Server started successfully"
        kill $SERVER_PID
    else
        echo "❌ Server failed to start"
        kill $SERVER_PID
        exit 1
    fi
else
    echo "❌ Failed to start server"
    exit 1
fi

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Run 'npm start' to start the development server"
echo "2. Open http://localhost:3000 in your browser"
echo "3. Use your mobile device to test the AR experience"
echo ""
echo "🔧 Development commands:"
echo "- npm start          # Start the server"
echo "- npm run dev        # Start with auto-reload"
echo "- npm run build      # Build the project"
echo ""
echo "📱 Testing:"
echo "- Use a mobile device with camera"
echo "- Point at the AR marker (Hiro pattern)"
echo "- Grant camera and microphone permissions"
echo "- Ask questions about Bitcoin!"
echo ""
echo "🍊 Happy coding with Talking Orange!"
