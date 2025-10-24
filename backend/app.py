"""
Talking Orange AR Backend Server
Python Flask backend for voice processing and Bitcoin evangelism.
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Add gen directory to path
gen_dir = os.path.join(os.path.dirname(__file__), '..', 'gen')
if gen_dir not in sys.path:
    sys.path.insert(0, gen_dir)

# Import our voice processing modules
from main import TalkingOrangeVoiceSystem, process_voice_file, process_voice_buffer, transcribe_audio, synthesize_speech

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global voice system instance
voice_system = None

@app.before_first_request
def initialize_voice_system():
    """Initialize the voice processing system."""
    global voice_system
    try:
        logger.info("🎤 Initializing Talking Orange Voice System...")
        voice_system = TalkingOrangeVoiceSystem()
        
        # Initialize asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(voice_system.initialize())
        
        logger.info("✅ Voice System initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Voice System initialization failed: {e}")
        voice_system = None

@app.route('/')
def index():
    """Serve the main frontend page."""
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from frontend directory."""
    return send_from_directory('../frontend', filename)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        status = {
            "status": "healthy",
            "voice_system": voice_system.get_status() if voice_system else {"initialized": False},
            "timestamp": asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/api/speech/process', methods=['POST'])
def process_speech():
    """Process speech input and return Bitcoin response with audio."""
    try:
        data = request.get_json()
        text = data.get('text', '')
        audio_data = data.get('audioData', '')
        session_id = data.get('sessionId', 'anonymous')
        language = data.get('language', 'en')
        tts_voice = data.get('ttsVoice', 'default')
        tts_engine = data.get('ttsEngine', 'auto')
        
        if not voice_system:
            return jsonify({"error": "Voice system not initialized"}), 500
        
        # Process the input
        if audio_data:
            # Process audio input
            audio_buffer = bytes.fromhex(audio_data) if isinstance(audio_data, str) else audio_data
            result = asyncio.run(voice_system.process_voice_input(
                audio_buffer, language, tts_voice, tts_engine
            ))
        elif text:
            # Process text input
            result = asyncio.run(voice_system.process_voice_input(
                text, language, tts_voice, tts_engine
            ))
        else:
            return jsonify({"error": "No text or audio provided"}), 400
        
        # Save audio response to file
        audio_filename = f"speech_{session_id}_{int(asyncio.get_event_loop().time())}.wav"
        audio_path = os.path.join('../public/audio', audio_filename)
        
        # Ensure audio directory exists
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        
        with open(audio_path, 'wb') as f:
            f.write(result['audio_data'])
        
        return jsonify({
            "transcription": result.get('transcription', ''),
            "response": result.get('response_text', ''),
            "audioUrl": f"/audio/{audio_filename}",
            "timestamp": asyncio.get_event_loop().time(),
            "sttEngine": result.get('stt_engine', 'whisper'),
            "ttsEngine": result.get('tts_engine', 'auto'),
            "language": language,
            "voice": tts_voice
        })
        
    except Exception as e:
        logger.error(f"Speech processing error: {e}")
        return jsonify({"error": "Speech processing failed"}), 500

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
        transcription = asyncio.run(voice_system.transcribe_only(audio_buffer, language))
        
        return jsonify({
            "transcription": transcription,
            "language": language,
            "timestamp": asyncio.get_event_loop().time()
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
        audio_data = asyncio.run(voice_system.synthesize_only(text, voice, language, engine))
        
        # Save audio to file
        audio_filename = f"tts_{int(asyncio.get_event_loop().time())}.wav"
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
            "timestamp": asyncio.get_event_loop().time()
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
        content = asyncio.run(voice_system._generate_bitcoin_response(prompt))
        
        return jsonify({
            "content": content,
            "type": content_type,
            "topic": topic,
            "difficulty": difficulty,
            "length": length,
            "timestamp": asyncio.get_event_loop().time()
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
            "timestamp": asyncio.get_event_loop().time()
        })
        
    except Exception as e:
        logger.error(f"Voice listing error: {e}")
        return jsonify({"error": "Failed to get voices"}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve audio files."""
    return send_from_directory('../public/audio', filename)

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
