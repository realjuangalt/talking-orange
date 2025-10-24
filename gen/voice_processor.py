"""
Voice Processor Module
Combines voice-to-text and text-to-voice functionality for Talking Orange AR project.
Provides a unified interface for voice processing with Bitcoin evangelism focus.
"""

import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Union
from voice_to_text import VoiceToTextService
from text_to_voice import TextToVoiceService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceProcessor:
    """
    Unified voice processing service combining STT and TTS capabilities.
    Optimized for Talking Orange AR project with Bitcoin evangelism focus.
    """
    
    def __init__(self, model_dir: str = None, voice_dir: str = None):
        self.model_dir = model_dir or os.getenv('MODEL_DIR', '/opt/jarvis_editor/2.0/models')
        self.voice_dir = voice_dir or os.getenv('VOICE_DIR', './voices')
        
        # Initialize services
        self.stt_service = VoiceToTextService(model_dir=self.model_dir)
        self.tts_service = TextToVoiceService(voice_dir=self.voice_dir)
        
        self.initialized = False
        
    def initialize(self) -> bool:
        """Initialize both STT and TTS services."""
        try:
            logger.info("Initializing Voice Processor...")
            
            # Initialize STT service
            if not self.stt_service.initialize():
                logger.error("Failed to initialize STT service")
                return False
            
            # TTS service doesn't need explicit initialization
            logger.info("Voice Processor initialized successfully")
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Voice Processor initialization failed: {e}")
            return False
    
    def process_voice_input(self, audio_input: Union[str, bytes], 
                           language: str = "en", 
                           tts_voice: str = "default",
                           tts_engine: str = "auto") -> Dict[str, Any]:
        """
        Process voice input: transcribe speech and generate response audio.
        
        Args:
            audio_input: Audio file path or audio buffer
            language: Language code
            tts_voice: Voice for TTS response
            tts_engine: TTS engine to use
            
        Returns:
            Dict with transcription, response text, and audio data
        """
        try:
            if not self.initialized:
                raise Exception("Voice Processor not initialized")
            
            # Step 1: Transcribe audio
            logger.info("Transcribing audio input...")
            if isinstance(audio_input, str):
                # File path
                stt_result = self.stt_service.transcribe_audio(audio_input, language)
            else:
                # Audio buffer
                stt_result = self.stt_service.transcribe_audio_buffer(audio_input, language)
            
            transcription = stt_result["text"]
            logger.info(f"Transcription: {transcription}")
            
            # Step 2: Generate Bitcoin response (placeholder for now)
            response_text = self._generate_bitcoin_response(transcription)
            logger.info(f"Response: {response_text}")
            
            # Step 3: Synthesize response audio
            logger.info("Synthesizing response audio...")
            tts_result = self.tts_service.synthesize_speech(
                response_text, 
                voice=tts_voice, 
                language=language, 
                engine=tts_engine
            )
            
            return {
                "transcription": transcription,
                "response_text": response_text,
                "audio_data": tts_result["audio_data"],
                "audio_format": tts_result["format"],
                "stt_engine": stt_result["model"],
                "tts_engine": tts_result["engine"],
                "language": language,
                "voice": tts_voice
            }
            
        except Exception as e:
            logger.error(f"Voice processing failed: {e}")
            raise Exception(f"Voice processing error: {str(e)}")
    
    def transcribe_only(self, audio_input: Union[str, bytes], language: str = "en") -> str:
        """Transcribe audio input only."""
        try:
            if isinstance(audio_input, str):
                result = self.stt_service.transcribe_audio(audio_input, language)
            else:
                result = self.stt_service.transcribe_audio_buffer(audio_input, language)
            
            return result["text"]
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise Exception(f"Transcription error: {str(e)}")
    
    def synthesize_only(self, text: str, voice: str = "default", 
                       language: str = "en", engine: str = "auto") -> bytes:
        """Synthesize text to speech only."""
        try:
            result = self.tts_service.synthesize_speech(text, voice, language, engine)
            return result["audio_data"]
            
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            raise Exception(f"TTS synthesis error: {str(e)}")
    
    def _generate_bitcoin_response(self, user_input: str) -> str:
        """
        Generate Bitcoin evangelism response based on user input.
        This is a placeholder - in production, this would use the LLM service.
        """
        input_lower = user_input.lower()
        
        # Bitcoin-related responses
        if any(word in input_lower for word in ['bitcoin', 'crypto', 'blockchain', 'btc']):
            responses = [
                "Bitcoin is amazing! It's digital money that gives you financial freedom! 🍊",
                "Bitcoin is revolutionary! It's decentralized, secure, and scarce!",
                "Bitcoin is the future of money! It's digital gold that you can send anywhere!",
                "Bitcoin gives you financial sovereignty! No banks, no governments, just you and your money!"
            ]
            import random
            return random.choice(responses)
        
        elif any(word in input_lower for word in ['what', 'how', 'explain', 'tell']):
            return "I'd love to explain Bitcoin! It's decentralized digital money that works without banks. What would you like to know more about?"
        
        elif any(word in input_lower for word in ['hello', 'hi', 'hey']):
            return "Hello there! I'm the Talking Orange! 🍊 I'm here to tell you all about Bitcoin! What would you like to know?"
        
        elif any(word in input_lower for word in ['help', 'how']):
            return "I'm here to help you understand Bitcoin! It's digital money that's secure, fast, and gives you control over your finances!"
        
        else:
            return "That's interesting! Bitcoin is such an exciting topic! 🍊 What would you like to know about digital money and financial freedom?"
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of voice processing services."""
        return {
            "initialized": self.initialized,
            "stt_status": self.stt_service.get_status(),
            "tts_status": self.tts_service.get_status(),
            "model_dir": self.model_dir,
            "voice_dir": self.voice_dir
        }
    
    def get_available_voices(self, engine: str = "auto") -> list:
        """Get available voices for TTS."""
        return self.tts_service.get_available_voices(engine)
    
    def get_available_engines(self) -> list:
        """Get available TTS engines."""
        return self.tts_service.available_engines

# Convenience functions for easy usage
def process_voice_file(audio_path: str, language: str = "en", 
                      tts_voice: str = "default", tts_engine: str = "auto") -> Dict[str, Any]:
    """Process voice file and return transcription + response audio."""
    processor = VoiceProcessor()
    if processor.initialize():
        return processor.process_voice_input(audio_path, language, tts_voice, tts_engine)
    else:
        raise Exception("Failed to initialize Voice Processor")

def process_voice_buffer(audio_buffer: bytes, language: str = "en", 
                        tts_voice: str = "default", tts_engine: str = "auto") -> Dict[str, Any]:
    """Process voice buffer and return transcription + response audio."""
    processor = VoiceProcessor()
    if processor.initialize():
        return processor.process_voice_input(audio_buffer, language, tts_voice, tts_engine)
    else:
        raise Exception("Failed to initialize Voice Processor")

# Example usage
if __name__ == "__main__":
    # Test the voice processor
    processor = VoiceProcessor()
    
    if processor.initialize():
        print("✅ Voice Processor initialized successfully")
        print(f"Status: {processor.get_status()}")
        print(f"Available TTS engines: {processor.get_available_engines()}")
        print(f"Available voices: {processor.get_available_voices()}")
    else:
        print("❌ Voice Processor initialization failed")
