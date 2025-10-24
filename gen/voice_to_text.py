"""
Voice to Text Module
Handles audio transcription using Whisper with local model support.
Optimized for Talking Orange AR project with Bitcoin evangelism focus.
"""

import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import whisper
import torch
import pydub

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceToTextService:
    """
    Voice to Text service using Whisper for audio transcription.
    Supports local models and GPU/CPU fallback for optimal performance.
    """
    
    def __init__(self, model_dir: str = None, model_name: str = "small"):
        self.model_dir = model_dir or os.getenv('MODEL_DIR', '/opt/jarvis_editor/2.0/models')
        self.model_name = model_name or os.getenv('WHISPER_MODEL_NAME', 'small')
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.use_fp16 = self.device == "cuda"
        
        # Ensure model directory exists
        os.makedirs(self.model_dir, exist_ok=True)
        
    def initialize(self):
        """Initialize the Whisper model."""
        try:
            logger.info(f"Loading Whisper model '{self.model_name}' from {self.model_dir} on device={self.device}")
            
            # Load model with fallback
            try:
                self.model = whisper.load_model(
                    self.model_name, 
                    download_root=self.model_dir, 
                    device=self.device
                )
            except Exception as e:
                logger.warning(f"Failed to load Whisper on {self.device}: {e}. Falling back to CPU.")
                self.device = "cpu"
                self.use_fp16 = False
                self.model = whisper.load_model(
                    self.model_name, 
                    download_root=self.model_dir, 
                    device=self.device
                )
            
            logger.info(f"Whisper model loaded successfully on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Whisper model: {e}")
            return False
    
    def transcribe_audio(self, audio_path: str, language: str = "en") -> Dict[str, Any]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            language: Language code (default: 'en')
            
        Returns:
            Dict with transcription results
        """
        try:
            if not self.model:
                raise Exception("Whisper model not initialized")
            
            # Check if audio file exists
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Get audio metadata
            try:
                audio_seg = pydub.AudioSegment.from_file(audio_path)
                duration_sec = round(len(audio_seg) / 1000.0, 2)
                logger.info(f"Transcribing audio: {audio_path}, duration: {duration_sec}s")
            except Exception as e:
                logger.warning(f"Could not read audio metadata: {e}")
            
            # Transcribe audio
            import time
            start_time = time.time()
            
            result = self.model.transcribe(
                audio_path, 
                fp16=self.use_fp16, 
                verbose=True,
                language=language if language != "auto" else None
            )
            
            elapsed_time = round(time.time() - start_time, 2)
            logger.info(f"Transcription completed in {elapsed_time}s")
            
            return {
                "text": result["text"].strip(),
                "language": result.get("language", language),
                "duration": elapsed_time,
                "confidence": 0.9,  # Whisper doesn't provide confidence scores
                "model": self.model_name,
                "device": self.device
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise Exception(f"Transcription error: {str(e)}")
    
    def transcribe_audio_buffer(self, audio_buffer: bytes, language: str = "en") -> Dict[str, Any]:
        """
        Transcribe audio from buffer.
        
        Args:
            audio_buffer: Audio data as bytes
            language: Language code (default: 'en')
            
        Returns:
            Dict with transcription results
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_buffer)
                temp_path = temp_file.name
            
            try:
                # Transcribe the temporary file
                result = self.transcribe_audio(temp_path, language)
                return result
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file: {e}")
                    
        except Exception as e:
            logger.error(f"Buffer transcription failed: {e}")
            raise Exception(f"Buffer transcription error: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            "initialized": self.model is not None,
            "model_name": self.model_name,
            "model_dir": self.model_dir,
            "device": self.device,
            "use_fp16": self.use_fp16
        }

# Convenience functions for easy usage
def transcribe_audio_file(audio_path: str, model_name: str = "small", language: str = "en") -> str:
    """Transcribe audio file and return text."""
    service = VoiceToTextService(model_name=model_name)
    if service.initialize():
        result = service.transcribe_audio(audio_path, language)
        return result["text"]
    else:
        raise Exception("Failed to initialize VoiceToTextService")

def transcribe_audio_buffer(audio_buffer: bytes, model_name: str = "small", language: str = "en") -> str:
    """Transcribe audio buffer and return text."""
    service = VoiceToTextService(model_name=model_name)
    if service.initialize():
        result = service.transcribe_audio_buffer(audio_buffer, language)
        return result["text"]
    else:
        raise Exception("Failed to initialize VoiceToTextService")

# Example usage
if __name__ == "__main__":
    # Test the service
    service = VoiceToTextService()
    
    if service.initialize():
        print("✅ VoiceToTextService initialized successfully")
        print(f"Status: {service.get_status()}")
    else:
        print("❌ VoiceToTextService initialization failed")
