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
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceToTextService:
    """
    Voice to Text service using Whisper for audio transcription.
    Supports local models and GPU/CPU fallback for optimal performance.
    """
    
    def __init__(self, model_dir: str = None, model_name: str = "medium"):
        self.model_dir = model_dir or os.getenv('MODEL_DIR', str(Path(__file__).parent.parent / 'models'))
        self.model_name = model_name or os.getenv('WHISPER_MODEL_NAME', 'medium')
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
        temp_path = None
        try:
            # Validate audio buffer
            if not audio_buffer or len(audio_buffer) < 100:
                raise ValueError("Audio buffer is too small or empty")
            
            logger.info(f"Processing audio buffer: {len(audio_buffer)} bytes")
            
            # Create temporary file with WebM extension (frontend sends WebM format)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
                temp_file.write(audio_buffer)
                temp_path = temp_file.name
            
            logger.info(f"Created temporary audio file: {temp_path}")
            
            # Check if file was written successfully
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                raise ValueError("Failed to write audio to temporary file")
            
            try:
                # Try to load with pydub to validate format
                try:
                    audio_seg = pydub.AudioSegment.from_file(temp_path)
                    duration_sec = round(len(audio_seg) / 1000.0, 2)
                    logger.info(f"Audio validated: duration={duration_sec}s, sample_rate={audio_seg.frame_rate}")
                except Exception as pydub_error:
                    logger.warning(f"pydub validation failed: {pydub_error}, but continuing with Whisper")
                
                # Transcribe the temporary file
                result = self.transcribe_audio(temp_path, language)
                return result
                
            except Exception as transcription_error:
                logger.error(f"Transcription error: {transcription_error}")
                # Try to convert format using ffmpeg if available
                try:
                    converted_path = self._convert_audio_format(temp_path)
                    if converted_path:
                        logger.info(f"Using converted audio: {converted_path}")
                        result = self.transcribe_audio(converted_path, language)
                        # Clean up converted file
                        try:
                            os.unlink(converted_path)
                        except:
                            pass
                        return result
                    else:
                        raise transcription_error
                except Exception as convert_error:
                    logger.error(f"Audio conversion failed: {convert_error}")
                    raise transcription_error
                    
        except Exception as e:
            logger.error(f"Buffer transcription failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Buffer transcription error: {str(e)}")
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    logger.info(f"Cleaned up temporary file: {temp_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to delete temporary file {temp_path}: {cleanup_error}")
    
    def _convert_audio_format(self, input_path: str, output_format: str = 'wav') -> Optional[str]:
        """Convert audio file to a different format using ffmpeg."""
        try:
            # Check if ffmpeg is available
            result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning("ffmpeg not found, cannot convert audio")
                return None
            
            # Create output file path
            output_path = input_path.rsplit('.', 1)[0] + '.' + output_format
            
            # Convert audio using ffmpeg
            cmd = [
                'ffmpeg', '-y',  # Overwrite output file
                '-i', input_path,
                '-ar', '16000',  # Resample to 16kHz (Whisper's preferred rate)
                '-ac', '1',      # Mono channel
                output_path
            ]
            
            logger.info(f"Converting audio: ffmpeg {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(f"Audio converted successfully to: {output_path}")
                return output_path
            else:
                logger.error(f"ffmpeg conversion failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            return None
    
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
def transcribe_audio_file(audio_path: str, model_name: str = "medium", language: str = "en") -> str:
    """Transcribe audio file and return text."""
    service = VoiceToTextService(model_name=model_name)
    if service.initialize():
        result = service.transcribe_audio(audio_path, language)
        return result["text"]
    else:
        raise Exception("Failed to initialize VoiceToTextService")

def transcribe_audio_buffer(audio_buffer: bytes, model_name: str = "medium", language: str = "en") -> str:
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
