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

def initialize_voice_system():
    """Initialize the voice processing system."""
    global voice_system
    try:
        logger.info("🎤 Initializing Talking Orange Voice System...")
        
        # Try to create the voice system
        logger.info("🔧 Creating TalkingOrangeVoiceSystem instance...")
        voice_system = TalkingOrangeVoiceSystem()
        logger.info("✅ TalkingOrangeVoiceSystem instance created")
        
        # Initialize asynchronously
        logger.info("🔄 Running async initialization...")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(voice_system.initialize())
            logger.info(f"✅ Async initialization result: {result}")
        except Exception as async_error:
            logger.error(f"❌ Async initialization failed: {async_error}")
            # Try synchronous initialization as fallback
            logger.info("🔄 Trying synchronous initialization...")
            result = voice_system.initialize_sync()
            logger.info(f"✅ Sync initialization result: {result}")
        
        logger.info("✅ Voice System initialized successfully")
        
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
        import time
        logger.info(f"🔍 Health check - voice_system: {voice_system is not None}")
        
        if voice_system:
            logger.info("🔍 Voice system exists, getting status...")
            voice_status = voice_system.get_status()
            logger.info(f"🔍 Voice system status: {voice_status}")
        else:
            logger.info("🔍 Voice system is None")
            voice_status = {"initialized": False}
        
        status = {
            "status": "healthy",
            "voice_system": voice_status,
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
                audio_buffer = base64.b64decode(audio_data)
                logger.info(f"🔊 Decoded audio buffer: {len(audio_buffer)} bytes")
                logger.info(f"🔊 Audio buffer type: {type(audio_buffer)}")
                logger.info(f"🔊 First 20 bytes: {audio_buffer[:20] if len(audio_buffer) > 20 else audio_buffer}")
                
                logger.info(f"🎤 Calling voice_system.process_voice_input_sync...")
                result = voice_system.process_voice_input_sync(
                    audio_buffer, language, tts_voice, tts_engine
                )
                logger.info(f"🎤 Voice processing result keys: {list(result.keys())}")
                logger.info(f"🎤 Voice processing result audio_data length: {len(result.get('audio_data', b''))} bytes")
            except Exception as e:
                logger.error(f"❌ Audio processing error: {e}")
                import traceback
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
        
        # Save audio response to file
        import time
        audio_filename = f"speech_{session_id}_{int(time.time())}.wav"
        audio_path = os.path.join('../public/audio', audio_filename)
        
        logger.info(f"💾 Saving audio response...")
        logger.info(f"📁 Audio filename: {audio_filename}")
        logger.info(f"📁 Audio path: {audio_path}")
        logger.info(f"📊 Result keys: {list(result.keys())}")
        logger.info(f"📊 Audio data type: {type(result.get('audio_data'))}")
        logger.info(f"📊 Audio data length: {len(result.get('audio_data', b''))} bytes")
        
        # Ensure audio directory exists
        audio_dir = os.path.dirname(audio_path)
        logger.info(f"📁 Audio directory: {audio_dir}")
        os.makedirs(audio_dir, exist_ok=True)
        logger.info(f"✅ Audio directory exists: {os.path.exists(audio_dir)}")
        
        # Write audio data
        try:
            with open(audio_path, 'wb') as f:
                f.write(result['audio_data'])
            logger.info(f"✅ Audio file saved successfully: {audio_path}")
            logger.info(f"📊 File size after save: {os.path.getsize(audio_path)} bytes")
        except Exception as e:
            logger.error(f"❌ Failed to save audio file: {e}")
            raise
        
        return jsonify({
            "transcription": result.get('transcription', ''),
            "response": result.get('response_text', ''),
            "audioUrl": f"/audio/{audio_filename}",
            "timestamp": time.time(),
            "sttEngine": result.get('stt_engine', 'whisper'),
            "ttsEngine": result.get('tts_engine', 'auto'),
            "language": language,
            "voice": tts_voice
        })
        
    except Exception as e:
        logger.error(f"❌ Speech processing error: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
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
        
        # Save audio to file
        audio_filename = f"tts_{int(time.time())}.wav"
        audio_path = os.path.join('../public/audio', audio_filename)
        
        # Ensure audio directory exists
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        
        with open(audio_path, 'wb') as f:
            f.write(audio_data)
        
        return jsonify({
            "audioUrl": f"/audio/{audio_filename}",
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
    """Serve audio files."""
    return send_from_directory('../public/audio', filename)

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
    os.makedirs('../public/audio', exist_ok=True)
    os.makedirs('../frontend', exist_ok=True)
    
    # Start the Flask server
    port = int(os.getenv('PORT', 3000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"🚀 Starting Talking Orange Python Backend on port {port}")
    logger.info(f"📊 API endpoints available at http://localhost:{port}/api/")
    logger.info(f"🎯 Frontend served at http://localhost:{port}/")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
