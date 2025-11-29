"""
Talking Orange AR Backend Server
Python Flask backend for voice processing and Bitcoin evangelism.
"""

import os
import sys
import json
import logging
import asyncio
import time
import traceback
import tempfile
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Add backend/gen directory to path
gen_dir = os.path.join(os.path.dirname(__file__), 'gen')
if gen_dir not in sys.path:
    sys.path.insert(0, gen_dir)

# Import our voice processing modules
import importlib.util

# Load the main module from backend/gen directory
spec = importlib.util.spec_from_file_location("main", os.path.join(gen_dir, "main.py"))
main_module = importlib.util.module_from_spec(spec)
sys.modules["main"] = main_module
spec.loader.exec_module(main_module)

# Import the classes and functions we need
TalkingOrangeVoiceSystem = main_module.TalkingOrangeVoiceSystem
process_voice_file = main_module.process_voice_file
process_voice_buffer = main_module.process_voice_buffer
transcribe_audio = main_module.transcribe_audio
synthesize_speech = main_module.synthesize_speech

# Load environment variables from project root
project_root = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

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
    global voice_system
    import time
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
            import traceback
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
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        voice_system = None

# Initialize voice system on startup
initialize_voice_system()

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
        data = request.get_json()
        logger.info(f"📥 Received speech request: {list(data.keys())}")
        
        text = data.get('text', '')
        audio_data = data.get('audioData', '')
        session_id = data.get('sessionId', 'anonymous')
        language = data.get('language', 'en')
        tts_voice = data.get('ttsVoice', 'default')
        tts_engine = data.get('ttsEngine', 'auto')
        
        logger.info(f"🎤 Audio data present: {bool(audio_data)}, Text present: {bool(text)}")
        logger.info(f"🌍 Language: {language}, Session: {session_id}")
        
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
                
                # Save user audio input to data/user/ with timestamp
                user_audio_filename = f"user_input_{session_id}_{int(time.time())}.webm"
                user_audio_path = os.path.join('data', 'user', user_audio_filename)
                os.makedirs(os.path.dirname(user_audio_path), exist_ok=True)
                
                try:
                    with open(user_audio_path, 'wb') as f:
                        f.write(audio_buffer)
                    logger.info(f"💾 Saved user audio input to: {user_audio_path}")
                    logger.info(f"📊 User audio file size: {os.path.getsize(user_audio_path)} bytes")
                except Exception as save_error:
                    logger.error(f"Failed to save user audio: {save_error}")
                    # Don't fail the whole request if we can't save the file
                
                # Process audio with voice system
                import time
                api_start = time.time()
                logger.info(f"🎤 [API] Calling voice_system.process_voice_input_sync...")
                logger.info(f"🎤 [API] Audio buffer size: {len(audio_buffer)} bytes")
                logger.info(f"🎤 [API] Language: {language}, TTS voice: {tts_voice}, TTS engine: {tts_engine}")
                
                result = voice_system.process_voice_input_sync(
                    audio_buffer, language, tts_voice, tts_engine
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
            result = voice_system.process_voice_input_sync(
                text, language, tts_voice, tts_engine
            )
        else:
            logger.error("❌ No text or audio provided")
            return jsonify({"error": "No text or audio provided"}), 400
        
        # Save AI audio response to data/ai/ with timestamp (as MP3)
        audio_filename = f"ai_response_{session_id}_{int(time.time())}.mp3"
        audio_path = os.path.join('data', 'ai', audio_filename)
        
        logger.info(f"💾 Saving audio response...")
        logger.info(f"📁 Audio filename: {audio_filename}")
        logger.info(f"📁 Audio path: {audio_path}")
        logger.info(f"📊 Result keys: {list(result.keys())}")
        logger.info(f"📊 Audio data type: {type(result.get('audio_data'))}")
        logger.info(f"📊 Audio data length: {len(result.get('audio_data', b''))} bytes")
        
        # Ensure AI audio directory exists
        audio_dir = os.path.dirname(audio_path)
        logger.info(f"📁 Audio directory: {audio_dir}")
        os.makedirs(audio_dir, exist_ok=True)
        logger.info(f"✅ Audio directory exists: {os.path.exists(audio_dir)}")
        
        # Write AI audio data (convert to MP3 if needed)
        try:
            audio_data = result['audio_data']
            
            # Check if audio is already MP3 or convert it
            audio_format = result.get('audio_format', result.get('format', 'wav'))
            logger.info(f"📊 Audio format from TTS: {audio_format}")
            
            # Save audio file
            if audio_format.lower() in ['mp3', 'audio/mpeg']:
                # Already MP3, save directly
                with open(audio_path, 'wb') as f:
                    f.write(audio_data)
                logger.info(f"✅ AI audio file saved as MP3: {audio_path}")
                audio_filename = f"ai_response_{session_id}_{int(time.time())}.mp3"
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
                    fallback_filename = f"ai_response_{session_id}_{int(time.time())}.{original_ext}"
                    fallback_path = os.path.join('data', 'ai', fallback_filename)
                    with open(fallback_path, 'wb') as f:
                        f.write(audio_data)
                    audio_filename = fallback_filename
                    logger.info(f"✅ AI audio file saved in original format: {fallback_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save audio file: {e}")
            logger.warning(f"⚠️ Continuing without saving audio file")
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
            response_data["audioUrl"] = f"/data/ai/{audio_filename}"
        else:
            logger.warning("⚠️ No audio file saved, skipping audioUrl in response")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Speech processing error: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Speech processing failed: {str(e)}"}), 500

@app.route('/api/speech/transcribe', methods=['POST'])
def transcribe_speech():
    """Transcribe audio input only."""
    try:
        data = request.get_json()
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
        data = request.get_json()
        text = data.get('text', '')
        voice = data.get('voice', 'default')
        language = data.get('language', 'en')
        engine = data.get('engine', 'auto')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        if not voice_system:
            return jsonify({"error": "Voice system not initialized"}), 500
        
        # Synthesize speech
        try:
            from gen.text_to_voice import synthesize_speech_sync
            tts_result = synthesize_speech_sync(text, voice, language, engine)
            audio_data = tts_result['audio_data']
            logger.info(f"TTS result: {tts_result}")
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return jsonify({"error": f"TTS synthesis failed: {str(e)}"}), 500
        
        # Save AI audio to data/ai/ with timestamp (as MP3)
        audio_filename = f"ai_tts_{int(time.time())}.mp3"
        audio_path = os.path.join('data', 'ai', audio_filename)
        
        # Ensure AI audio directory exists
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        
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
            "audioUrl": f"/data/ai/{audio_filename}",
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
        data = request.get_json()
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
    """Serve files from data directories (user audio inputs and AI audio outputs)."""
    try:
        # Only allow user and ai directories for security
        if directory not in ['user', 'ai']:
            return jsonify({"error": "Invalid directory"}), 400
        
        # Construct the safe path
        data_dir = os.path.join('data', directory)
        
        if not os.path.exists(data_dir):
            return jsonify({"error": "Directory not found"}), 404
        
        return send_from_directory(data_dir, filename)
    except Exception as e:
        logger.error(f"Error serving data file: {e}")
        return jsonify({"error": "Failed to serve file"}), 500

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
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('../frontend', exist_ok=True)
    
    # Start the Flask server
    port = int(os.getenv('PORT', 3000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"🚀 Starting Talking Orange Python Backend on port {port}")
    logger.info(f"📊 API endpoints available at http://localhost:{port}/api/")
    logger.info(f"🎯 Frontend served at http://localhost:{port}/")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
