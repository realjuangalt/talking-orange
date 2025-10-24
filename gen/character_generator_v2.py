"""
Character Generator V2
Modular character generation using the new AI content generation factory.
Uses the generic building blocks for text and image generation.
"""

import json
import os
import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from pathlib import Path

try:
    from .text_generator import TextGenerator
    from .image_generator import ImageGenerator
    from .prompt_loader import prompt_loader
    from .schema_loader import schema_loader
except ImportError:
    from text_generator import TextGenerator
    from image_generator import ImageGenerator
    from prompt_loader import prompt_loader
    from schema_loader import schema_loader

# Set up logging
logger = logging.getLogger(__name__)

class CharacterGeneratorV2:
    """Modular character generator using the AI content generation factory."""
    
    def __init__(self, output_dir: str = "test"):
        """
        Initialize the character generator.
        
        Args:
            output_dir: Directory to save generated content (relative to gen/)
        """
        self.text_generator = TextGenerator()
        self.image_generator = ImageGenerator()
        self.output_dir = Path(__file__).parent / output_dir
        self.output_dir.mkdir(exist_ok=True)
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_character(
        self, 
        character_name: str, 
        character_description: str, 
        graphical_style: str = "fantasy art",
        progress_callback: Optional[Callable] = None
    ) -> Optional[str]:
        """
        Generate a complete character using the modular AI factory.
        
        Args:
            character_name: Name of the character
            character_description: Description of the character
            graphical_style: Visual style for image generation (e.g., "fantasy art", "anime", "realistic")
            progress_callback: Optional callback for progress updates
            
        Returns:
            Character directory path if successful, None otherwise
        """
        logger.info(f"Starting character generation for {character_name}")
        
        try:
            # Step 1: Generate character JSON
            if progress_callback:
                progress_callback(1, "Generating character stats and abilities...")
            
            character_json = await self.generate_character_json(character_name, character_description)
            if not character_json:
                logger.error("Failed to generate character JSON")
                return None
            
            # Step 2: Generate character lore
            if progress_callback:
                progress_callback(2, "Generating character lore...")
            
            character_lore = await self.generate_character_lore(character_json)
            if not character_lore:
                logger.warning("Failed to generate character lore")
                character_lore = "No lore generated."
            
            # Step 3: Generate profile image
            if progress_callback:
                progress_callback(3, "Generating profile image...")
            
            # Generate image prompt first
            image_prompt = await self.generate_profile_image_prompt(character_json, character_lore)
            if not image_prompt:
                logger.warning("Failed to generate profile image prompt")
                image_prompt = "No image prompt generated."
            
            # Generate the actual image
            profile_image_url = await self.image_generator.generate_image(prompt=image_prompt)
            
            # Step 4: Create character directory and save files
            if progress_callback:
                progress_callback(4, "Saving character files...")
            
            character_dir = await self.save_character_files(
                character_name, character_json, character_lore, profile_image_url, image_prompt
            )
            
            if progress_callback:
                progress_callback(5, "Character generation complete!")
            
            logger.info(f"Character generation completed successfully: {character_dir}")
            return str(character_dir)
            
        except Exception as e:
            logger.error(f"Error generating character: {str(e)}")
            return None
    
    async def generate_character_json(
        self, 
        character_name: str, 
        character_description: str
    ) -> Optional[Dict[str, Any]]:
        """
        Generate character JSON using the modular text generator.
        
        Args:
            character_name: Name of the character
            character_description: Description of the character
            
        Returns:
            Character JSON data or None if failed
        """
        try:
            # Get character generation prompt template
            prompt_template = prompt_loader.get_character_generation_prompt()
            
            # Get character schema
            character_schema = schema_loader.get_character_schema()
            schema_text = json.dumps(character_schema, indent=2)
            
            # Generate JSON using the text generator with template
            character_data = await self.text_generator.generate_json_with_template(
                prompt_template,
                {
                    "character_name": character_name,
                    "character_description": character_description,
                    "character_schema": schema_text
                }
            )
            
            # Validate the generated data
            if not schema_loader.validate_character_data(character_data):
                errors = schema_loader.get_character_validation_errors(character_data)
                logger.error(f"Generated character data is invalid: {errors}")
                return None
            
            logger.info("Character JSON generated successfully")
            return character_data
            
        except Exception as e:
            logger.error(f"Error generating character JSON: {str(e)}")
            return None
    
    async def generate_character_lore(
        self, 
        character_json: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate character lore using the modular text generator.
        
        Args:
            character_json: Character data dictionary
            
        Returns:
            Generated lore text or None if failed
        """
        try:
            # Get lore generation prompt template
            prompt_template = prompt_loader.get_lore_generation_prompt()
            
            # Format the prompt with character data
            prompt = prompt_loader.format_prompt(
                prompt_template,
                character_name=character_json.get("name", ""),
                character_description=character_json.get("description", ""),
                character_background=character_json.get("background", ""),
                character_personality=character_json.get("personality", ""),
                character_json=json.dumps(character_json, indent=2)
            )
            
            # Generate lore using the text generator
            lore = await self.text_generator.generate_text(prompt)
            
            logger.info("Character lore generated successfully")
            return lore
            
        except Exception as e:
            logger.error(f"Error generating character lore: {str(e)}")
            return None
    
    async def generate_profile_image(
        self, 
        character_json: Dict[str, Any],
        character_lore: str
    ) -> Optional[str]:
        """
        Generate profile image using the modular image generator.
        Uses two-step process: first generate image prompt, then generate image.
        
        Args:
            character_json: Character data dictionary
            character_lore: The character lore text
            
        Returns:
            Base64 image data or None if failed
        """
        try:
            # Step 1: Generate image prompt using text AI
            image_prompt = await self.generate_profile_image_prompt(character_json, character_lore)
            if not image_prompt:
                logger.warning("Failed to generate profile image prompt")
                return None
            
            # Step 2: Generate the actual image
            image_data = await self.image_generator.generate_image(
                prompt=image_prompt
            )
            
            if image_data:
                logger.info("Profile image generated successfully")
                return image_data
            else:
                logger.warning("Failed to generate profile image")
                return None
                
        except Exception as e:
            logger.error(f"Error generating profile image: {str(e)}")
            return None
    
    async def generate_profile_image_prompt(
        self, 
        character_json: Dict[str, Any],
        character_lore: str
    ) -> Optional[str]:
        """
        Generate profile image prompt using text AI.
        
        Args:
            character_json: The character JSON data
            character_lore: The character lore text
            
        Returns:
            Generated image prompt or None if failed
        """
        try:
            # Get profile image prompt template
            prompt_template = prompt_loader.get_profile_picture_prompt()
            
            # Generate image prompt using the text generator
            image_prompt = await self.text_generator.generate_with_template(
                prompt_template,
                {
                    "character_lore": character_lore,
                    "character_json": json.dumps(character_json, indent=2)
                }
            )
            
            if image_prompt:
                logger.info("Profile image prompt generated successfully")
                return image_prompt
            else:
                logger.warning("Failed to generate profile image prompt")
                return None
                
        except Exception as e:
            logger.error(f"Error generating profile image prompt: {str(e)}")
            return None
    
    async def save_character_files(
        self,
        character_name: str,
        character_json: Dict[str, Any],
        character_lore: str,
        profile_image_url: Optional[str],
        image_prompt: str
    ) -> Path:
        """
        Save all character files to the output directory.
        
        Args:
            character_name: Name of the character
            character_json: Character JSON data
            character_lore: Character lore text
            profile_image_url: URL of the profile image
            
        Returns:
            Path to the character directory
        """
        # Create character directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        character_dir_name = f"{character_name}_{timestamp}"
        character_dir = self.output_dir / character_dir_name
        character_dir.mkdir(exist_ok=True)
        
        # Save character JSON
        character_file = character_dir / "character.json"
        with open(character_file, 'w', encoding='utf-8') as f:
            json.dump(character_json, f, indent=2, ensure_ascii=False)
        
        # Save character lore
        lore_file = character_dir / "lore.md"
        with open(lore_file, 'w', encoding='utf-8') as f:
            f.write(character_lore)
        
        # Save image prompt for reference
        if profile_image_url:
            prompt_file = character_dir / "image_prompt.txt"
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(image_prompt)
            
            # Save the base64 image data
            image_file = character_dir / "profile_image.webp"
            try:
                import base64
                image_data = base64.b64decode(profile_image_url)
                with open(image_file, 'wb') as f:
                    f.write(image_data)
                logger.info(f"Profile image saved to {image_file}")
            except Exception as e:
                logger.warning(f"Failed to save profile image to {image_file}: {e}")
        
        logger.info(f"Character files saved to {character_dir}")
        return character_dir

# Convenience functions for easy usage
async def generate_character_async(
    character_name: str,
    character_description: str,
    output_dir: str = "test",
    progress_callback: Optional[Callable] = None
) -> Optional[str]:
    """
    Generate a complete character asynchronously.
    
    Args:
        character_name: Name of the character
        character_description: Description of the character
        output_dir: Directory to save generated content
        progress_callback: Optional callback for progress updates
        
    Returns:
        Character directory path if successful, None otherwise
    """
    generator = CharacterGeneratorV2(output_dir)
    return await generator.generate_character(character_name, character_description, progress_callback)

def generate_character(
    character_name: str,
    character_description: str,
    output_dir: str = "test",
    progress_callback: Optional[Callable] = None
) -> Optional[str]:
    """
    Generate a complete character synchronously.
    
    Args:
        character_name: Name of the character
        character_description: Description of the character
        output_dir: Directory to save generated content
        progress_callback: Optional callback for progress updates
        
    Returns:
        Character directory path if successful, None otherwise
    """
    return asyncio.run(generate_character_async(character_name, character_description, output_dir, progress_callback))

# Example usage and testing
if __name__ == "__main__":
    async def test_character_generation():
        """Test the character generation system."""
        
        def progress_callback(step: int, message: str):
            print(f"Step {step}: {message}")
        
        # Test character generation
        character_name = "Test Character"
        character_description = "A brave warrior from the northern lands"
        
        print(f"Generating character: {character_name}")
        result = await generate_character_async(
            character_name, 
            character_description, 
            progress_callback=progress_callback
        )
        
        if result:
            print(f"Character generated successfully: {result}")
        else:
            print("Character generation failed")
    
    # Run the test
    asyncio.run(test_character_generation())
