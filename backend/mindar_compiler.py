"""
MindAR Target Image Compiler
Compiles regular images (JPG, PNG) to MindAR .mind target files.
Uses Node.js with the MindAR Core API (same compiler as the web tool at 
https://hiukim.github.io/mind-ar-js-doc/tools/compile).

Reference: https://hiukim.github.io/mind-ar-js-doc/core-api
"""

import os
import sys
import subprocess
import logging
import tempfile
import shutil
import json
from pathlib import Path

logger = logging.getLogger(__name__)

def check_node_available():
    """Check if Node.js is available on the system."""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            logger.info(f"✅ Node.js available: {version}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.warning(f"⚠️ Node.js not available: {e}")
    return False

def check_mindar_available():
    """Check if mind-ar npm package is available."""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        node_modules = os.path.join(project_root, 'node_modules', 'mind-ar')
        
        if os.path.exists(node_modules):
            logger.info("✅ mind-ar package found in node_modules")
            # Also check if canvas is available (required by compile_target.js)
            canvas_modules = os.path.join(project_root, 'node_modules', 'canvas')
            if not os.path.exists(canvas_modules):
                logger.warning("⚠️ canvas package not found (required for compilation)")
                return False
            return True
        
        # Check global installation
        result = subprocess.run(['npm', 'list', '-g', 'mind-ar'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and 'mind-ar' in result.stdout:
            logger.info("✅ mind-ar package found globally")
            # Check for canvas globally
            canvas_result = subprocess.run(['npm', 'list', '-g', 'canvas'], capture_output=True, text=True, timeout=5)
            if canvas_result.returncode != 0 or 'canvas' not in canvas_result.stdout:
                logger.warning("⚠️ canvas package not found globally (required for compilation)")
                return False
            return True
    except Exception as e:
        logger.debug(f"mind-ar check: {e}")
    return False

def install_mindar():
    """Install mind-ar and canvas npm packages."""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        logger.info("📦 Installing mind-ar and canvas packages...")
        
        # Install both mind-ar and canvas (canvas is required by compile_target.js)
        packages = ['mind-ar', 'canvas']
        for package in packages:
            logger.info(f"📦 Installing {package}...")
            result = subprocess.run(
                ['npm', 'install', package, '--save'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=300  # canvas can take a while to build
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {package} installed successfully")
            else:
                logger.error(f"❌ Failed to install {package}: {result.stderr}")
                if package == 'canvas':
                    logger.warning("⚠️ canvas installation failed. This may require system dependencies.")
                    logger.warning("   On Ubuntu/Debian: sudo apt-get install build-essential libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev")
                return False
        
        logger.info("✅ All packages installed successfully")
        return True
    except subprocess.TimeoutExpired:
        logger.error("❌ npm install timed out")
        return False
    except FileNotFoundError:
        logger.error("❌ npm not found. Please install Node.js and npm")
        return False
    except Exception as e:
        logger.error(f"❌ Error installing mind-ar: {e}")
        return False

def compile_image_to_mind(image_path, output_path=None):
    """
    Compile an image file to MindAR .mind target file.
    Uses Node.js with MindAR Core API (same compiler as the web tool at 
    https://hiukim.github.io/mind-ar-js-doc/tools/compile).
    
    Reference: https://hiukim.github.io/mind-ar-js-doc/core-api
    
    Args:
        image_path: Path to input image (JPG, PNG, etc.)
        output_path: Path for output .mind file (optional, defaults to same name as input)
        
    Returns:
        Path to compiled .mind file, or None if compilation failed
    """
    try:
        # Check if Node.js is available
        if not check_node_available():
            raise RuntimeError(
                "Node.js is not available. Please install Node.js to compile AR targets.\n"
                "Install: https://nodejs.org/\n"
                "Then run: npm install mind-ar"
            )
        
        # Check/install mind-ar package
        if not check_mindar_available():
            logger.info("📦 mind-ar package not found, installing...")
            if not install_mindar():
                raise RuntimeError(
                    "Failed to install mind-ar package. Please install manually:\n"
                    "npm install mind-ar\n"
                    "Or globally: npm install -g mind-ar"
                )
        
        # Validate input file
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        if not os.path.isfile(image_path):
            raise ValueError(f"Path is not a file: {image_path}")
        
        # Check file extension
        ext = os.path.splitext(image_path)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            raise ValueError(f"Unsupported image format: {ext}. Supported: JPG, PNG, WEBP")
        
        # Determine output path
        if output_path is None:
            output_path = os.path.splitext(image_path)[0] + '.mind'
        elif not output_path.endswith('.mind'):
            output_path = output_path + '.mind'
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Compile image to .mind file using MindAR Core API via Node.js
        logger.info(f"🔄 Compiling {image_path} to {output_path}...")
        logger.info(f"   Using MindAR Core API (same as web tool at https://hiukim.github.io/mind-ar-js-doc/tools/compile)")
        
        # Use the Node.js compilation script
        # Reference: https://hiukim.github.io/mind-ar-js-doc/core-api
        # Web Compiler: https://hiukim.github.io/mind-ar-js-doc/tools/compile
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        compile_script = os.path.join(project_root, 'backend', 'compile_target.js')
        
        # Ensure the script exists (it should be created during installation)
        if not os.path.exists(compile_script):
            logger.error(f"❌ Compilation script not found: {compile_script}")
            logger.error("   Please ensure the backend/compile_target.js file exists")
            logger.error("   This file should be created automatically during installation")
            logger.error("   This file should be created automatically during installation")
            return None
        
        # Run the compilation script
        # Note: Compilation can take 60-180 seconds depending on image size and complexity
        # Puppeteer needs time to: load page, upload file, compile (30-60s), download file
        cmd = ['node', compile_script, image_path, output_path]
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes - compilation can take 60-120 seconds, plus overhead
        )
        
        if result.returncode == 0 and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"✅ Successfully compiled .mind file: {output_path} ({file_size} bytes)")
            return output_path
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            logger.error(f"❌ Compilation failed (returncode={result.returncode})")
            logger.error(f"   stderr: {result.stderr}")
            logger.error(f"   stdout: {result.stdout}")
            logger.error(f"   Command: {' '.join(cmd)}")
            
            # Check for common error patterns and provide helpful hints
            error_lower = error_msg.lower()
            hint = ""
            if "cannot find module 'canvas'" in error_lower or "require('canvas')" in error_lower or "cannot find module \"canvas\"" in error_lower:
                hint = "\n\n💡 Hint: The 'canvas' package is missing. Install it with:\n   npm install canvas\n\n   If installation fails, you may need system dependencies:\n   sudo apt-get install -y libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev libpixman-1-dev\n\n   Then reinstall canvas: npm install canvas"
            elif "cannot find module 'mind-ar'" in error_lower or "cannot find module \"mind-ar\"" in error_lower:
                hint = "\n\n💡 Hint: The 'mind-ar' package is missing. Install it with:\n   npm install mind-ar"
            elif "node" in error_lower and ("not found" in error_lower or "command not found" in error_lower):
                hint = "\n\n💡 Hint: Node.js is not installed or not in PATH. Install from: https://nodejs.org/"
            elif "error: cannot find module" in error_lower or "error: cannot resolve" in error_lower:
                # Generic module not found error
                if "canvas" in error_lower:
                    hint = "\n\n💡 Hint: The 'canvas' package is missing. Install it with:\n   npm install canvas\n\n   If installation fails, install system dependencies first:\n   sudo apt-get install -y libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev libpixman-1-dev"
                elif "mind-ar" in error_lower:
                    hint = "\n\n💡 Hint: The 'mind-ar' package is missing. Install it with:\n   npm install mind-ar"
            
            # Raise an exception with the error message so it can be caught and returned to frontend
            raise RuntimeError(f"Compilation failed: {error_msg}{hint}")
            
    except RuntimeError as e:
        # Re-raise runtime errors (like missing package) as-is
        logger.error(f"❌ {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Error compiling image to .mind: {e}")
        logger.error(f"   Traceback: {sys.exc_info()}")
        return None

def validate_image_for_ar(image_path):
    """
    Validate that an image is suitable for AR target compilation.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Tuple (is_valid, message)
    """
    try:
        from PIL import Image  # type: ignore[reportMissingImports]
        
        # Check file exists
        if not os.path.exists(image_path):
            return False, "Image file not found"
        
        # Open and check image
        with Image.open(image_path) as img:
            width, height = img.size
            
            # Check dimensions (should be reasonable for AR)
            if width < 100 or height < 100:
                return False, f"Image too small ({width}x{height}). Minimum 100x100 pixels recommended."
            
            if width > 5000 or height > 5000:
                return False, f"Image too large ({width}x{height}). Maximum 5000x5000 pixels recommended."
            
            # Check aspect ratio (should be roughly square for best results)
            aspect_ratio = width / height
            if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                return False, f"Image aspect ratio ({aspect_ratio:.2f}) may not work well. Square images (1:1) work best."
            
            # Check if image has enough contrast (basic check)
            # Convert to grayscale for contrast analysis
            gray = img.convert('L')
            pixels = list(gray.getdata())
            min_brightness = min(pixels)
            max_brightness = max(pixels)
            contrast_range = max_brightness - min_brightness
            
            if contrast_range < 50:
                return False, "Image has low contrast. High-contrast images work better for AR tracking."
            
            return True, f"Image is suitable ({width}x{height}, contrast: {contrast_range})"
            
    except ImportError:
        # PIL not available, skip validation
        logger.warning("⚠️ PIL/Pillow not available, skipping image validation")
        return True, "Image validation skipped (PIL not available)"
    except Exception as e:
        logger.warning(f"⚠️ Image validation error: {e}")
        return True, "Image validation skipped"

