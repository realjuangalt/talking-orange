"""
Main Voice Processing Module for Talking Orange AR Project
Handles voice-to-text, text-to-voice, and Bitcoin evangelism responses.
Uses individual modules as needed for clean, modular architecture.
"""

import os
import sys
import json
import logging
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dotenv import load_dotenv

# Import our voice processing modules
try:
    from .voice_to_text import VoiceToTextService
    from .text_to_voice import TextToVoiceService
    from .text_generator import TextGenerator
except ImportError:
    # Fallback for when called from backend
    from voice_to_text import VoiceToTextService
    from text_to_voice import TextToVoiceService
    from text_generator import TextGenerator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TalkingOrangeVoiceSystem:
    """
    Main voice processing system for Talking Orange AR project.
    Coordinates STT, TTS, and Bitcoin evangelism responses.
    """
    
    def __init__(self, model_dir: str = None, voice_dir: str = None):
        self.model_dir = model_dir or os.getenv('MODEL_DIR', str(Path(__file__).parent.parent.parent / 'models'))
        self.voice_dir = voice_dir or os.getenv('VOICE_DIR', './voices')
        
        # Initialize services
        self.stt_service = VoiceToTextService(model_dir=self.model_dir)
        self.tts_service = TextToVoiceService(voice_dir=self.voice_dir)
        self.text_generator = TextGenerator()
        
        self.initialized = False
        
    async def initialize(self) -> bool:
        """Initialize all voice processing services."""
        try:
            logger.info("Initializing Talking Orange Voice System...")
            
            # Initialize STT service
            if not self.stt_service.initialize():
                logger.error("Failed to initialize STT service")
                return False
            
            # TTS service doesn't need explicit initialization
            logger.info("Talking Orange Voice System initialized successfully")
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Voice system initialization failed: {e}")
            return False
    
    def initialize_sync(self) -> bool:
        """Synchronous initialization for Flask compatibility."""
        try:
            logger.info("Initializing Talking Orange Voice System (sync)...")
            
            # Initialize STT service
            if not self.stt_service.initialize():
                logger.error("Failed to initialize STT service")
                return False
            
            # TTS service doesn't need explicit initialization
            logger.info("Talking Orange Voice System initialized successfully (sync)")
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Voice system initialization failed (sync): {e}")
            return False
    
    def process_voice_input_sync(self, audio_input: Union[str, bytes], 
                                language: str = "en", 
                                tts_voice: str = "default",
                                tts_engine: str = "auto") -> Dict[str, Any]:
        """
        Synchronous version of process_voice_input for Flask compatibility.
        """
        try:
            logger.info("Processing voice input (sync)...")
            
            # Transcribe audio
            if isinstance(audio_input, bytes):
                transcription = self.stt_service.transcribe_audio_buffer(audio_input, language)
                user_text = transcription["text"]
            else:
                user_text = audio_input
            
            logger.info(f"Transcribed text: {user_text}")
            
            # Generate Bitcoin response
            response_text = self._generate_bitcoin_response_sync(user_text)
            logger.info(f"Generated response: {response_text[:100]}...")
            
            # Synthesize speech
            try:
                from .text_to_voice import synthesize_speech_sync
            except ImportError:
                from text_to_voice import synthesize_speech_sync
            tts_result = synthesize_speech_sync(response_text, voice=tts_voice, language=language, engine=tts_engine)
            
            return {
                "transcription": user_text,
                "response_text": response_text,
                "audio_data": tts_result["audio_data"],
                "stt_engine": "whisper",
                "tts_engine": tts_result["engine"],
                "tts_voice": tts_result["voice"]
            }
            
        except Exception as e:
            logger.error(f"Voice processing failed (sync): {e}")
            return {
                "transcription": "",
                "response_text": "I'm having trouble processing your request. Please try again.",
                "audio_data": b"",
                "stt_engine": "error",
                "tts_engine": "error",
                "tts_voice": "error"
            }
    
    def _generate_bitcoin_response_sync(self, user_input: str) -> str:
        """Synchronous Bitcoin response generation using real LLM."""
        try:
            # Use the text generator for real LLM response
            try:
                from .text_generator import TextGenerator
            except ImportError:
                from text_generator import TextGenerator
            
            # Load Bitcoin evangelism prompt from file
            prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'bitcoin_evangelism.txt')
            
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    system_prompt = f.read().strip()
            else:
                logger.error(f"Prompt file not found at {prompt_path}")
                system_prompt = "You are a friendly Bitcoin educator."
            
            # Create full prompt
            bitcoin_prompt = f"{system_prompt}\n\nThe user said: {user_input}"

            # Log conversation to file
            self._log_conversation(user_input, bitcoin_prompt)

            # Generate response using Venice AI
            text_generator = TextGenerator()
            
            # Run the async function synchronously
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    text_generator.generate_text(bitcoin_prompt)
                )
                if response and response.strip():
                    response_text = response.strip()
                    # Log AI response
                    self._log_ai_response(response_text)
                    return response_text
                else:
                    fallback_response = "I'm having trouble generating a response right now. Please try again!"
                    # Log the fallback response
                    self._log_ai_response(fallback_response)
                    return fallback_response
            finally:
                loop.close()
            
        except Exception as e:
            logger.error(f"LLM response generation failed: {e}")
            fallback_response = f"Sorry, I'm having trouble connecting to my AI brain right now. Error: {str(e)}"
            # Log the fallback response
            self._log_ai_response(fallback_response)
            return fallback_response
    
    async def process_voice_input(self, audio_input: Union[str, bytes], 
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
                raise Exception("Voice system not initialized")
            
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
            
            # Step 2: Generate Bitcoin response using real LLM
            response_text = await self._generate_bitcoin_response(transcription)
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
    
    async def transcribe_only(self, audio_input: Union[str, bytes], language: str = "en") -> str:
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
    
    async def synthesize_only(self, text: str, voice: str = "default", 
                             language: str = "en", engine: str = "auto") -> bytes:
        """Synthesize text to speech only."""
        try:
            result = self.tts_service.synthesize_speech(text, voice, language, engine)
            return result["audio_data"]
            
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            raise Exception(f"TTS synthesis error: {str(e)}")
    
    async def _generate_bitcoin_response(self, user_input: str) -> str:
        """
        Generate Bitcoin evangelism response using real LLM API.
        Uses Venice AI API with Bitcoin evangelism prompt.
        """
        try:
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
            
            # Create full prompt for logging
            full_prompt = f"System: {system_prompt}\n\nUser: {user_input}"
            
            # Log conversation to file
            self._log_conversation(user_input, full_prompt)
            
            # Use the text generator for real LLM response
            response = await self.text_generator.generate_text(
                prompt=full_prompt,
                model="llama-3.3-70b",
                max_tokens=150,
                temperature=0.7
            )
            
            if response:
                response_text = response.strip()
                # Log AI response
                self._log_ai_response(response_text)
                return response_text
            else:
                error_response = "I'm having trouble thinking right now. Could you ask me again?"
                self._log_ai_response(error_response)
                raise Exception("No response from LLM")
                
        except Exception as e:
            logger.error(f"Bitcoin response generation failed: {e}")
            # Fallback to simple Bitcoin response
            return f"Bitcoin is amazing! It's digital money that gives you financial freedom! 🍊 What would you like to know about Bitcoin?"
    
    def _log_conversation(self, user_input: str, full_prompt: str):
        """Log conversation details to talk.log file."""
        try:
            from datetime import datetime
            log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'talk.log')
            
            with open(log_path, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"\n{'='*80}\n")
                f.write(f"CONVERSATION LOG - {timestamp}\n")
                f.write(f"{'='*80}\n")
                f.write(f"USER TRANSCRIPTION: {user_input}\n")
                f.write(f"{'='*80}\n")
                f.write(f"PROMPT SENT TO AI:\n{full_prompt}\n")
                f.write(f"{'='*80}\n")
                f.flush()
                
        except Exception as e:
            logger.error(f"Failed to log conversation: {e}")
    
    def _log_ai_response(self, ai_response: str):
        """Log AI response to talk.log file."""
        try:
            from datetime import datetime
            log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'talk.log')
            
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"AI RESPONSE: {ai_response}\n")
                f.write(f"{'='*80}\n")
                f.flush()
                
        except Exception as e:
            logger.error(f"Failed to log AI response: {e}")
    
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
async def process_voice_file(audio_path: str, language: str = "en", 
                           tts_voice: str = "default", tts_engine: str = "auto") -> Dict[str, Any]:
    """Process voice file and return transcription + response audio."""
    system = TalkingOrangeVoiceSystem()
    if await system.initialize():
        return await system.process_voice_input(audio_path, language, tts_voice, tts_engine)
    else:
        raise Exception("Failed to initialize Voice System")

async def process_voice_buffer(audio_buffer: bytes, language: str = "en", 
                              tts_voice: str = "default", tts_engine: str = "auto") -> Dict[str, Any]:
    """Process voice buffer and return transcription + response audio."""
    system = TalkingOrangeVoiceSystem()
    if await system.initialize():
        return await system.process_voice_input(audio_buffer, language, tts_voice, tts_engine)
    else:
        raise Exception("Failed to initialize Voice System")

async def transcribe_audio(audio_input: Union[str, bytes], language: str = "en") -> str:
    """Transcribe audio input only."""
    system = TalkingOrangeVoiceSystem()
    if await system.initialize():
        return await system.transcribe_only(audio_input, language)
    else:
        raise Exception("Failed to initialize Voice System")

async def synthesize_speech(text: str, voice: str = "default", 
                           language: str = "en", engine: str = "auto") -> bytes:
    """Synthesize text to speech only."""
    system = TalkingOrangeVoiceSystem()
    if await system.initialize():
        return await system.synthesize_only(text, voice, language, engine)
    else:
        raise Exception("Failed to initialize Voice System")

# Example usage and testing
async def main():
    """Main function for testing the voice system."""
    try:
        print("🍊 Talking Orange Voice System Test")
        print("=" * 40)
        
        # Initialize system
        system = TalkingOrangeVoiceSystem()
        
        if await system.initialize():
            print("✅ Voice System initialized successfully")
            print(f"Status: {system.get_status()}")
            print(f"Available TTS engines: {system.get_available_engines()}")
            print(f"Available voices: {system.get_available_voices()}")
            
            # Test TTS synthesis
            try:
                print("\n🔊 Testing TTS synthesis...")
                audio_data = await system.synthesize_only(
                    "Hello! I am the Talking Orange! 🍊 I'm here to tell you all about Bitcoin!",
                    "default", "en", "auto"
                )
                logger.info(f"✅ TTS synthesis successful: {len(audio_data)} bytes")
            except Exception as e:
                print(f"⚠️ TTS synthesis test failed: {e}")
            
            print("\n🎉 Talking Orange Voice System test completed!")
            
        else:
            print("❌ Voice System initialization failed")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
