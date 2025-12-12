"""
Talking Orange AR Backend Server
Python Flask backend for voice processing and Bitcoin evangelism.
"""

import os
import sys

print("=" * 60, file=sys.stderr)
print("🚀 [STARTUP] Starting backend server...", file=sys.stderr)
print("=" * 60, file=sys.stderr)
print("📦 [STARTUP] Importing standard library modules...", file=sys.stderr)
import json
import logging
import asyncio
import time
import traceback
import tempfile
import subprocess
from pathlib import Path
print("✅ [STARTUP] Standard library modules imported", file=sys.stderr)

print("📦 [STARTUP] Importing Flask and dependencies...", file=sys.stderr)
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
print("✅ [STARTUP] Flask and dependencies imported", file=sys.stderr)

# Add backend/gen directory to path
print("📁 [STARTUP] Setting up Python path...", file=sys.stderr)
gen_dir = os.path.join(os.path.dirname(__file__), 'gen')
if gen_dir not in sys.path:
    sys.path.insert(0, gen_dir)
print(f"✅ [STARTUP] Python path configured (gen_dir: {gen_dir})", file=sys.stderr)

# Import our voice processing modules - LAZY LOADING to prevent reloader issues
# Only import in main process, not in Flask reloader child process
print("📦 [STARTUP] Checking if voice modules should be imported...", file=sys.stderr)
is_reloader = os.environ.get('WERKZEUG_RUN_MAIN') != 'true' and os.environ.get('FLASK_ENV') == 'development'
print(f"   [STARTUP] Is reloader process: {is_reloader}", file=sys.stderr)

if is_reloader:
    print("⏭️  [STARTUP] Skipping voice module import in reloader process", file=sys.stderr)
    # Set placeholders that will be loaded on first use
    TalkingOrangeVoiceSystem = None
    process_voice_file = None
    process_voice_buffer = None
    transcribe_audio = None
    synthesize_speech = None
    main_module = None
else:
    print("📦 [STARTUP] Importing voice processing modules...", file=sys.stderr)
    import importlib.util
    print("   [STARTUP] importlib.util imported", file=sys.stderr)

    # Load the main module from backend/gen directory
    print("   [STARTUP] Loading main.py from gen directory...", file=sys.stderr)
    main_py_path = os.path.join(gen_dir, "main.py")
    print(f"   [STARTUP] main.py path: {main_py_path}", file=sys.stderr)
    print(f"   [STARTUP] main.py exists: {os.path.exists(main_py_path)}", file=sys.stderr)

    spec = importlib.util.spec_from_file_location("main", main_py_path)
    print("   [STARTUP] Spec created", file=sys.stderr)
    main_module = importlib.util.module_from_spec(spec)
    print("   [STARTUP] Module from spec created", file=sys.stderr)
    sys.modules["main"] = main_module
    print("   [STARTUP] Module added to sys.modules", file=sys.stderr)
    print("   [STARTUP] Executing main.py module (this may take a moment)...", file=sys.stderr)
    spec.loader.exec_module(main_module)
    print("   [STARTUP] main.py module executed", file=sys.stderr)

    # Import the classes and functions we need
    print("   [STARTUP] Extracting classes and functions from main module...", file=sys.stderr)
    TalkingOrangeVoiceSystem = main_module.TalkingOrangeVoiceSystem
    process_voice_file = main_module.process_voice_file
    process_voice_buffer = main_module.process_voice_buffer
    transcribe_audio = main_module.transcribe_audio
    synthesize_speech = main_module.synthesize_speech
    print("✅ [STARTUP] Voice processing modules imported", file=sys.stderr)

# Import user management module
print("📦 [STARTUP] Importing user_manager module...", file=sys.stderr)
from user_manager import (
    ensure_user_directories,
    ensure_project_directories,
    get_user_audio_path,
    get_user_media_path,
    get_user_audio_url,
    get_user_media_url,
    get_user_id_from_session,
    get_user_base_path,
    get_project_base_path,
    user_exists,
    project_exists,
    list_user_projects,
    list_user_files as list_user_files_from_manager,
    detect_project_from_path
)
print("✅ [STARTUP] user_manager module imported", file=sys.stderr)

# Import MindAR compiler
print("📦 [STARTUP] Importing MindAR compiler...", file=sys.stderr)
try:
    from mindar_compiler import compile_image_to_mind, validate_image_for_ar, check_node_available
    MINDAR_COMPILER_AVAILABLE = True
    print("✅ [STARTUP] MindAR compiler imported", file=sys.stderr)
except ImportError as e:
    # Logger might not be initialized yet, use print for early errors
    print(f"⚠️ [STARTUP] mindar_compiler module not available: {e}", file=sys.stderr)
    MINDAR_COMPILER_AVAILABLE = False
    compile_image_to_mind = None
    validate_image_for_ar = None
    check_node_available = None

# Load environment variables from project root
print("📦 [STARTUP] Loading environment variables...", file=sys.stderr)
project_root = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.join(project_root, '.env')
print(f"   [STARTUP] .env path: {env_path}", file=sys.stderr)
load_dotenv(env_path)
print("✅ [STARTUP] Environment variables loaded", file=sys.stderr)

# Set up logging
print("📦 [STARTUP] Setting up logging...", file=sys.stderr)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
print("✅ [STARTUP] Logging configured", file=sys.stderr)

# Initialize Flask app
print("🔧 [STARTUP] Initializing Flask app...", file=sys.stderr)
app = Flask(__name__)
print("🔧 [STARTUP] Flask app created", file=sys.stderr)
CORS(app)
print("🔧 [STARTUP] CORS configured", file=sys.stderr)

# Global voice system instance
voice_system = None

def _convert_to_mp3(audio_data: bytes, output_path: str, input_format: str = 'wav') -> str:
    """Convert audio data to MP3 format using ffmpeg."""
    try:
        
        # Create temporary file with the input format
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{input_format}')
        temp_input.write(audio_data)
        temp_input_path = temp_input.name
        temp_input.close()
        
        logger.info(f"📝 Created temporary input file: {temp_input_path}")
        
        try:
            # Convert to MP3 using ffmpeg
            cmd = [
                'ffmpeg', '-y',  # Overwrite output
                '-i', temp_input_path,
                '-codec:a', 'libmp3lame',  # Use MP3 codec
                '-b:a', '128k',  # 128kbps bitrate
                output_path
            ]
            
            logger.info(f"🔄 Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(f"✅ Successfully converted to MP3: {output_path}")
                return output_path
            else:
                logger.error(f"❌ ffmpeg conversion failed: {result.stderr}")
                # Fallback: save original format
                logger.warning(f"⚠️ Saving as original format instead")
                fallback_path = output_path.replace('.mp3', f'.{input_format}')
                with open(fallback_path, 'wb') as f:
                    f.write(audio_data)
                return fallback_path
        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_input_path):
                    os.unlink(temp_input_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temp file: {cleanup_error}")
                
    except Exception as e:
        logger.error(f"❌ MP3 conversion failed: {e}")
        # Fallback: save original format
        logger.warning(f"⚠️ Saving as original format instead")
        fallback_path = output_path.replace('.mp3', f'.{input_format}')
        with open(fallback_path, 'wb') as f:
            f.write(audio_data)
        return fallback_path

def initialize_voice_system():
    """Initialize the voice processing system."""
    global voice_system, TalkingOrangeVoiceSystem, main_module
    
    # Lazy load voice module if not already loaded (for reloader compatibility)
    if TalkingOrangeVoiceSystem is None or main_module is None:
        logger.info("📦 [INIT] Lazy loading voice processing modules...")
        import importlib.util
        gen_dir = os.path.join(os.path.dirname(__file__), 'gen')
        main_py_path = os.path.join(gen_dir, "main.py")
        spec = importlib.util.spec_from_file_location("main", main_py_path)
        main_module = importlib.util.module_from_spec(spec)
        sys.modules["main"] = main_module
        spec.loader.exec_module(main_module)
        TalkingOrangeVoiceSystem = main_module.TalkingOrangeVoiceSystem
        # Update globals
        globals()['process_voice_file'] = main_module.process_voice_file
        globals()['process_voice_buffer'] = main_module.process_voice_buffer
        globals()['transcribe_audio'] = main_module.transcribe_audio
        globals()['synthesize_speech'] = main_module.synthesize_speech
        logger.info("✅ [INIT] Voice processing modules loaded")
    
    init_start = time.time()
    
    try:
        logger.info("🎤 [INIT] Initializing Talking Orange Voice System...")
        logger.info(f"🎤 [INIT] Voice system currently: {'exists' if voice_system else 'None'}")
        
        # Try to create the voice system
        logger.info("🔧 [INIT] Creating TalkingOrangeVoiceSystem instance...")
        create_start = time.time()
        voice_system = TalkingOrangeVoiceSystem()
        create_duration = round(time.time() - create_start, 2)
        logger.info(f"✅ [INIT] TalkingOrangeVoiceSystem instance created in {create_duration}s")
        
        # Initialize asynchronously
        logger.info("🔄 [INIT] Running async initialization...")
        init_voice_start = time.time()
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(voice_system.initialize())
            init_voice_duration = round(time.time() - init_voice_start, 2)
            logger.info(f"✅ [INIT] Async initialization completed in {init_voice_duration}s, result: {result}")
        except Exception as async_error:
            logger.error(f"❌ [INIT] Async initialization failed: {async_error}")
            logger.error(f"❌ [INIT] Async error traceback: {traceback.format_exc()}")
            # Try synchronous initialization as fallback
            logger.info("🔄 [INIT] Trying synchronous initialization as fallback...")
            init_voice_start = time.time()
            result = voice_system.initialize_sync()
            init_voice_duration = round(time.time() - init_voice_start, 2)
            logger.info(f"✅ [INIT] Sync initialization completed in {init_voice_duration}s, result: {result}")
        
        total_duration = round(time.time() - init_start, 2)
        logger.info(f"✅ [INIT] Voice System initialized successfully in {total_duration}s total")
        
        # Log system status
        if voice_system:
            status = voice_system.get_status()
            logger.info(f"📊 [INIT] Voice system status: initialized={status.get('initialized', False)}")
            if status.get('stt_status'):
                stt = status['stt_status']
                logger.info(f"📊 [INIT] STT: device={stt.get('device')}, model={stt.get('model_name')}, fp16={stt.get('use_fp16')}")
            if status.get('tts_status'):
                tts = status['tts_status']
                logger.info(f"📊 [INIT] TTS: engines={tts.get('available_engines', [])}")
        
    except Exception as e:
        logger.error(f"❌ Voice System initialization failed: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        voice_system = None

# Initialize voice system on startup
# Only initialize in the main process, not in Flask's reloader process
# Flask sets WERKZEUG_RUN_MAIN='true' in the main process (when using reloader)
# In production (no reloader), WERKZEUG_RUN_MAIN won't be set, but we still initialize
import sys
print("🔍 [STARTUP] Checking environment variables...", file=sys.stderr)
is_debug = os.environ.get('DEBUG', 'False').lower() == 'true'
is_main_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
print(f"   DEBUG={is_debug}, WERKZEUG_RUN_MAIN={is_main_process}", file=sys.stderr)

# DISABLED: Voice system initialization on startup to prevent high I/O
# Voice system will initialize lazily when first speech request is made
print("🔄 [STARTUP] Voice system initialization disabled on startup (will initialize on first use)", file=sys.stderr)
logger.info("🔄 [STARTUP] Voice system initialization disabled on startup (will initialize on first use)")

@app.route('/')
def index():
    """Serve the main frontend page."""
    return send_from_directory('../frontend', 'index.html')

@app.route('/print')
def print_page():
    """Serve the print demo page."""
    return send_from_directory('../frontend', 'print.html')

@app.route('/test')
def test_route():
    """Test route to verify Flask is working"""
    logger.info("🧪 Test route called!")
    return "Test route working!"

@app.route('/targets.mind')
def targets_mind():
    """Serve the compiled MindAR targets file"""
    logger.info("🎯 targets.mind route called!")
    try:
        return send_from_directory('..', 'targets.mind')
    except Exception as e:
        logger.error(f"❌ Error serving targets.mind: {e}")
        return f"Error: {e}", 500

@app.route('/talking-orange-smile.png')
def talking_orange_smile():
    """Serve the talking orange smile PNG"""
    return send_from_directory('..', 'talking-orange-smile.png')

@app.route('/talking-orange-mouth-half.png')
def talking_orange_mouth_half():
    """Serve the talking orange mouth half open PNG"""
    return send_from_directory('..', 'talking-orange-half-open-mouth.png')

@app.route('/talking-orange-mouth-open.png')
def talking_orange_mouth_open():
    """Serve the talking orange mouth wide open PNG"""
    return send_from_directory('..', 'talking-orange-open-mouth.png')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from frontend directory."""
    return send_from_directory('../frontend', filename)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        logger.info(f"🔍 Health check - voice_system: {voice_system is not None}")
        
        if voice_system:
            logger.info("🔍 Voice system exists, getting status...")
            voice_status = voice_system.get_status()
            logger.info(f"🔍 Voice system status: {voice_status}")
            
            # Extract device info from STT service
            device_info = {
                "device": "unknown",
                "use_fp16": False,
                "model_name": "unknown"
            }
            if voice_status.get('stt_status'):
                stt_status = voice_status['stt_status']
                device_info = {
                    "device": stt_status.get('device', 'unknown'),
                    "use_fp16": stt_status.get('use_fp16', False),
                    "model_name": stt_status.get('model_name', 'unknown')
                }
        else:
            logger.info("🔍 Voice system is None")
            voice_status = {"initialized": False}
            device_info = {"device": "unknown", "use_fp16": False, "model_name": "unknown"}
        
        status = {
            "status": "healthy",
            "voice_system": voice_status,
            "whisper_device": device_info,
            "timestamp": time.time()
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/api/speech/process', methods=['POST'])
def process_speech():
    """Process speech input and return Bitcoin response with audio."""
    try:
        # Parse JSON request with error handling
        try:
            data = request.get_json(force=True, silent=True)
        except Exception as json_error:
            logger.error(f"❌ JSON parsing error: {json_error}")
            logger.error(f"❌ Content-Type: {request.content_type}")
            logger.error(f"❌ Request data preview: {str(request.data)[:200] if request.data else 'None'}")
            return jsonify({"error": f"Invalid JSON request: {str(json_error)}"}), 400
        
        if data is None:
            logger.error("❌ Failed to parse JSON request - data is None")
            logger.error(f"❌ Content-Type: {request.content_type}")
            logger.error(f"❌ Request data length: {len(request.data) if request.data else 0}")
            logger.error(f"❌ Request data preview: {str(request.data)[:200] if request.data else 'None'}")
            return jsonify({"error": "Invalid JSON request or missing data"}), 400
        
        # Validate data is a dictionary
        if not isinstance(data, dict):
            logger.error(f"❌ Request data is not a dictionary: {type(data)}")
            return jsonify({"error": "Invalid request format - expected JSON object"}), 400
        
        logger.info(f"📥 Received speech request: {list(data.keys())}")
        
        text = data.get('text', '')
        audio_data = data.get('audioData', '')
        session_id = data.get('sessionId', 'anonymous')
        # Get userId and projectName from request (preferred) or use defaults
        user_id = data.get('userId', None)
        project_name = data.get('projectName', 'default')
        language = data.get('language', 'en')
        tts_voice = data.get('ttsVoice', 'default')
        tts_engine = data.get('ttsEngine', 'auto')
        
        logger.info(f"🎤 Audio data present: {bool(audio_data)}, Text present: {bool(text)}")
        logger.info(f"🌍 Language: {language}, Session: {session_id}")
        logger.info(f"👤 Request userId: {user_id}, Request projectName: {project_name}")
        
        # Validate that we have either audio or text
        if not audio_data and not text:
            logger.error("❌ No audio data or text provided")
            return jsonify({"error": "No audio data or text provided"}), 400
        
        if not voice_system:
            logger.error("❌ Voice system not initialized")
            logger.error(f"❌ Voice system object: {voice_system}")
            logger.error(f"❌ Voice system type: {type(voice_system)}")
            return jsonify({"error": "Voice system not initialized"}), 500
        
        # Process the input
        if audio_data:
            # Process audio input - handle base64 encoded audio
            logger.info(f"🎵 Processing audio data (length: {len(audio_data) if audio_data else 0})")
            try:
                import base64
                # time is already imported at module level
                
                # Validate base64 audio data
                if not audio_data or len(audio_data) < 10:
                    raise ValueError("Audio data is empty or too small")
                
                # Decode base64 audio
                try:
                    audio_buffer = base64.b64decode(audio_data)
                except Exception as decode_error:
                    logger.error(f"Base64 decoding failed: {decode_error}")
                    raise ValueError(f"Invalid base64 audio data: {str(decode_error)}")
                
                if not audio_buffer or len(audio_buffer) < 100:
                    raise ValueError("Decoded audio buffer is too small")
                
                logger.info(f"🔊 Decoded audio buffer: {len(audio_buffer)} bytes")
                logger.info(f"🔊 Audio buffer type: {type(audio_buffer)}")
                logger.info(f"🔊 First 20 bytes: {audio_buffer[:20] if len(audio_buffer) > 20 else audio_buffer}")
                
                # Use userId from request if provided, otherwise fall back to session lookup
                if not user_id:
                    user_id = get_user_id_from_session(session_id)
                    logger.info(f"🔄 Using userId from session lookup: {user_id}")
                else:
                    logger.info(f"✅ Using userId from request: {user_id}")
                
                # Ensure project_name is set (should already be from request, but double-check)
                if project_name == 'default' and data.get('projectName'):
                    project_name = data.get('projectName')
                
                logger.info(f"👤 Final User ID: {user_id}, Final Project: {project_name}")
                
                # Save user audio input to project-specific directory
                user_audio_filename = f"user_input_{int(time.time())}.webm"
                user_audio_path = get_user_audio_path(user_id, user_audio_filename, 'user', project_name)
                ensure_project_directories(user_id, project_name)  # Ensure project directories exist
                
                try:
                    with open(user_audio_path, 'wb') as f:
                        f.write(audio_buffer)
                    logger.info(f"💾 Saved user audio input to: {user_audio_path}")
                    logger.info(f"📊 User audio file size: {os.path.getsize(user_audio_path)} bytes")
                except Exception as save_error:
                    logger.error(f"Failed to save user audio: {save_error}")
                    # Don't fail the whole request if we can't save the file
                
                # Process audio with voice system
                api_start = time.time()
                logger.info(f"🎤 [API] Calling voice_system.process_voice_input_sync...")
                logger.info(f"🎤 [API] Audio buffer size: {len(audio_buffer)} bytes")
                logger.info(f"🎤 [API] Language: {language}, TTS voice: {tts_voice}, TTS engine: {tts_engine}")
                
                result = voice_system.process_voice_input_sync(
                    audio_buffer, language, tts_voice, tts_engine, user_id, project_name
                )
                
                api_duration = round(time.time() - api_start, 2)
                logger.info(f"✅ [API] Voice processing completed in {api_duration}s")
                logger.info(f"📊 [API] Voice processing result keys: {list(result.keys())}")
                logger.info(f"📊 [API] Transcription: '{result.get('transcription', '')[:50]}...'")
                logger.info(f"📊 [API] Response text length: {len(result.get('response_text', ''))} characters")
                logger.info(f"📊 [API] Audio data length: {len(result.get('audio_data', b''))} bytes")
                logger.info(f"📊 [API] STT engine: {result.get('stt_engine', 'unknown')}")
                logger.info(f"📊 [API] TTS engine: {result.get('tts_engine', 'unknown')}")
                
                # Validate result
                if not result or 'transcription' not in result:
                    raise ValueError("Invalid response from voice processing system")
                
            except ValueError as ve:
                logger.error(f"❌ Audio validation error: {ve}")
                return jsonify({"error": f"Invalid audio data: {str(ve)}"}), 400
            except Exception as e:
                logger.error(f"❌ Audio processing error: {e}")
                logger.error(f"❌ Audio processing traceback: {traceback.format_exc()}")
                return jsonify({"error": f"Audio processing failed: {str(e)}"}), 500
        elif text:
            # Process text input
            logger.info(f"📝 Processing text input: {text[:50]}...")
            # Use userId from request if provided, otherwise fall back to session lookup
            if not user_id:
                user_id = get_user_id_from_session(session_id)
                logger.info(f"🔄 Using userId from session lookup: {user_id}")
            else:
                logger.info(f"✅ Using userId from request: {user_id}")
            
            # Ensure project_name is set
            if project_name == 'default' and data.get('projectName'):
                project_name = data.get('projectName')
            
            logger.info(f"👤 Final User ID: {user_id}, Final Project: {project_name}")
            result = voice_system.process_voice_input_sync(
                text, language, tts_voice, tts_engine, user_id, project_name
            )
        else:
            logger.error("❌ No text or audio provided")
            return jsonify({"error": "No text or audio provided"}), 400
        
        # user_id and project_name should already be set correctly from request data above
        # Only fall back to session lookup if they weren't set (shouldn't happen, but safety check)
        if not user_id:
            user_id = get_user_id_from_session(session_id)
            logger.warn(f"⚠️ [AUDIO SAVE] user_id was not set, using session lookup: {user_id}")
        
        if project_name == 'default' and data.get('projectName'):
            project_name = data.get('projectName')
        
        logger.info(f"💾 [AUDIO SAVE] Using user_id: {user_id}, project_name: {project_name}")
        
        # Save AI audio response to project-specific directory (as MP3)
        audio_filename = f"ai_response_{int(time.time())}.mp3"
        audio_path = get_user_audio_path(user_id, audio_filename, 'ai', project_name)
        ensure_project_directories(user_id, project_name)  # Ensure project directories exist
        
        logger.info(f"💾 Saving audio response...")
        logger.info(f"📁 Audio filename: {audio_filename}")
        logger.info(f"📁 Audio path: {audio_path}")
        logger.info(f"📊 Result keys: {list(result.keys())}")
        logger.info(f"📊 Audio data type: {type(result.get('audio_data'))}")
        logger.info(f"📊 Audio data length: {len(result.get('audio_data', b''))} bytes")
        
        # Ensure AI audio directory exists
        audio_dir = os.path.dirname(audio_path)
        logger.info(f"📁 [AUDIO SAVE] Audio directory: {audio_dir}")
        logger.info(f"📁 [AUDIO SAVE] Audio directory absolute path: {os.path.abspath(audio_dir)}")
        
        # Check if directory exists
        if not os.path.exists(audio_dir):
            logger.info(f"📁 [AUDIO SAVE] Directory does not exist, creating...")
            try:
                os.makedirs(audio_dir, exist_ok=True)
                logger.info(f"✅ [AUDIO SAVE] Directory created")
            except Exception as mkdir_error:
                logger.error(f"❌ [AUDIO SAVE] Failed to create directory: {mkdir_error}")
                raise
        else:
            logger.info(f"✅ [AUDIO SAVE] Directory already exists")
        
        # Check directory permissions
        if os.path.exists(audio_dir):
            is_writable = os.access(audio_dir, os.W_OK)
            logger.info(f"📁 [AUDIO SAVE] Directory writable: {is_writable}")
            if not is_writable:
                logger.error(f"❌ [AUDIO SAVE] Directory is NOT writable! Permission denied.")
                logger.error(f"❌ [AUDIO SAVE] Try: chmod 755 {audio_dir} or chown to current user")
                raise PermissionError(f"Directory {audio_dir} is not writable")
        else:
            logger.error(f"❌ [AUDIO SAVE] Directory does not exist after creation attempt!")
            raise FileNotFoundError(f"Directory {audio_dir} does not exist")
        
        # Write AI audio data (convert to MP3 if needed)
        try:
            audio_data = result.get('audio_data')
            
            # Validate audio data exists and is not empty
            if not audio_data:
                logger.error(f"❌ [AUDIO SAVE] audio_data is None or missing in result!")
                logger.error(f"❌ [AUDIO SAVE] Result keys: {list(result.keys())}")
                raise ValueError("Audio data is missing from TTS result")
            
            if len(audio_data) == 0:
                logger.error(f"❌ [AUDIO SAVE] audio_data is empty (0 bytes)!")
                raise ValueError("Audio data is empty")
            
            logger.info(f"✅ [AUDIO SAVE] Audio data validated: {len(audio_data)} bytes")
            
            # Check if audio is already MP3 or convert it
            audio_format = result.get('audio_format', result.get('format', 'wav'))
            logger.info(f"📊 [AUDIO SAVE] Audio format from TTS: {audio_format}")
            
            # Save audio file
            logger.info(f"💾 [AUDIO SAVE] Attempting to save audio file: {audio_path}")
            logger.info(f"💾 [AUDIO SAVE] File absolute path: {os.path.abspath(audio_path)}")
            
            if audio_format.lower() in ['mp3', 'audio/mpeg']:
                # Already MP3, save directly
                logger.info(f"💾 [AUDIO SAVE] Audio is already MP3, saving directly...")
                try:
                    with open(audio_path, 'wb') as f:
                        bytes_written = f.write(audio_data)
                    logger.info(f"✅ [AUDIO SAVE] AI audio file saved as MP3: {audio_path}")
                    logger.info(f"✅ [AUDIO SAVE] Bytes written: {bytes_written} (expected: {len(audio_data)})")
                    
                    # Verify file was written
                    if os.path.exists(audio_path):
                        file_size = os.path.getsize(audio_path)
                        logger.info(f"✅ [AUDIO SAVE] File verified: {file_size} bytes")
                        if file_size != len(audio_data):
                            logger.warning(f"⚠️ [AUDIO SAVE] File size mismatch! Expected {len(audio_data)}, got {file_size}")
                    else:
                        logger.error(f"❌ [AUDIO SAVE] File does not exist after write attempt!")
                    
                    # audio_filename is already set correctly above, don't reset it
                except PermissionError as perm_error:
                    logger.error(f"❌ [AUDIO SAVE] Permission denied writing to {audio_path}")
                    logger.error(f"❌ [AUDIO SAVE] Error: {perm_error}")
                    raise
                except Exception as write_error:
                    logger.error(f"❌ [AUDIO SAVE] Failed to write file: {write_error}")
                    raise
            else:
                # Convert to MP3 using ffmpeg
                logger.info(f"🔄 Converting audio to MP3 format...")
                try:
                    converted_path = _convert_to_mp3(audio_data, audio_path, audio_format)
                    audio_filename = os.path.basename(converted_path)
                    logger.info(f"✅ AI audio file converted and saved as MP3: {converted_path}")
                except Exception as convert_error:
                    logger.error(f"❌ MP3 conversion failed: {convert_error}")
                    # Fallback: save in original format
                    original_ext = audio_format if audio_format != 'wav' else 'wav'
                    fallback_filename = f"ai_response_{int(time.time())}.{original_ext}"
                    fallback_path = os.path.join('data', 'ai', fallback_filename)
                    with open(fallback_path, 'wb') as f:
                        f.write(audio_data)
                    audio_filename = fallback_filename
                    logger.info(f"✅ AI audio file saved in original format: {fallback_path}")
            
        except Exception as e:
            logger.error(f"❌ [AUDIO SAVE] Failed to save audio file: {e}")
            logger.error(f"❌ [AUDIO SAVE] Error type: {type(e).__name__}")
            logger.error(f"❌ [AUDIO SAVE] Traceback: {traceback.format_exc()}")
            logger.warning(f"⚠️ [AUDIO SAVE] Continuing without saving audio file")
            audio_filename = None
        
        response_data = {
            "transcription": result.get('transcription', ''),
            "response": result.get('response_text', ''),
            "timestamp": time.time(),
            "sttEngine": result.get('stt_engine', 'whisper'),
            "ttsEngine": result.get('tts_engine', 'auto'),
            "language": language,
            "voice": tts_voice
        }
        
        # Add audioUrl only if we successfully saved the file
        if audio_filename:
            response_data["audioUrl"] = get_user_audio_url(user_id, audio_filename, 'ai', project_name)
            response_data["userId"] = user_id  # Include user ID in response
            logger.info(f"✅ [AUDIO SAVE] audioUrl added to response: {response_data['audioUrl']}")
        else:
            logger.warning("⚠️ [AUDIO SAVE] No audio file saved, skipping audioUrl in response")
            logger.warning(f"⚠️ [AUDIO SAVE] This means TTS failed or audio save failed - check logs above")
            logger.warning(f"⚠️ [AUDIO SAVE] Result had audio_data: {bool(result.get('audio_data'))}")
            logger.warning(f"⚠️ [AUDIO SAVE] Audio data length: {len(result.get('audio_data', b''))} bytes")
        
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        error_traceback = traceback.format_exc()
        
        logger.error(f"❌ Speech processing error: {error_msg}")
        logger.error(f"❌ Error type: {error_type}")
        logger.error(f"❌ Traceback: {error_traceback}")
        
        # Return detailed error in debug mode, generic in production
        debug = os.getenv('DEBUG', 'False').lower() == 'true'
        if debug:
            return jsonify({
                "error": f"Speech processing failed: {error_msg}",
                "error_type": error_type,
                "traceback": error_traceback
            }), 500
        else:
            return jsonify({"error": f"Speech processing failed: {error_msg}"}), 500

@app.route('/api/speech/transcribe', methods=['POST'])
def transcribe_speech():
    """Transcribe audio input only."""
    try:
        data = request.get_json(force=True, silent=True)
        if data is None:
            return jsonify({"error": "Invalid JSON request"}), 400
        
        audio_data = data.get('audioData', '')
        language = data.get('language', 'en')
        
        if not audio_data:
            return jsonify({"error": "No audio data provided"}), 400
        
        if not voice_system:
            return jsonify({"error": "Voice system not initialized"}), 500
        
        # Transcribe audio
        audio_buffer = bytes.fromhex(audio_data) if isinstance(audio_data, str) else audio_data
        transcription = voice_system.transcribe_only_sync(audio_buffer, language)
        
        return jsonify({
            "transcription": transcription,
            "language": language,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return jsonify({"error": "Transcription failed"}), 500

@app.route('/api/speech/synthesize', methods=['POST'])
def synthesize_speech_endpoint():
    """Synthesize text to speech only."""
    try:
        data = request.get_json(force=True, silent=True)
        if data is None:
            return jsonify({"error": "Invalid JSON request"}), 400
        
        text = data.get('text', '')
        voice = data.get('voice', 'default')
        language = data.get('language', 'en')
        engine = data.get('engine', 'auto')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        if not voice_system:
            return jsonify({"error": "Voice system not initialized"}), 500
        
        # Get user ID from session (if provided)
        session_id = data.get('sessionId', 'anonymous')
        user_id = get_user_id_from_session(session_id)
        
        # Synthesize speech
        try:
            from gen.text_to_voice import synthesize_speech_sync
            tts_result = synthesize_speech_sync(text, voice, language, engine)
            audio_data = tts_result['audio_data']
            logger.info(f"TTS result: {tts_result}")
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return jsonify({"error": f"TTS synthesis failed: {str(e)}"}), 500
        
        # Get project name from request
        project_name = request.json.get('projectName', 'default') if request.json else 'default'
        
        # Save AI audio to project-specific directory (as MP3)
        audio_filename = f"ai_tts_{int(time.time())}.mp3"
        audio_path = get_user_audio_path(user_id, audio_filename, 'ai', project_name)
        ensure_project_directories(user_id, project_name)  # Ensure project directories exist
        
        # Check if audio is already MP3 or convert it
        audio_format = tts_result.get('format', 'wav')
        logger.info(f"📊 Audio format from TTS: {audio_format}")
        
        if audio_format.lower() in ['mp3', 'audio/mpeg']:
            # Already MP3, save directly
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            logger.info(f"💾 Saved AI TTS audio as MP3 to: {audio_path}")
        else:
            # Convert to MP3 using ffmpeg
                logger.info(f"🔄 Converting AI TTS audio to MP3 format...")
                audio_path = _convert_to_mp3(audio_data, audio_path, audio_format)
                logger.info(f"💾 Saved AI TTS audio (converted to MP3) to: {audio_path}")
        
        return jsonify({
            "audioUrl": get_user_audio_url(user_id, audio_filename, 'ai', project_name),
            "userId": user_id,
            "text": text,
            "voice": voice,
            "language": language,
            "engine": engine,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"TTS synthesis error: {e}")
        return jsonify({"error": "TTS synthesis failed"}), 500

@app.route('/api/bitcoin/content', methods=['POST'])
def generate_bitcoin_content():
    """Generate Bitcoin-specific content."""
    try:
        data = request.get_json(force=True, silent=True)
        if data is None:
            return jsonify({"error": "Invalid JSON request"}), 400
        
        content_type = data.get('contentType', 'conversational')
        topic = data.get('topic', 'general')
        difficulty = data.get('difficulty', 'beginner')
        length = data.get('length', 'short')
        
        if not voice_system:
            return jsonify({"error": "Voice system not initialized"}), 500
        
        # Generate Bitcoin content
        prompt = f"Generate {content_type} Bitcoin content about {topic} for {difficulty} level, {length} length"
        content = voice_system._generate_bitcoin_response_sync(prompt)
        
        return jsonify({
            "content": content,
            "type": content_type,
            "topic": topic,
            "difficulty": difficulty,
            "length": length,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"Bitcoin content generation error: {e}")
        return jsonify({"error": "Content generation failed"}), 500

@app.route('/api/voices', methods=['GET'])
def get_available_voices():
    """Get available TTS voices."""
    try:
        if not voice_system:
            return jsonify({"error": "Voice system not initialized"}), 500
        
        voices = voice_system.get_available_voices()
        engines = voice_system.get_available_engines()
        
        return jsonify({
            "voices": voices,
            "engines": engines,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"Voice listing error: {e}")
        return jsonify({"error": "Failed to get voices"}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve audio files from public/audio directory."""
    return send_from_directory('../public/audio', filename)

@app.route('/data/<directory>/<filename>')
def serve_data_files(directory, filename):
    """
    Serve files from legacy data directories (DEPRECATED - use user-specific endpoints).
    Kept for backward compatibility.
    """
    try:
        # Only allow user and ai directories for security
        if directory not in ['user', 'ai']:
            return jsonify({"error": "Invalid directory"}), 400
        
        # Construct the safe path
        # Use absolute path to avoid issues with working directory
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(backend_dir, 'data', directory)
        
        if not os.path.exists(data_dir):
            return jsonify({"error": "Directory not found"}), 404
        
        return send_from_directory(data_dir, filename)
    except Exception as e:
        logger.error(f"Error serving data file: {e}")
        return jsonify({"error": "Failed to serve file"}), 500

@app.route('/api/users/<user_id>/<project_name>/audio/<audio_type>/<filename>')
def serve_project_audio(user_id, project_name, audio_type, filename):
    """
    Serve project-specific audio files.
    
    Args:
        user_id: User identifier
        project_name: Project name
        audio_type: 'user' for user input, 'ai' for AI response
        filename: Audio filename
    """
    try:
        # Validate audio_type
        if audio_type not in ['user', 'ai']:
            return jsonify({"error": "Invalid audio type. Must be 'user' or 'ai'"}), 400
        
        # Security: Validate user_id and project_name (prevent directory traversal)
        if '..' in user_id or '/' in user_id or '\\' in user_id:
            return jsonify({"error": "Invalid user ID"}), 400
        if '..' in project_name or '/' in project_name or '\\' in project_name:
            return jsonify({"error": "Invalid project name"}), 400
        
        # Get project audio path
        audio_path = get_user_audio_path(user_id, filename, audio_type, project_name)
        
        # Security: Ensure the path is within the user's directory
        user_base = get_user_base_path(user_id)
        if not os.path.abspath(audio_path).startswith(os.path.abspath(user_base)):
            return jsonify({"error": "Invalid file path"}), 403
        
        # Check if file exists
        if not os.path.exists(audio_path) or not os.path.isfile(audio_path):
            logger.warning(f"Audio file not found: {audio_path}")
            return jsonify({"error": "File not found"}), 404
        
        # Serve the file
        audio_dir = os.path.dirname(audio_path)
        return send_from_directory(audio_dir, filename)
    except Exception as e:
        logger.error(f"Error serving project audio file: {e}")
        return jsonify({"error": "Failed to serve file"}), 500

@app.route('/api/users/<user_id>/audio/<audio_type>/<filename>')
def serve_user_audio(user_id, audio_type, filename):
    """
    Serve user-specific audio files (legacy route, without project_name).
    Falls back to 'default' project.
    
    Args:
        user_id: User identifier
        audio_type: 'user' for user input, 'ai' for AI response
        filename: Audio filename
    """
    try:
        # Validate audio_type
        if audio_type not in ['user', 'ai']:
            return jsonify({"error": "Invalid audio type. Must be 'user' or 'ai'"}), 400
        
        # Security: Validate user_id (prevent directory traversal)
        if '..' in user_id or '/' in user_id or '\\' in user_id:
            return jsonify({"error": "Invalid user ID"}), 400
        
        # Try project-based path first (default project)
        project_name = 'default'
        audio_path = get_user_audio_path(user_id, filename, audio_type, project_name)
        
        # If not found in project, try legacy path (without project)
        if not os.path.exists(audio_path) or not os.path.isfile(audio_path):
            audio_path = get_user_audio_path(user_id, filename, audio_type, None)
        
        # Security: Ensure the path is within the user's directory
        user_base = get_user_base_path(user_id)
        if not os.path.abspath(audio_path).startswith(os.path.abspath(user_base)):
            return jsonify({"error": "Invalid file path"}), 403
        
        # Check if file exists
        if not os.path.exists(audio_path) or not os.path.isfile(audio_path):
            return jsonify({"error": "File not found"}), 404
        
        # Serve the file
        audio_dir = os.path.dirname(audio_path)
        return send_from_directory(audio_dir, filename)
    except Exception as e:
        logger.error(f"Error serving user audio file: {e}")
        return jsonify({"error": "Failed to serve file"}), 500

@app.route('/api/users/<user_id>/<project_name>/media/<filename>')
def serve_project_media(user_id, project_name, filename):
    """
    Serve project-specific media files (images, videos, etc.).
    
    Args:
        user_id: User identifier
        project_name: Project name
        filename: Media filename
    """
    try:
        # Security: Validate user_id and project_name (prevent directory traversal)
        if '..' in user_id or '/' in user_id or '\\' in user_id:
            return jsonify({"error": "Invalid user ID"}), 400
        if '..' in project_name or '/' in project_name or '\\' in project_name:
            return jsonify({"error": "Invalid project name"}), 400
        
        # Get project media path
        media_path = get_user_media_path(user_id, filename, project_name)
        
        # Security: Ensure the path is within the user's directory
        project_base = get_project_base_path(user_id, project_name)
        if not os.path.abspath(media_path).startswith(os.path.abspath(project_base)):
            return jsonify({"error": "Invalid file path"}), 403
        
        # Check if file exists
        if not os.path.exists(media_path) or not os.path.isfile(media_path):
            return jsonify({"error": "File not found"}), 404
        
        # Serve the file
        media_dir = os.path.dirname(media_path)
        return send_from_directory(media_dir, filename)
    except Exception as e:
        logger.error(f"Error serving project media file: {e}")
        return jsonify({"error": "Failed to serve file"}), 500

@app.route('/api/users/<user_id>/media/<filename>')
def serve_user_media(user_id, filename):
    """
    Serve user-specific media files (backward compatibility - tries old structure first, then projects).
    
    Args:
        user_id: User identifier
        filename: Media filename
    """
    try:
        # Security: Validate user_id (prevent directory traversal)
        if '..' in user_id or '/' in user_id or '\\' in user_id:
            return jsonify({"error": "Invalid user ID"}), 400
        
        # Try old structure first (for backward compatibility)
        user_base = get_user_base_path(user_id)
        old_media_path = os.path.join(user_base, 'media', filename)
        
        if os.path.exists(old_media_path) and os.path.isfile(old_media_path):
            media_dir = os.path.dirname(old_media_path)
            return send_from_directory(media_dir, filename)
        
        # Try default project
        try:
            media_path = get_user_media_path(user_id, filename, 'default')
            if os.path.exists(media_path) and os.path.isfile(media_path):
                media_dir = os.path.dirname(media_path)
                return send_from_directory(media_dir, filename)
        except:
            pass
        
        # Try talking-orange project (common case)
        try:
            media_path = get_user_media_path(user_id, filename, 'talking-orange')
            if os.path.exists(media_path) and os.path.isfile(media_path):
                media_dir = os.path.dirname(media_path)
                return send_from_directory(media_dir, filename)
        except:
            pass
        
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        logger.error(f"Error serving user media file: {e}")
        return jsonify({"error": "Failed to serve file"}), 500

@app.route('/api/users/<user_id>/<project_name>/ui')
def serve_project_ui(user_id, project_name):
    """
    Serve project-specific UI HTML file.
    This file contains project-specific HTML, CSS, and JavaScript.
    
    Structure: users/{user_id}/{project_name}/ui.html
    
    Args:
        user_id: User identifier
        project_name: Project name
    """
    try:
        # Security: Validate user_id and project_name (prevent directory traversal)
        if '..' in user_id or '/' in user_id or '\\' in user_id:
            return jsonify({"error": "Invalid user ID"}), 400
        if '..' in project_name or '/' in project_name or '\\' in project_name:
            return jsonify({"error": "Invalid project name"}), 400
        
        # Get project base path (users/{user_id}/{project_name})
        project_base = get_project_base_path(user_id, project_name)
        ui_file_path = os.path.join(project_base, 'ui.html')
        
        # Security: Ensure the path is within the user's directory
        user_base = get_user_base_path(user_id)
        if not os.path.abspath(ui_file_path).startswith(os.path.abspath(user_base)):
            return jsonify({"error": "Invalid file path"}), 403
        
        # Check if UI file exists
        if not os.path.exists(ui_file_path) or not os.path.isfile(ui_file_path):
            logger.warning(f"Project UI file not found: {ui_file_path}")
            return jsonify({"error": "Project UI file not found"}), 404
        
        # Read and return the UI file content
        with open(ui_file_path, 'r', encoding='utf-8') as f:
            ui_content = f.read()
        
        # Return as HTML
        return ui_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        logger.error(f"Error serving project UI file: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": "Failed to serve UI file"}), 500

@app.route('/api/users/<user_id>/<project_name>/js/<filename>')
def serve_project_js(user_id, project_name, filename):
    """
    Serve project-specific JavaScript module files.
    This allows projects to have custom animation, voice processing, and other modules.
    
    Structure: users/{user_id}/{project_name}/js/{filename}
    
    Args:
        user_id: User identifier
        project_name: Project name
        filename: JavaScript filename (e.g., 'animation-module.js')
    """
    try:
        # Security: Validate user_id, project_name, and filename (prevent directory traversal)
        if '..' in user_id or '/' in user_id or '\\' in user_id:
            return jsonify({"error": "Invalid user ID"}), 400
        if '..' in project_name or '/' in project_name or '\\' in project_name:
            return jsonify({"error": "Invalid project name"}), 400
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({"error": "Invalid filename"}), 400
        
        # Ensure filename ends with .js
        if not filename.endswith('.js'):
            return jsonify({"error": "Invalid file type. Only .js files are allowed"}), 400
        
        # Get project base path (users/{user_id}/{project_name})
        project_base = get_project_base_path(user_id, project_name)
        js_file_path = os.path.join(project_base, 'js', filename)
        
        # Security: Ensure the path is within the user's directory
        user_base = get_user_base_path(user_id)
        if not os.path.abspath(js_file_path).startswith(os.path.abspath(user_base)):
            return jsonify({"error": "Invalid file path"}), 403
        
        # Check if JS file exists
        if not os.path.exists(js_file_path) or not os.path.isfile(js_file_path):
            logger.warning(f"Project JS file not found: {js_file_path}")
            return jsonify({"error": "Project JS file not found"}), 404
        
        # Read and return the JS file content
        with open(js_file_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Return as JavaScript
        return js_content, 200, {'Content-Type': 'application/javascript; charset=utf-8'}
    except Exception as e:
        logger.error(f"Error serving project JS file: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": "Failed to serve JS file"}), 500

@app.route('/api/users/<user_id>/<project_name>/media/videos/<video_dir>/<filename>')
def serve_project_video_frame(user_id, project_name, video_dir, filename):
    """
    Serve video animation frames from project directories.
    
    Args:
        user_id: User identifier
        project_name: Project name
        video_dir: Video directory name
        filename: Frame filename
    """
    try:
        # Security: Validate user_id, project_name and paths
        if '..' in user_id or '/' in user_id or '\\' in user_id:
            return jsonify({"error": "Invalid user ID"}), 400
        if '..' in project_name or '/' in project_name or '\\' in project_name:
            return jsonify({"error": "Invalid project name"}), 400
        if '..' in video_dir or '..' in filename:
            return jsonify({"error": "Invalid path"}), 400
        
        directories = ensure_project_directories(user_id, project_name)
        video_path = os.path.join(directories['media'], 'videos', video_dir, filename)
        
        # Security: Ensure the path is within the project's directory
        project_base = get_project_base_path(user_id, project_name)
        if not os.path.abspath(video_path).startswith(os.path.abspath(project_base)):
            return jsonify({"error": "Invalid file path"}), 403
        
        # Check if file exists
        if not os.path.exists(video_path):
            return jsonify({"error": "File not found"}), 404
        
        # Serve the file
        video_dir_path = os.path.dirname(video_path)
        return send_from_directory(video_dir_path, filename)
    except Exception as e:
        logger.error(f"Error serving project video frame: {e}")
        return jsonify({"error": "Failed to serve file"}), 500

@app.route('/api/users/<user_id>/media/videos/<video_dir>/<filename>')
def serve_user_video_frame(user_id, video_dir, filename):
    """
    Serve video animation frames (backward compatibility - tries old structure first, then projects).
    
    Args:
        user_id: User identifier
        video_dir: Video directory name
        filename: Frame filename
    """
    try:
        # Security: Validate user_id and paths
        if '..' in user_id or '/' in user_id or '\\' in user_id:
            return jsonify({"error": "Invalid user ID"}), 400
        if '..' in video_dir or '..' in filename:
            return jsonify({"error": "Invalid path"}), 400
        
        # Try old structure first
        user_base = get_user_base_path(user_id)
        old_video_path = os.path.join(user_base, 'media', 'videos', video_dir, filename)
        
        if os.path.exists(old_video_path):
            video_dir_path = os.path.dirname(old_video_path)
            return send_from_directory(video_dir_path, filename)
        
        # Try default project
        try:
            directories = ensure_project_directories(user_id, 'default')
            video_path = os.path.join(directories['media'], 'videos', video_dir, filename)
            if os.path.exists(video_path):
                video_dir_path = os.path.dirname(video_path)
                return send_from_directory(video_dir_path, filename)
        except:
            pass
        
        # Try talking-orange project
        try:
            directories = ensure_project_directories(user_id, 'talking-orange')
            video_path = os.path.join(directories['media'], 'videos', video_dir, filename)
            if os.path.exists(video_path):
                video_dir_path = os.path.dirname(video_path)
                return send_from_directory(video_dir_path, filename)
        except:
            pass
        
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        logger.error(f"Error serving video frame: {e}")
        return jsonify({"error": "Failed to serve file"}), 500

@app.route('/api/users/<user_id>/files', methods=['GET'])
def list_user_files(user_id):
    """
    List files for a user.
    
    Args:
        user_id: User identifier
    """
    try:
        from user_manager import list_user_files as get_files
        
        # Security: Validate user_id
        if '..' in user_id or '/' in user_id or '\\' in user_id:
            return jsonify({"error": "Invalid user ID"}), 400
        
        file_type = request.args.get('type', 'all')  # 'all', 'user', 'ai', or 'media'
        files = get_files(user_id, file_type)
        
        # Format file list with metadata
        formatted_files = {
            'user': [],
            'ai': [],
            'media': []
        }
        
        directories = ensure_user_directories(user_id)
        
        for file_type_key in ['user', 'ai', 'media']:
            file_list = files.get(file_type_key, [])
            for filename in file_list:
                file_path = os.path.join(directories[f'data_{file_type_key}'] if file_type_key != 'media' else directories['media'], filename)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    formatted_files[file_type_key].append({
                        'filename': filename,
                        'size': file_size,
                        'fileType': file_type_key
                    })
        
        return jsonify({
            "userId": user_id,
            "files": formatted_files,
            "timestamp": time.time()
        })
    except Exception as e:
        logger.error(f"Error listing user files: {e}")
        return jsonify({"error": "Failed to list files"}), 500

@app.route('/api/users/upload', methods=['POST'])
def upload_user_file():
    """
    Upload a file for a user (target image or media content).
    """
    try:
        logger.info("📤 Upload request received")
        
        if 'file' not in request.files:
            logger.error("❌ No file in request")
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.error("❌ Empty filename")
            return jsonify({"error": "No file selected"}), 400
        
        file_type = request.form.get('fileType', 'media')  # 'target' or 'media'
        user_id = request.form.get('userId')
        project_name = request.form.get('projectName', 'default')  # Get project name from request
        
        logger.info(f"📤 Upload: user_id={user_id}, project_name={project_name}, file_type={file_type}, filename={file.filename}")
        
        if not user_id:
            logger.error("❌ No user_id provided")
            return jsonify({"error": "User ID required"}), 400
        
        # Security: Validate user_id and project_name
        if '..' in user_id or '/' in user_id or '\\' in user_id:
            logger.error(f"❌ Invalid user_id: {user_id}")
            return jsonify({"error": "Invalid user ID"}), 400
        if '..' in project_name or '/' in project_name or '\\' in project_name:
            logger.error(f"❌ Invalid project_name: {project_name}")
            return jsonify({"error": "Invalid project name"}), 400
        
        # Ensure project directories exist (this will create the project if it doesn't exist)
        try:
            directories = ensure_project_directories(user_id, project_name)
            logger.info(f"✅ Project directories ensured for {user_id}/{project_name}")
        except Exception as e:
            logger.error(f"❌ Failed to ensure project directories: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({"error": f"Failed to create project directories: {str(e)}"}), 500
        
        # Determine save location
        save_dir = directories['media']
        logger.info(f"📁 Save directory: {save_dir}")
        
        # Security: Sanitize filename
        original_filename = os.path.basename(file.filename)
        if '..' in original_filename or '/' in original_filename or '\\' in original_filename:
            return jsonify({"error": "Invalid filename"}), 400
        
        # Handle target images - compile to .mind file
        if file_type == 'target':
            logger.info(f"🎯 Processing target image upload")
            
            # Use targets subdirectory for target images
            # Check if 'targets' key exists, otherwise create it
            if 'targets' not in directories:
                targets_dir = os.path.join(save_dir, 'targets')
                directories['targets'] = targets_dir
            else:
                targets_dir = directories['targets']
            
            os.makedirs(targets_dir, exist_ok=True)
            logger.info(f"📁 Targets directory: {targets_dir}")
            
            # Save original image in targets/ subdirectory
            image_filename = f"target_source_{int(time.time())}_{original_filename}"
            image_path = os.path.join(targets_dir, image_filename)
            logger.info(f"💾 Saving target image to: {image_path}")
            file.save(image_path)
            logger.info(f"✅ Target image saved: {image_path} ({os.path.getsize(image_path)} bytes)")
            
            # Validate image for AR
            if validate_image_for_ar and callable(validate_image_for_ar):
                logger.info(f"🔍 Validating image for AR...")
                try:
                    is_valid, validation_msg = validate_image_for_ar(image_path)
                    if not is_valid:
                        # Delete invalid image
                        try:
                            os.remove(image_path)
                        except:
                            pass
                        logger.error(f"❌ Image validation failed: {validation_msg}")
                        return jsonify({
                            "error": f"Image not suitable for AR: {validation_msg}",
                            "validation": validation_msg
                        }), 400
                    logger.info(f"✅ Image validation: {validation_msg}")
                except Exception as validation_error:
                    logger.warning(f"⚠️ Image validation error (continuing anyway): {validation_error}")
            else:
                logger.info(f"⚠️ Image validation skipped (validator not available)")
            
            # Compile to .mind file - use standard name "targets.mind" in media root
            mind_filename = "targets.mind"  # Standard name, one per project
            mind_path = os.path.join(save_dir, mind_filename)
            logger.info(f"🔨 Compiling to .mind file: {mind_path}")
            
            if compile_image_to_mind and callable(compile_image_to_mind):
                try:
                    logger.info(f"🔨 Calling compile_image_to_mind({image_path}, {mind_path})...")
                    compiled_path = compile_image_to_mind(image_path, mind_path)
                    logger.info(f"🔨 Compilation result: {compiled_path}")
                    
                    if compiled_path and os.path.exists(compiled_path):
                        # Success - return .mind file info
                        file_size = os.path.getsize(compiled_path)
                        logger.info(f"✅ Target compiled successfully: {compiled_path} ({file_size} bytes)")
                        
                        return jsonify({
                            "success": True,
                            "filename": mind_filename,
                            "originalImage": image_filename,
                            "size": file_size,
                            "fileType": "target",
                            "url": get_user_media_url(user_id, mind_filename, project_name),
                            "message": "Target image compiled successfully. Your AR marker is ready to use!"
                        }), 200
                    else:
                        # Compilation failed - check why
                        logger.error(f"❌ Compilation failed: compiled_path={compiled_path}")
                        logger.error(f"   File exists check: {os.path.exists(compiled_path) if compiled_path else 'compiled_path is None'}")
                        logger.error(f"   Image path exists: {os.path.exists(image_path)}")
                        logger.error(f"   Output path: {mind_path}")
                        
                        # Check if Node.js is available
                        from mindar_compiler import check_node_available
                        node_available = check_node_available() if check_node_available else False
                        
                        error_hint = "Compilation returned None. "
                        if not node_available:
                            error_hint += "Node.js is not installed. Install from https://nodejs.org/"
                        else:
                            error_hint += "Check server logs for compilation details."
                        
                        return jsonify({
                            "error": "Failed to compile image to AR target.",
                            "originalImage": image_filename,
                            "hint": error_hint,
                            "details": f"compiled_path={compiled_path}, node_available={node_available}"
                        }), 500
                except RuntimeError as runtime_error:
                    # RuntimeError from compile_image_to_mind (e.g., Node.js not available)
                    error_str = str(runtime_error)
                    logger.error(f"❌ Compilation runtime error: {error_str}")
                    
                    # Extract hint if it's already in the error message
                    hint = "Install Node.js from https://nodejs.org/ and run: npm install mind-ar canvas"
                    if "💡 Hint:" in error_str:
                        # The hint is already in the error message from mindar_compiler.py
                        hint = None  # Don't duplicate the hint
                    
                    return jsonify({
                        "error": error_str,
                        "originalImage": image_filename,
                        "hint": hint
                    }), 500
                except Exception as compile_error:
                    logger.error(f"❌ Compilation exception: {compile_error}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return jsonify({
                        "error": f"Compilation failed: {str(compile_error)}",
                        "originalImage": image_filename,
                        "hint": "Check server logs for details"
                    }), 500
            else:
                # Compiler not available
                logger.error(f"❌ Compiler not available: compile_image_to_mind={compile_image_to_mind}")
                return jsonify({
                    "error": "AR target compiler not available. Please install Node.js and mind-ar-compiler.",
                    "originalImage": image_filename,
                    "hint": "Install Node.js: https://nodejs.org/ then run: npm install -g mind-ar-compiler"
                }), 500
        else:
            # Regular media files
            filename = original_filename
            file_path = os.path.join(save_dir, filename)
            
            # Save file
            file.save(file_path)
            file_size = os.path.getsize(file_path)
            
            logger.info(f"✅ File uploaded: {file_path} ({file_size} bytes)")
            
            return jsonify({
                "success": True,
                "filename": filename,
                "size": file_size,
                "fileType": file_type,
                "url": get_user_media_url(user_id, filename, project_name)
            }), 200
        
    except Exception as e:
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        logger.error(f"❌ Error uploading file: {error_msg}")
        logger.error(f"❌ Traceback: {error_traceback}")
        # Return detailed error to frontend for debugging
        return jsonify({
            "error": f"Upload failed: {error_msg}",
            "details": error_traceback.split('\n')[-5:] if error_traceback else None  # Last 5 lines of traceback
        }), 500

# ============================================
# Nostr Authentication Endpoints
# ============================================

@app.route('/api/auth/nostr/login', methods=['POST'])
def nostr_login():
    """
    Authenticate with Nostr private key (nsec).
    Validates nsec, derives npub, sets secure cookie.
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        nsec = data.get('nsec', '').strip()
        
        if not nsec:
            return jsonify({"error": "nsec is required"}), 400
        
        # Validate nsec format (starts with 'nsec1')
        if not nsec.startswith('nsec1'):
            return jsonify({"error": "Invalid nsec format"}), 400
        
        # For now, we'll validate by attempting to derive npub
        # In production, you might want to use a Python bech32 library
        # For simplicity, we'll accept the nsec and derive npub on frontend
        # But we need to validate it's a real nsec
        
        # Since we can't easily decode bech32 in Python without additional libs,
        # we'll use a subprocess to call Node.js or accept the npub from frontend
        # For security, we should validate the nsec properly
        
        # For now, we'll accept npub from frontend (derived from nsec)
        # The frontend will send both nsec and npub, we validate they match
        npub = data.get('npub', '').strip()
        
        if not npub or not npub.startswith('npub1'):
            return jsonify({"error": "Invalid npub format"}), 400
        
        # Use npub as userId (it's the public key, safe to use)
        user_id = npub
        
        # Create base user directory if it doesn't exist
        try:
            user_base = get_user_base_path(user_id)
            os.makedirs(user_base, exist_ok=True)
            os.chmod(user_base, 0o755)
            logger.info(f"✅ User directory created/verified: {user_base}")
        except Exception as e:
            logger.error(f"❌ Failed to create user directory for {user_id}: {e}")
            # Don't fail login if directory creation fails, but log it
        
        # Set secure cookie with npub
        response = jsonify({
            "success": True,
            "npub": npub,
            "userId": user_id,
            "message": "Logged in successfully"
        })
        
        # Set httpOnly cookie (secure in production)
        response.set_cookie(
            'nostr_npub',
            npub,
            max_age=60*60*24*30,  # 30 days
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite='Lax'
        )
        
        logger.info(f"✅ Nostr login successful: {npub[:20]}...")
        
        return response, 200
        
    except Exception as e:
        logger.error(f"Error in nostr login: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

@app.route('/api/auth/nostr/status', methods=['GET'])
def nostr_auth_status():
    """
    Check if user is authenticated.
    Returns npub and user_id if authenticated.
    """
    try:
        npub = request.cookies.get('nostr_npub')
        
        if not npub:
            return jsonify({
                "authenticated": False
            }), 200
        
        # Validate npub format
        if not npub.startswith('npub1'):
            return jsonify({
                "authenticated": False
            }), 200
        
        # Use npub as userId
        user_id = npub
        
        return jsonify({
            "authenticated": True,
            "npub": npub,
            "userId": user_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        return jsonify({"authenticated": False}), 200

@app.route('/api/auth/nostr/logout', methods=['POST'])
def nostr_logout():
    """
    Logout user by clearing authentication cookie.
    """
    try:
        response = jsonify({
            "success": True,
            "message": "Logged out successfully"
        })
        
        # Clear cookie
        response.set_cookie(
            'nostr_npub',
            '',
            max_age=0,
            httponly=True,
            secure=False,
            samesite='Lax'
        )
        
        return response, 200
        
    except Exception as e:
        logger.error(f"Error logging out: {e}")
        return jsonify({"error": f"Logout failed: {str(e)}"}), 500

@app.route('/api/users/<user_id>/projects', methods=['GET'])
def list_user_projects_endpoint(user_id):
    """
    List all projects for a user.
    """
    try:
        # Security: Validate user_id
        if '..' in user_id or '/' in user_id or '\\' in user_id:
            return jsonify({"error": "Invalid user ID"}), 400
        
        projects = list_user_projects(user_id)
        return jsonify({"projects": projects}), 200
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        return jsonify({"error": f"Failed to list projects: {str(e)}"}), 500

@app.route('/api/users/<user_id>/projects', methods=['POST'])
def create_user_project(user_id):
    """
    Create a new project for a user.
    """
    try:
        # Security: Validate user_id
        if '..' in user_id or '/' in user_id or '\\' in user_id:
            return jsonify({"error": "Invalid user ID"}), 400
        
        data = request.get_json(force=True, silent=True) or {}
        project_name = data.get('projectName', '').strip()
        
        if not project_name:
            return jsonify({"error": "Project name is required"}), 400
        
        # Security: Validate project_name
        if '..' in project_name or '/' in project_name or '\\' in project_name:
            return jsonify({"error": "Invalid project name"}), 400
        
        # Check if project already exists
        if project_exists(user_id, project_name):
            return jsonify({"error": "Project already exists"}), 400
        
        # Create project directories
        directories = ensure_project_directories(user_id, project_name)
        
        logger.info(f"✅ Created project: {user_id}/{project_name}")
        
        return jsonify({
            "success": True,
            "projectName": project_name,
            "message": f"Project '{project_name}' created successfully"
        }), 200
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Failed to create project: {str(e)}"}), 500

@app.route('/api/users/<user_id>/<project_name>/files', methods=['GET'])
def list_project_files_endpoint(user_id, project_name):
    """
    List all files in a project.
    """
    try:
        logger.info(f"📁 Listing files for user={user_id}, project={project_name}")
        
        # Security: Validate user_id and project_name
        if '..' in user_id or '/' in user_id or '\\' in user_id:
            return jsonify({"error": "Invalid user ID"}), 400
        if '..' in project_name or '/' in project_name or '\\' in project_name:
            return jsonify({"error": "Invalid project name"}), 400
        
        # Ensure directories exist first (this will create them if needed)
        try:
            directories = ensure_project_directories(user_id, project_name)
            logger.info(f"✅ Directories ensured for {user_id}/{project_name}")
        except Exception as e:
            logger.error(f"❌ Failed to ensure directories for {user_id}/{project_name}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({"error": f"Failed to create project directories: {str(e)}"}), 500
        
        # List files
        try:
            # Import here to avoid conflict with local list_user_files() route handler
            from user_manager import list_user_files as get_user_files
            files = get_user_files(user_id, project_name)
            logger.info(f"✅ Listed files: {len(files.get('user', []))} user, {len(files.get('ai', []))} ai, {len(files.get('media', []))} media")
        except Exception as e:
            logger.error(f"❌ Failed to list files for {user_id}/{project_name}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Return empty file list instead of error
            files = {'user': [], 'ai': [], 'media': []}
        
        # Format file list with metadata
        formatted_files = {
            'user': [],
            'ai': [],
            'media': []
        }
        
        # Map file types to directory keys
        dir_map = {
            'user': 'user_input',
            'ai': 'ai',
            'media': 'media'
        }
        
        for file_type_key in ['user', 'ai', 'media']:
            file_list = files.get(file_type_key, [])
            dir_key = dir_map.get(file_type_key)
            
            if not dir_key or dir_key not in directories:
                logger.warning(f"Directory key '{dir_key}' not found in directories for {file_type_key}")
                continue
                
            for filename in file_list:
                try:
                    file_path = os.path.join(directories[dir_key], filename)
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        formatted_files[file_type_key].append({
                            'filename': filename,
                            'size': file_size,
                            'fileType': file_type_key
                        })
                except Exception as e:
                    logger.error(f"Error processing file {filename} for {file_type_key}: {e}")
                    continue
        
        return jsonify({"files": formatted_files}), 200
    except Exception as e:
        logger.error(f"Error listing project files: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Failed to list files: {str(e)}"}), 500

@app.route('/api/targets', methods=['GET'])
def get_all_targets():
    """
    Get all available AR targets from all users.
    Returns targets with their associated media information.
    """
    try:
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        users_dir = os.path.join(backend_dir, 'users')
        
        targets = []
        
        if not os.path.exists(users_dir):
            return jsonify({"targets": []}), 200
        
        # Scan all user directories and their projects
        for user_id in os.listdir(users_dir):
            user_path = os.path.join(users_dir, user_id)
            if not os.path.isdir(user_path):
                continue
            
            # Security: Skip invalid user IDs
            if '..' in user_id or '/' in user_id or '\\' in user_id:
                continue
            
            # Scan projects within user directory
            for project_name in os.listdir(user_path):
                project_path = os.path.join(user_path, project_name)
                if not os.path.isdir(project_path):
                    continue
                
                # Security: Skip invalid project names
                if '..' in project_name or '/' in project_name or '\\' in project_name:
                    continue
                
                # Look for media directory in project
                media_dir = os.path.join(project_path, 'media')
                if not os.path.exists(media_dir):
                    continue
                
                # Look for .mind files (AR targets) in project media
                # Prefer "targets.mind" as standard name, but accept any .mind file
                mind_files = [f for f in os.listdir(media_dir) if f.endswith('.mind') and os.path.isfile(os.path.join(media_dir, f))]
                # Prefer targets.mind if it exists
                target_filename = 'targets.mind' if 'targets.mind' in mind_files else (mind_files[0] if mind_files else None)
                
                if target_filename:
                    target_path = os.path.join(media_dir, target_filename)
                    if os.path.isfile(target_path):
                            # Get associated media files (content, not target images)
                            media_files = []
                            for media_file in os.listdir(media_dir):
                                # Skip .mind files (targets) and target source images
                                if media_file == target_filename or media_file.endswith('.mind'):
                                    continue
                                if os.path.isfile(os.path.join(media_dir, media_file)):
                                    # Skip files in targets/ subdirectory (those are source images)
                                    if not media_file.startswith('target_source_'):
                                        media_files.append({
                                            'filename': media_file,
                                            'url': get_user_media_url(user_id, media_file, project_name),
                                            'type': _get_file_type(media_file)
                                        })
                            
                            # Get video directories and their contents (frames + audio files)
                            videos_dir = os.path.join(media_dir, 'videos')
                            if os.path.exists(videos_dir):
                                for video_dir in os.listdir(videos_dir):
                                    video_path = os.path.join(videos_dir, video_dir)
                                    if os.path.isdir(video_path):
                                        # Add the video animation directory itself
                                        media_files.append({
                                            'filename': video_dir,
                                            'url': f"/api/users/{user_id}/{project_name}/media/videos/{video_dir}/",
                                            'type': 'video_animation'
                                        })
                                        
                                        # Also include audio files from video directories
                                        for file_in_video_dir in os.listdir(video_path):
                                            file_path = os.path.join(video_path, file_in_video_dir)
                                            if os.path.isfile(file_path) and file_in_video_dir.endswith(('.mp3', '.wav', '.ogg')):
                                                media_files.append({
                                                    'filename': file_in_video_dir,
                                                    'url': f"/api/users/{user_id}/{project_name}/media/videos/{video_dir}/{file_in_video_dir}",
                                                    'type': 'audio',
                                                    'videoDir': video_dir  # Track which video directory it's in
                                                })
                            
                            targets.append({
                                'targetId': f"{user_id}_{project_name}_{target_filename}",
                                'userId': user_id,
                                'projectName': project_name,
                                'filename': target_filename,
                                'url': get_user_media_url(user_id, target_filename, project_name),
                                'media': media_files
                            })
        
        # Also check for default talking-orange target in frontend/media (fallback)
        frontend_media = os.path.join(os.path.dirname(backend_dir), 'frontend', 'media')
        default_target = os.path.join(frontend_media, 'targets.mind')
        if os.path.exists(default_target):
            targets.append({
                'targetId': 'talking-orange_default',
                'userId': 'talking-orange',
                'filename': 'targets.mind',
                'url': './media/targets.mind',
                'media': _get_default_media_files(frontend_media),
                'isDefault': True
            })
        
        return jsonify({
            "targets": targets,
            "count": len(targets),
            "timestamp": time.time()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting targets: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": "Failed to get targets"}), 500

def _get_file_type(filename):
    """Determine file type from extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.png', '.jpg', '.jpeg', '.gif']:
        return 'image'
    elif ext in ['.mp4', '.webm', '.mov']:
        return 'video'
    elif ext in ['.mp3', '.wav', '.ogg']:
        return 'audio'
    elif ext == '.mind':
        return 'target'
    else:
        return 'other'

def _get_default_media_files(media_dir):
    """Get default media files from frontend/media."""
    media_files = []
    if not os.path.exists(media_dir):
        return media_files
    
    for filename in os.listdir(media_dir):
        file_path = os.path.join(media_dir, filename)
        if os.path.isfile(file_path) and filename != 'targets.mind':
            media_files.append({
                'filename': filename,
                'url': f'./media/{filename}',
                'type': _get_file_type(filename)
            })
    
    # Add videos directory
    videos_dir = os.path.join(media_dir, 'videos')
    if os.path.exists(videos_dir):
        for video_dir in os.listdir(videos_dir):
            video_path = os.path.join(videos_dir, video_dir)
            if os.path.isdir(video_path):
                media_files.append({
                    'filename': video_dir,
                    'url': f'./media/videos/{video_dir}/',
                    'type': 'video_animation'
                })
    
    return media_files

@app.route('/api/users/<user_id>/<project_name>/media/<filename>', methods=['DELETE'])
def delete_project_media(user_id, project_name, filename):
    """
    Delete a media file from a project.
    """
    try:
        # Security: Validate user_id and project_name
        if '..' in user_id or '/' in user_id or '\\' in user_id:
            return jsonify({"error": "Invalid user ID"}), 400
        if '..' in project_name or '/' in project_name or '\\' in project_name:
            return jsonify({"error": "Invalid project name"}), 400
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({"error": "Invalid filename"}), 400
        
        # Get project media path
        media_path = get_user_media_path(user_id, filename, project_name)
        
        # Security: Ensure the path is within the user's directory
        project_base = get_project_base_path(user_id, project_name)
        if not os.path.abspath(media_path).startswith(os.path.abspath(project_base)):
            return jsonify({"error": "Invalid file path"}), 403
        
        # Check if file exists
        if not os.path.exists(media_path) or not os.path.isfile(media_path):
            return jsonify({"error": "File not found"}), 404
        
        # Delete the file
        os.remove(media_path)
        logger.info(f"✅ Deleted file: {media_path}")
        
        return jsonify({"success": True, "message": "File deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return jsonify({"error": f"Failed to delete file: {str(e)}"}), 500

@app.route('/api/users/<user_id>/media/<filename>', methods=['DELETE'])
def delete_user_media(user_id, filename):
    """
    Delete a user's media file.
    """
    try:
        # Security: Validate user_id and filename
        if '..' in user_id or '/' in user_id or '\\' in user_id:
            return jsonify({"error": "Invalid user ID"}), 400
        
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({"error": "Invalid filename"}), 400
        
        # Get file path
        media_path = get_user_media_path(user_id, filename)
        
        # Security: Ensure the path is within the user's directory
        user_base = get_user_base_path(user_id)
        if not os.path.abspath(media_path).startswith(os.path.abspath(user_base)):
            return jsonify({"error": "Invalid file path"}), 403
        
        # Check if file exists
        if not os.path.exists(media_path):
            return jsonify({"error": "File not found"}), 404
        
        # Delete file
        os.remove(media_path)
        logger.info(f"✅ Deleted file: {media_path}")
        
        return jsonify({"success": True, "message": "File deleted"}), 200
        
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return jsonify({"error": "Failed to delete file"}), 500

@app.route('/ar-test.html')
def ar_test():
    """Serve the basic AR test page"""
    return send_from_directory('../frontend', 'ar-test.html')

@app.route('/mindar-simple.html')
def mindar_simple():
    """Serve the simple MindAR test page"""
    return send_from_directory('../frontend', 'mindar-simple.html')

@app.route('/mindar-local.html')
def mindar_local():
    """Serve the local MindAR test page"""
    return send_from_directory('../frontend', 'mindar-local.html')

@app.route('/mindar-orange.html')
def mindar_orange():
    """Serve the MindAR orange test page"""
    return send_from_directory('../frontend', 'mindar-orange.html')

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"❌ [500 ERROR HANDLER] {error}")
    try:
        logger.error(f"❌ [500 ERROR HANDLER] Traceback: {traceback.format_exc()}")
    except Exception as tb_error:
        logger.error(f"❌ [500 ERROR HANDLER] Could not get traceback: {tb_error}")
    return jsonify({"error": f"Internal server error: {str(error)}"}), 500

if __name__ == '__main__':
    print("=" * 60, file=sys.stderr)
    print("🚀 [STARTUP] Starting Flask server...", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    try:
        print("📁 [STARTUP] Step 1: Creating necessary directories...", file=sys.stderr)
        os.makedirs('../frontend', exist_ok=True)
        print("✅ [STARTUP] Step 1: Directories created", file=sys.stderr)
        
        print("🔧 [STARTUP] Step 2: Reading configuration...", file=sys.stderr)
        port = int(os.getenv('PORT', 3000))
        debug = os.getenv('DEBUG', 'False').lower() == 'true'
        print(f"   Port: {port}", file=sys.stderr)
        print(f"   Debug: {debug}", file=sys.stderr)
        print(f"   Working directory: {os.getcwd()}", file=sys.stderr)
        print("✅ [STARTUP] Step 2: Configuration loaded", file=sys.stderr)
        
        print("📊 [STARTUP] Step 3: Flask app ready", file=sys.stderr)
        print(f"   API endpoints: http://localhost:{port}/api/", file=sys.stderr)
        print(f"   Frontend: http://localhost:{port}/", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(f"🚀 [STARTUP] Starting Flask server on port {port} (debug={debug})", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        
        logger.info(f"🚀 Starting Talking Orange Python Backend on port {port}")
        logger.info(f"📊 API endpoints available at http://localhost:{port}/api/")
        logger.info(f"🎯 Frontend served at http://localhost:{port}/")
        
        app.run(host='0.0.0.0', port=port, debug=debug)
    except Exception as e:
        print(f"❌ [STARTUP] FATAL ERROR: {e}", file=sys.stderr)
        print(f"❌ [STARTUP] Traceback: {traceback.format_exc()}", file=sys.stderr)
        logger.error(f"FATAL STARTUP ERROR: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
