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
        Generate Bitcoin evangelism response using real LLM API.
        Uses Venice AI API with Bitcoin evangelism prompt.
        """
        try:
            import requests
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            venice_api_key = os.getenv('VENICE_KEY')
            
            if not venice_api_key:
                raise Exception("VENICE_KEY not found in environment variables")
            
            # Load Bitcoin evangelism prompt
            prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'bitcoin_evangelism.txt')
            system_prompt = ""
            
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    system_prompt = f.read().strip()
            else:
                system_prompt = """You are the Talking Orange, a friendly and enthusiastic Bitcoin evangelist. Your mission is to educate people about Bitcoin in an engaging, accessible way.

PERSONALITY:
- Enthusiastic and optimistic about Bitcoin
- Patient and educational
- Use simple, clear language
- Be encouraging and supportive
- Occasionally use orange-themed expressions
- Keep responses under 100 words
- End with a question to keep conversation going

You have access to web search capabilities, so you can provide up-to-date information about Bitcoin when needed."""
            
            # Call Venice AI API
            url = "https://api.venice.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {venice_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                "model": "llama-3.3-70b",
                "temperature": 0.7,
                "max_tokens": 150,
                "venice_parameters": {
                    "enable_web_search": "auto"
                },
                "parallel_tool_calls": True
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and data["choices"]:
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    raise Exception("No valid response from LLM")
            else:
                raise Exception(f"LLM API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Bitcoin response generation failed: {e}")
            # Fallback to simple Bitcoin response
            return f"Bitcoin is amazing! It's digital money that gives you financial freedom! 🍊 What would you like to know about Bitcoin?"
    
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
