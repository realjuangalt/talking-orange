# AR Target Image Compilation

## Overview

The system now automatically compiles regular image files (JPG, PNG, WEBP) to MindAR `.mind` target files when users upload target images. Users no longer need to know about `.mind` files - they just upload an image and the system handles the conversion.

## How It Works

1. **User uploads an image** via the user home page (`user.html`)
2. **Backend validates the image** (size, contrast, aspect ratio)
3. **Backend compiles the image** to a `.mind` file using the MindAR compiler
4. **Both files are saved**:
   - Original image: `target_image_<timestamp>_<filename>`
   - Compiled target: `target_<timestamp>.mind`

## Requirements

### Python Dependencies
The compilation uses the Python `mindar` package, which provides the same compiler as the web tool at [http://hiukim.github.io/mind-ar-js-doc/quick-start/compile](http://hiukim.github.io/mind-ar-js-doc/quick-start/compile).

Required packages:
- `mindar>=0.1.0` - MindAR compiler (same as web compiler)
- `Pillow>=9.0.0` - For image validation (optional but recommended)

**No Node.js required!** The Python package provides the same functionality as the web compiler.

## Installation

Run the install script which will:
1. Install Python dependencies including `mindar` and `Pillow`
2. Set up the virtual environment

```bash
./install.sh
```

The install script automatically installs all required Python packages from `requirements-python.txt`.

## Manual Installation

If you prefer to install manually:

```bash
# Activate virtual environment
source venv/bin/activate

# Install MindAR compiler and dependencies
pip install mindar Pillow
```

## Usage

### For Users

1. Go to the user home page (`/user.html`)
2. Upload an image in the "AR Target Image" section
3. The system will:
   - Validate the image (check size, contrast, etc.)
   - Compile it to a `.mind` file automatically
   - Show a success message when done

### Image Requirements

- **Format**: JPG, PNG, or WEBP
- **Size**: 100x100 to 5000x5000 pixels
- **Aspect Ratio**: Square (1:1) works best, but 0.5:1 to 2:1 is acceptable
- **Contrast**: High contrast images work better (black/white or bold colors)

### For Developers

The compilation is handled by `backend/mindar_compiler.py`:

```python
from mindar_compiler import compile_image_to_mind, validate_image_for_ar

# Validate image
is_valid, message = validate_image_for_ar('path/to/image.jpg')
if not is_valid:
    print(f"Image not suitable: {message}")

# Compile to .mind
mind_file = compile_image_to_mind('path/to/image.jpg', 'output.mind')
if mind_file:
    print(f"Compiled successfully: {mind_file}")
```

## API Endpoint

The upload endpoint (`POST /api/users/upload`) automatically handles compilation:

**Request:**
```
POST /api/users/upload
Content-Type: multipart/form-data

file: <image file>
fileType: target
userId: <user_id>
```

**Response (Success):**
```json
{
  "success": true,
  "filename": "target_1234567890.mind",
  "originalImage": "target_image_1234567890_myimage.jpg",
  "size": 12345,
  "fileType": "target",
  "url": "/api/users/<user_id>/media/target_1234567890.mind",
  "message": "Target image compiled successfully. Your AR marker is ready to use!"
}
```

**Response (Error):**
```json
{
  "error": "Image not suitable for AR: Image has low contrast...",
  "validation": "Image has low contrast. High-contrast images work better for AR tracking."
}
```

## Troubleshooting

### "mindar package not available"
- Install the package: `pip install mindar`
- Make sure you're in the virtual environment: `source venv/bin/activate`
- Reinstall requirements: `pip install -r requirements-python.txt`

### "Failed to compile image to AR target"
- Check mindar is installed: `python -c "from mindar.compiler import MindARCompiler; print('OK')"`
- Check Python version (requires 3.9+): `python --version`
- Reinstall: `pip install --upgrade mindar`

### "Image not suitable for AR"
- Use higher contrast images (black/white or bold colors)
- Ensure image is at least 100x100 pixels
- Try a square image (1:1 aspect ratio)

## Technical Details

### Compiler Module

The `mindar_compiler.py` module:
- Uses the Python `mindar` package (same as web compiler)
- Validates images before compilation
- Compiles images using `MindARCompiler.compile_directory()`
- Returns compiled `.mind` file path or error

### Compiler Details

The system uses the official MindAR Python package:
- **Package**: `mindar` (available on PyPI)
- **Same compiler**: As the web tool at http://hiukim.github.io/mind-ar-js-doc/quick-start/compile
- **No Node.js needed**: Pure Python implementation

### Image Validation

Validation checks:
- File exists and is readable
- Dimensions (100-5000 pixels)
- Aspect ratio (0.5:1 to 2:1)
- Contrast range (minimum 50)

## Future Improvements

- [ ] Support for PDF input (convert to image first)
- [ ] Batch compilation (multiple images at once)
- [ ] Preview of compiled target
- [ ] Compression optimization
- [ ] Web-based compiler fallback if Node.js unavailable

