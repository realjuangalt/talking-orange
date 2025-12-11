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
    
    def __init__(self, model_dir: str = None, model_name: str = None):
        self.model_dir = model_dir or os.getenv('MODEL_DIR', str(Path(__file__).parent.parent / 'models'))
        self.model_name = model_name or os.getenv('WHISPER_MODEL_NAME', 'medium')
        self.model = None
        
        # Check if CPU is forced via environment variable
        force_cpu = os.getenv('WHISPER_FORCE_CPU', 'false').lower() == 'true'
        if force_cpu:
            self.device = "cpu"
            logger.info("🔧 CPU mode forced via WHISPER_FORCE_CPU environment variable")
        else:
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                self.device = "cuda"
                cuda_device_count = torch.cuda.device_count()
                cuda_device_name = torch.cuda.get_device_name(0) if cuda_device_count > 0 else "Unknown"
                logger.info(f"🚀 GPU mode enabled - CUDA available")
                logger.info(f"   CUDA devices: {cuda_device_count}")
                logger.info(f"   GPU device: {cuda_device_name}")
                
                # Check GPU memory availability
                try:
                    for i in range(cuda_device_count):
                        props = torch.cuda.get_device_properties(i)
                        total_mem = props.total_memory / (1024**3)  # GB
                        allocated = torch.cuda.memory_allocated(i) / (1024**3)  # GB
                        reserved = torch.cuda.memory_reserved(i) / (1024**3)  # GB
                        free = total_mem - reserved
                        logger.info(f"   GPU {i} memory: {total_mem:.2f} GB total, {reserved:.2f} GB reserved, {free:.2f} GB free")
                        
                        # Warn if less than 1GB free (Whisper models need ~1-2GB)
                        if free < 1.0:
                            logger.warning(f"⚠️  GPU {i} has low free memory ({free:.2f} GB) - may fail to load model")
                            logger.warning(f"   Consider: 1) Free GPU memory, 2) Use smaller model, 3) Use CPU mode")
                except Exception as mem_error:
                    logger.warning(f"⚠️  Could not check GPU memory: {mem_error}")
            else:
                self.device = "cpu"
                logger.warning("⚠️  GPU requested but CUDA not available - falling back to CPU")
                logger.info("   Install PyTorch with CUDA support to use GPU")
        self.use_fp16 = self.device == "cuda"
        logger.info(f"🎯 Whisper will use device: {self.device} (FP16: {self.use_fp16})")
        
        # Ensure model directory exists
        os.makedirs(self.model_dir, exist_ok=True)
        
    def initialize(self):
        """Initialize the Whisper model. Automatically downloads if missing."""
        try:
            # Ensure model directory exists and is absolute
            self.model_dir = os.path.abspath(self.model_dir)
            os.makedirs(self.model_dir, exist_ok=True)
            
            # Verify directory is writable
            if not os.access(self.model_dir, os.W_OK):
                logger.warning(f"⚠️ Model directory is not writable: {self.model_dir}")
                logger.warning(f"   Models may be downloaded to default cache location instead")
            
            # Check if model file exists
            model_path = os.path.join(self.model_dir, f"{self.model_name}.pt")
            model_exists = os.path.exists(model_path)
            
            logger.info(f"🔍 Checking for Whisper model '{self.model_name}' in {self.model_dir}")
            
            if model_exists:
                file_size = os.path.getsize(model_path) / (1024 * 1024)  # Size in MB
                logger.info(f"📦 Whisper model '{self.model_name}.pt' found ({file_size:.1f} MB)")
            else:
                logger.info(f"📥 Whisper model '{self.model_name}.pt' not found")
                logger.info(f"   Download location: {self.model_dir}")
                logger.info(f"   Whisper will download automatically when loading...")
                logger.info(f"   This may take a few minutes depending on model size...")
            
            logger.info(f"🔄 Loading Whisper model '{self.model_name}' on device={self.device}")
            logger.info(f"   Using download_root: {self.model_dir}")
            
            # Load model with fallback - Whisper will auto-download if missing
            # Whisper automatically downloads models from HuggingFace if not found locally
            try:
                import time
                load_start = time.time()
                
                # Verify model name is valid
                try:
                    available_models = whisper.available_models()
                    if self.model_name not in available_models:
                        logger.error(f"❌ Invalid model name '{self.model_name}'. Available models: {available_models}")
                        raise ValueError(f"Model '{self.model_name}' not in available models: {available_models}")
                    logger.info(f"✅ Model name '{self.model_name}' is valid")
                except Exception as model_check_error:
                    logger.warning(f"⚠️ Could not verify model name: {model_check_error}")
                
                logger.info(f"📥 Calling whisper.load_model('{self.model_name}', download_root='{self.model_dir}', device='{self.device}')")
                self.model = whisper.load_model(
                    self.model_name, 
                    download_root=self.model_dir, 
                    device=self.device
                )
                load_duration = time.time() - load_start
                
                # Check if model was downloaded
                if not model_exists:
                    # Check again after loading
                    if os.path.exists(model_path):
                        file_size = os.path.getsize(model_path) / (1024 * 1024)  # Size in MB
                        logger.info(f"✅ Whisper model '{self.model_name}' downloaded ({file_size:.1f} MB) and loaded in {load_duration:.1f}s")
                    else:
                        # Check Whisper's default cache location
                        default_cache = os.path.expanduser("~/.cache/whisper")
                        default_model_path = os.path.join(default_cache, f"{self.model_name}.pt")
                        if os.path.exists(default_model_path):
                            logger.warning(f"⚠️ Model downloaded to default cache: {default_model_path}")
                            logger.info(f"   Copying to {self.model_dir}...")
                            try:
                                import shutil
                                shutil.copy2(default_model_path, model_path)
                                logger.info(f"✅ Model copied to {model_path}")
                            except Exception as copy_error:
                                logger.warning(f"⚠️ Could not copy model: {copy_error}")
                        else:
                            logger.warning(f"⚠️ Model file not found at {model_path} or default cache")
                            logger.info(f"   Model may be loaded in memory or using a different path")
                elif model_exists:
                    logger.info(f"✅ Whisper model '{self.model_name}' loaded from cache in {load_duration:.1f}s")
                    
            except Exception as e:
                error_str = str(e)
                logger.warning(f"⚠️ Failed to load Whisper on {self.device}: {e}")
                
                # Check if it's a CUDA out of memory error
                if "CUDA out of memory" in error_str or "out of memory" in error_str.lower():
                    logger.error("❌ CUDA Out of Memory Error")
                    logger.error("   The GPU doesn't have enough free memory to load the Whisper model")
                    logger.error("   Solutions:")
                    logger.error("   1. Free GPU memory (close other GPU applications)")
                    logger.error("   2. Use a smaller model (small instead of medium)")
                    logger.error("   3. Use CPU mode: ./start_local.sh --device cpu")
                    logger.error("   4. Clear GPU cache: python3 -c 'import torch; torch.cuda.empty_cache()'")
                
                logger.info("🔄 Attempting to load on CPU as fallback...")
                self.device = "cpu"
                self.use_fp16 = False
                try:
                    import time
                    load_start = time.time()
                    self.model = whisper.load_model(
                        self.model_name, 
                        download_root=self.model_dir, 
                        device=self.device
                    )
                    load_duration = time.time() - load_start
                    logger.info(f"✅ Whisper model loaded successfully on CPU (fallback) in {load_duration:.1f}s")
                except Exception as fallback_error:
                    logger.error(f"❌ Failed to load Whisper on CPU: {fallback_error}")
                    import traceback
                    logger.error(f"❌ Traceback: {traceback.format_exc()}")
                    raise fallback_error
            
            # Verify model was loaded
            if self.model is None:
                raise Exception("Model is None after loading")
            
            # Final verification - check if model file exists now
            if os.path.exists(model_path):
                file_size = os.path.getsize(model_path) / (1024 * 1024)
                logger.info(f"✅ Whisper model '{self.model_name}' initialized successfully")
                logger.info(f"   Model file: {model_path} ({file_size:.1f} MB)")
                logger.info(f"   Device: {self.device.upper()} ({'FP16 enabled' if self.use_fp16 else 'FP32'})")
                if self.device == "cuda":
                    logger.info(f"   GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Unknown'}")
            else:
                logger.warning(f"⚠️ Model file not found at expected path: {model_path}")
                logger.info(f"   Model may be in Whisper's default cache location")
                logger.info(f"   Device: {self.device.upper()} ({'FP16 enabled' if self.use_fp16 else 'FP32'})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Whisper model: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
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
            logger.info(f"🎤 [WHISPER] Starting transcription with model.transcribe()...")
            logger.info(f"🎤 [WHISPER] Parameters: fp16={self.use_fp16}, language={language}, device={self.device}")
            
            result = self.model.transcribe(
                audio_path, 
                fp16=self.use_fp16, 
                verbose=True,
                language=language if language != "auto" else None
            )
            
            elapsed_time = round(time.time() - start_time, 2)
            transcription_text = result.get("text", "").strip()
            detected_language = result.get("language", "unknown")
            
            logger.info(f"✅ [WHISPER] Transcription completed in {elapsed_time}s")
            logger.info(f"📝 [WHISPER] Detected language: {detected_language}")
            logger.info(f"📝 [WHISPER] Transcription text: '{transcription_text[:100]}...' (length: {len(transcription_text)})")
            logger.info(f"📊 [WHISPER] Result keys: {list(result.keys())}")
            
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
            logger.info(f"🎤 [WHISPER] Starting transcription...")
            logger.info(f"🎤 [WHISPER] Model: {self.model_name}, Device: {self.device}, FP16: {self.use_fp16}")
            logger.info(f"🎤 [WHISPER] Language: {language}")
            
            # Validate audio buffer
            if not audio_buffer or len(audio_buffer) < 100:
                raise ValueError("Audio buffer is too small or empty")
            
            logger.info(f"🎤 [WHISPER] Processing audio buffer: {len(audio_buffer)} bytes")
            
            # Check model is ready
            if not self.model:
                logger.error(f"❌ [WHISPER] Model is None! Model initialized: {hasattr(self, 'model')}")
                raise Exception("Whisper model not initialized")
            
            logger.info(f"✅ [WHISPER] Model object exists: {type(self.model)}")
            
            # Create temporary file with WebM extension (frontend sends WebM format)
            logger.info(f"📁 [WHISPER] Creating temporary audio file...")
            import time
            temp_start = time.time()
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
                temp_file.write(audio_buffer)
                temp_path = temp_file.name
            
            temp_duration = round(time.time() - temp_start, 2)
            file_size = os.path.getsize(temp_path)
            logger.info(f"✅ [WHISPER] Created temporary audio file in {temp_duration}s: {temp_path} ({file_size} bytes)")
            
            # Check if file was written successfully
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                logger.error(f"❌ [WHISPER] Failed to write audio to temporary file: {temp_path}")
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
                logger.info(f"🎤 [WHISPER] Calling transcribe_audio() on temporary file...")
                result = self.transcribe_audio(temp_path, language)
                logger.info(f"✅ [WHISPER] Transcription result received: {len(result.get('text', ''))} characters")
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
