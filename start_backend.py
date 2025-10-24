#!/usr/bin/env python3
"""
Startup script for Talking Orange Python Backend
Handles environment setup and starts the Flask server.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8 or higher is required")
        sys.exit(1)
    logger.info(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def check_environment():
    """Check if required environment variables are set."""
    required_vars = ['VENICE_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these in your .env file")
        sys.exit(1)
    
    logger.info("✅ Environment variables configured")

def install_dependencies():
    """Install Python dependencies."""
    try:
        logger.info("🔧 Installing Python dependencies...")
        
        # Install backend dependencies
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'backend/requirements.txt'], 
                      check=True, capture_output=True)
        
        # Install gen system dependencies
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'gen/requirements-python.txt'], 
                      check=True, capture_output=True)
        
        logger.info("✅ Dependencies installed successfully")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def create_directories():
    """Create necessary directories."""
    directories = [
        'public/audio',
        'frontend',
        'gen/prompts',
        'gen/voices'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Created directory: {directory}")

def start_server():
    """Start the Flask server."""
    try:
        logger.info("🚀 Starting Talking Orange Python Backend...")
        
        # Change to backend directory and start Flask app
        os.chdir('backend')
        subprocess.run([sys.executable, 'app.py'], check=True)
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Server failed to start: {e}")
        sys.exit(1)

def main():
    """Main startup function."""
    logger.info("🍊 Talking Orange Python Backend Startup")
    logger.info("=" * 50)
    
    # Check system requirements
    check_python_version()
    check_environment()
    
    # Setup
    create_directories()
    install_dependencies()
    
    # Start server
    start_server()

if __name__ == '__main__':
    main()
