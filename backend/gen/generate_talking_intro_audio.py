#!/usr/bin/env python3
"""
Generate talking intro audio file for test button.
This creates a static audio file that introduces the talking orange.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import based on where we're running from
try:
    from gen.text_to_voice import synthesize_speech_sync
except ImportError:
    # If running from backend/gen directory
    sys.path.insert(0, str(Path(__file__).parent))
    from text_to_voice import synthesize_speech_sync

def generate_intro_audio(language='en'):
    """Generate and save intro audio file for specified language."""
    
    # Generate intro text based on language
    if language == 'es':
        text = "Hola, soy Satoshka, una naranja parlante. Me gusta mucho bitcoin y sé demasiado sobre él. ¿Te gustaría que te cuente un chiste sobre bitcoin?"
        output_filename = 'talking-intro-es.mp3'
    else:
        text = "Hello, I'm Satoshka, a talking orange. I really like bitcoin and I know way too much about it. Would you like me to tell you a joke about bitcoin?"
        output_filename = 'talking-intro.mp3'
    
    voice = "default"
    engine = "auto"
    
    print(f"🎤 Generating intro audio ({language.upper()}) for: '{text}'")
    print(f"   Voice: {voice}, Language: {language}, Engine: {engine}")
    
    try:
        # Synthesize speech using sync function (uses gTTS which is more reliable)
        result = synthesize_speech_sync(
            text=text,
            voice=voice,
            language=language,
            engine=engine
        )
        
        # Check result
        if not result or not result.get('audio_data'):
            print("❌ Error: No audio data returned from TTS service")
            return False
        
        audio_data = result['audio_data']
        audio_format = result.get('format', 'mp3')
        used_engine = result.get('engine', 'unknown')
        
        print(f"✅ Audio generated successfully using {used_engine} engine")
        print(f"   Format: {audio_format}, Size: {len(audio_data)} bytes")
        
        # Determine output path
        # Save in frontend/media/videos/talking-orange-talking-animation/ to keep with animation frames
        repo_root = Path(__file__).parent.parent.parent
        output_dir = repo_root / 'frontend' / 'media' / 'videos' / 'talking-orange-talking-animation'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / output_filename
        
        # Save audio file
        print(f"💾 Saving audio to: {output_file}")
        with open(output_file, 'wb') as f:
            f.write(audio_data)
        
        file_size = output_file.stat().st_size
        print(f"✅ Successfully saved intro audio ({language.upper()})!")
        print(f"   File: {output_file}")
        print(f"   Size: {file_size} bytes")
        print(f"   Accessible at: ./media/videos/talking-orange-talking-animation/{output_filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating intro audio ({language.upper()}): {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🎭 Talking Orange - Intro Audio Generator")
    print("=" * 60)
    print()
    
    # Generate both English and Spanish versions
    success_en = generate_intro_audio('en')
    print()
    success_es = generate_intro_audio('es')
    
    print()
    if success_en and success_es:
        print("✨ All done! Both intro audio files (EN and ES) are ready.")
    elif success_en:
        print("⚠️  English audio generated, but Spanish audio failed.")
        sys.exit(1)
    elif success_es:
        print("⚠️  Spanish audio generated, but English audio failed.")
        sys.exit(1)
    else:
        print("⚠️  Failed to generate intro audio. Check errors above.")
        sys.exit(1)

