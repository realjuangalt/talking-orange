"""
Text to Voice Module
Handles text-to-speech synthesis using multiple TTS engines.
Supports local and cloud TTS with fallback options for Talking Orange AR project.
"""

import os
import sys
import json
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Union
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextToVoiceService:
    """
    Text to Voice service supporting multiple TTS engines.
    Prioritizes local engines for low hardware requirements and good quality.
    """
    
    def __init__(self, voice_dir: str = None):
        self.voice_dir = voice_dir or os.getenv('VOICE_DIR', './voices')
        self.venice_api_key = os.getenv('VENICE_KEY')
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Note: voice_dir is not used for storing voice files (voices come from system/cloud)
        # Directory creation removed as it's unnecessary
        
        # Initialize available engines
        self.available_engines = []
        self._check_available_engines()
        
    def _check_available_engines(self):
        """Check which TTS engines are available."""
        engines = []
        
        # Check local engines
        local_engines = ['espeak', 'festival', 'pico2wave', 'gtts']
        for engine in local_engines:
            try:
                result = subprocess.run(['which', engine], capture_output=True, text=True)
                if result.returncode == 0:
                    engines.append(f"local_{engine}")
                    logger.info(f"Local TTS engine found: {engine}")
            except Exception:
                pass
        
        # Check cloud APIs
        if self.venice_api_key:
            engines.append("venice_ai")
            logger.info("Venice AI TTS available")
        
        if self.elevenlabs_api_key:
            engines.append("elevenlabs")
            logger.info("ElevenLabs TTS available")
            
        if self.openai_api_key:
            engines.append("openai")
            logger.info("OpenAI TTS available")
        
        self.available_engines = engines
        logger.info(f"Available TTS engines: {engines}")
    
    def synthesize_speech(self, text: str, voice: str = "default", language: str = "en", 
                         engine: str = "auto", speed: float = 1.0, pitch: float = 1.0) -> Dict[str, Any]:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            voice: Voice to use
            language: Language code
            engine: TTS engine to use ('auto' for best available)
            speed: Speech speed (0.5-2.0)
            pitch: Voice pitch (0.5-2.0)
            
        Returns:
            Dict with audio data and metadata
        """
        try:
            if not text.strip():
                raise ValueError("Empty text provided")
            
            # Choose best engine if auto
            if engine == "auto":
                logger.info(f"🔊 [TTS] Auto-selecting best TTS engine...")
                logger.info(f"🔊 [TTS] Available engines: {self.available_engines}")
                engine = self._choose_best_engine()
                logger.info(f"🔊 [TTS] Selected engine: {engine}")
            else:
                logger.info(f"🔊 [TTS] Using specified engine: {engine}")
                if engine not in self.available_engines:
                    logger.warning(f"⚠️ [TTS] Engine '{engine}' not in available engines: {self.available_engines}")
            
            logger.info(f"🔊 [TTS] Synthesizing speech with {engine} engine")
            logger.info(f"🔊 [TTS] Text length: {len(text)} characters")
            logger.info(f"🔊 [TTS] Language: {language}, Voice: {voice}, Speed: {speed}, Pitch: {pitch}")
            
            import time
            tts_start = time.time()
            
            # Route to appropriate engine
            tts_result = None
            if engine.startswith("local_"):
                logger.info(f"🔊 [TTS] Routing to local engine: {engine}")
                tts_result = self._synthesize_local(text, engine, voice, language, speed, pitch)
            elif engine == "venice_ai":
                logger.info(f"🔊 [TTS] Routing to Venice AI cloud engine")
                tts_result = self._synthesize_venice_ai(text, voice, language, speed)
            elif engine == "elevenlabs":
                logger.info(f"🔊 [TTS] Routing to ElevenLabs cloud engine")
                tts_result = self._synthesize_elevenlabs(text, voice, language, speed)
            elif engine == "openai":
                logger.info(f"🔊 [TTS] Routing to OpenAI cloud engine")
                tts_result = self._synthesize_openai(text, voice, language, speed)
            else:
                raise ValueError(f"Unknown TTS engine: {engine}")
            
            tts_duration = round(time.time() - tts_start, 2)
            audio_size = len(tts_result.get("audio_data", b""))
            logger.info(f"✅ [TTS] Synthesis completed in {tts_duration}s")
            logger.info(f"✅ [TTS] Generated audio size: {audio_size} bytes ({audio_size/1024:.1f} KB)")
            logger.info(f"✅ [TTS] Audio format: {tts_result.get('format', 'unknown')}")
            logger.info(f"✅ [TTS] Engine used: {tts_result.get('engine', 'unknown')}")
            
            return tts_result
                
        except Exception as e:
            tts_duration = round(time.time() - tts_start, 2) if 'tts_start' in locals() else 0
            logger.error(f"❌ [TTS] Synthesis failed after {tts_duration}s: {e}")
            logger.error(f"❌ [TTS] Error type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ [TTS] Traceback: {traceback.format_exc()}")
            raise Exception(f"TTS synthesis error: {str(e)}")
    
    def _choose_best_engine(self) -> str:
        """Choose the best available TTS engine."""
        # Priority order: local engines first, then cloud
        priority_engines = [
            "local_espeak",      # Fast, good quality
            "local_festival",    # Good quality
            "local_pico2wave",   # Lightweight
            "local_gtts",        # Google TTS (requires internet)
            "venice_ai",         # High quality cloud
            "elevenlabs",        # Premium cloud
            "openai"             # OpenAI cloud
        ]
        
        for engine in priority_engines:
            if engine in self.available_engines:
                return engine
        
        raise Exception("No TTS engines available")
    
    def _synthesize_local(self, text: str, engine: str, voice: str, language: str, 
                         speed: float, pitch: float) -> Dict[str, Any]:
        """Synthesize speech using local TTS engines."""
        try:
            import time
            local_start = time.time()
            logger.info(f"🔊 [TTS LOCAL] Starting local synthesis with {engine}...")
            
            # Create temporary output file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                output_path = temp_file.name
            
            logger.info(f"📁 [TTS LOCAL] Temporary output file: {output_path}")
            
            # Build command based on engine
            if engine == "local_espeak":
                cmd = [
                    'espeak', 
                    '-v', f'{language}', 
                    '-s', str(int(160 * speed)), 
                    '-p', str(int(50 * pitch)),
                    '--stdout'
                ]
                
            elif engine == "local_festival":
                cmd = ['festival', '--tts', '--language', language]
                
            elif engine == "local_pico2wave":
                cmd = [
                    'pico2wave', 
                    '--lang', language.split('-')[0], 
                    '--wave', output_path
                ]
                
            elif engine == "local_gtts":
                # Use gTTS Python library
                return self._synthesize_gtts(text, language, speed)
            
            else:
                raise ValueError(f"Unknown local engine: {engine}")
            
            # Execute command
            if engine == "local_pico2wave":
                # pico2wave writes directly to file
                cmd.append(f'"{text}"')
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            else:
                # Other engines output to stdout
                cmd.append(f'"{text}"')
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    # Write stdout to file
                    with open(output_path, 'wb') as f:
                        f.write(result.stdout)
                else:
                    raise Exception(f"TTS command failed: {result.stderr}")
            
            # Read generated audio
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                file_size = os.path.getsize(output_path)
                logger.info(f"✅ [TTS LOCAL] Audio file generated: {file_size} bytes")
                with open(output_path, 'rb') as f:
                    audio_data = f.read()
                
                logger.info(f"✅ [TTS LOCAL] Audio data read: {len(audio_data)} bytes")
                
                # Clean up
                os.unlink(output_path)
                logger.info(f"🧹 [TTS LOCAL] Temporary file cleaned up")
                
                local_duration = round(time.time() - local_start, 2)
                logger.info(f"✅ [TTS LOCAL] Local synthesis completed in {local_duration}s")
                
                return {
                    "audio_data": audio_data,
                    "format": "wav",
                    "engine": engine,
                    "voice": voice,
                    "language": language,
                    "speed": speed,
                    "pitch": pitch
                }
            else:
                logger.error(f"❌ [TTS LOCAL] Audio file missing or empty: {output_path}")
                logger.error(f"❌ [TTS LOCAL] File exists: {os.path.exists(output_path)}")
                if os.path.exists(output_path):
                    logger.error(f"❌ [TTS LOCAL] File size: {os.path.getsize(output_path)} bytes")
                raise Exception("TTS engine failed to generate audio")
                
        except Exception as e:
            local_duration = round(time.time() - local_start, 2) if 'local_start' in locals() else 0
            logger.error(f"❌ [TTS LOCAL] Local TTS synthesis failed after {local_duration}s: {e}")
            logger.error(f"❌ [TTS LOCAL] Error type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ [TTS LOCAL] Traceback: {traceback.format_exc()}")
            raise Exception(f"Local TTS error: {str(e)}")
    
    def _synthesize_gtts(self, text: str, language: str, speed: float) -> Dict[str, Any]:
        """Synthesize speech using Google TTS (gTTS)."""
        try:
            from gtts import gTTS
            import io
            
            # Create gTTS object
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Generate audio
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_data = audio_buffer.getvalue()
            
            return {
                "audio_data": audio_data,
                "format": "mp3",
                "engine": "local_gtts",
                "voice": "google",
                "language": language,
                "speed": speed
            }
            
        except ImportError:
            raise Exception("gTTS not installed. Install with: pip install gtts")
        except Exception as e:
            logger.error(f"gTTS synthesis failed: {e}")
            raise Exception(f"gTTS error: {str(e)}")
    
    def _synthesize_venice_ai(self, text: str, voice: str, language: str, speed: float) -> Dict[str, Any]:
        """Synthesize speech using Venice AI TTS."""
        try:
            if not self.venice_api_key:
                raise Exception("Venice AI API key not found")
            
            url = "https://api.venice.ai/api/v1/audio/speech"
            headers = {
                "Authorization": f"Bearer {self.venice_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "tts-kokoro",
                "response_format": "mp3",
                "speed": speed,
                "streaming": False,
                "voice": voice or "bm_fable",
                "input": text[:4096]  # Truncate to max length
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return {
                    "audio_data": response.content,
                    "format": "mp3",
                    "engine": "venice_ai",
                    "voice": voice,
                    "language": language,
                    "speed": speed
                }
            else:
                raise Exception(f"Venice AI TTS error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Venice AI TTS failed: {e}")
            raise Exception(f"Venice AI TTS error: {str(e)}")
    
    def _synthesize_elevenlabs(self, text: str, voice: str, language: str, speed: float) -> Dict[str, Any]:
        """Synthesize speech using ElevenLabs TTS."""
        try:
            if not self.elevenlabs_api_key:
                raise Exception("ElevenLabs API key not found")
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice or 'pNInz6obpgDQGcFmaJgB'}"
            headers = {
                "Accept": "audio/mpeg",
                "xi-api-key": self.elevenlabs_api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return {
                    "audio_data": response.content,
                    "format": "mp3",
                    "engine": "elevenlabs",
                    "voice": voice,
                    "language": language,
                    "speed": speed
                }
            else:
                raise Exception(f"ElevenLabs TTS error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"ElevenLabs TTS failed: {e}")
            raise Exception(f"ElevenLabs TTS error: {str(e)}")
    
    def _synthesize_openai(self, text: str, voice: str, language: str, speed: float) -> Dict[str, Any]:
        """Synthesize speech using OpenAI TTS."""
        try:
            if not self.openai_api_key:
                raise Exception("OpenAI API key not found")
            
            url = "https://api.openai.com/v1/audio/speech"
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "tts-1",
                "voice": voice or "alloy",
                "input": text
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return {
                    "audio_data": response.content,
                    "format": "mp3",
                    "engine": "openai",
                    "voice": voice,
                    "language": language,
                    "speed": speed
                }
            else:
                raise Exception(f"OpenAI TTS error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"OpenAI TTS failed: {e}")
            raise Exception(f"OpenAI TTS error: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            "initialized": True,
            "available_engines": self.available_engines,
            "voice_dir": self.voice_dir,
            "has_venice_key": bool(self.venice_api_key),
            "has_elevenlabs_key": bool(self.elevenlabs_api_key),
            "has_openai_key": bool(self.openai_api_key)
        }

# Convenience functions for easy usage
def synthesize_speech(text: str, voice: str = "default", language: str = "en", 
                     engine: str = "auto") -> bytes:
    """Synthesize speech and return audio data."""
    service = TextToVoiceService()
    result = service.synthesize_speech(text, voice, language, engine)
    return result["audio_data"]

def get_available_voices(engine: str = "auto") -> list:
    """Get available voices for specified engine."""
    service = TextToVoiceService()
    if engine == "auto":
        engine = service._choose_best_engine()
    
    # Return common voices based on engine
    if engine.startswith("local_"):
        return ["default", "male", "female"]
    elif engine == "venice_ai":
        return ["bm_fable", "bm_male", "bm_female"]
    elif engine == "elevenlabs":
        return ["pNInz6obpgDQGcFmaJgB", "EXAVITQu4vr4xnSDxMaL", "VR6AewLTigWG4xSOukaG"]
    elif engine == "openai":
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    else:
        return ["default"]

def synthesize_speech_sync(text: str, voice: str = "default", 
                          language: str = "en", engine: str = "auto") -> Dict[str, Any]:
    """
    Synchronous version of synthesize_speech for Flask compatibility.
    """
    try:
        logger.info(f"Synthesizing speech (sync): {text[:50]}...")
        
        # Use gTTS for simple synchronous TTS
        try:
            from gtts import gTTS
            import io
            
            tts = gTTS(text=text, lang=language, slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_data = audio_buffer.getvalue()
            
            logger.info("✅ gTTS synthesis successful")
            return {
                "audio_data": audio_data,
                "format": "mp3",
                "engine": "gtts",
                "voice": voice
            }
            
        except Exception as gtts_error:
            logger.error(f"gTTS failed: {gtts_error}")
            
            # Fallback to simple text response
            return {
                "audio_data": b"",
                "format": "wav",
                "engine": "fallback",
                "voice": voice
            }
            
    except Exception as e:
        logger.error(f"TTS synthesis failed (sync): {e}")
        return {
            "audio_data": b"",
            "format": "wav",
            "engine": "error",
            "voice": voice
        }

# Example usage
if __name__ == "__main__":
    # Test the service
    service = TextToVoiceService()
    
    print("✅ TextToVoiceService initialized")
    print(f"Status: {service.get_status()}")
    
    # Test synthesis
    try:
        result = service.synthesize_speech("Hello, I am the Talking Orange!", "default", "en")
        logger.info(f"✅ TTS synthesis successful: {len(result['audio_data'])} bytes")
    except Exception as e:
        print(f"❌ TTS synthesis failed: {e}")
