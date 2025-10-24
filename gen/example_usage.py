"""
Example usage of the modular AI content generation factory.
Demonstrates how to use the building blocks for different purposes.
"""

import asyncio
import logging
from text_generator import TextGenerator
from image_generator import ImageGenerator
from prompt_loader import prompt_loader
from schema_loader import schema_loader

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def example_text_generation():
    """Example of using the text generator for various purposes."""
    print("📝 TEXT GENERATION EXAMPLES")
    print("=" * 50)
    
    text_gen = TextGenerator()
    
    # 1. Basic text generation
    print("\n1. Basic text generation:")
    story = await text_gen.generate_text("Write a short story about a dragon and a knight")
    print(f"Story: {story[:100]}...")
    
    # 2. JSON generation
    print("\n2. JSON generation:")
    character_data = await text_gen.generate_json(
        "Generate a fantasy character in JSON format with name, class, and level"
    )
    print(f"Character: {character_data}")
    
    # 3. Template-based generation
    print("\n3. Template-based generation:")
    template = "Create a {character_type} named {name} who is {description}"
    character = await text_gen.generate_with_template(
        template,
        {
            "character_type": "wizard",
            "name": "Gandalf",
            "description": "wise and powerful"
        }
    )
    print(f"Character description: {character}")
    
    # 4. Template-based JSON generation
    print("\n4. Template-based JSON generation:")
    character_json = await text_gen.generate_json_with_template(
        template,
        {
            "character_type": "warrior",
            "name": "Aragorn",
            "description": "a ranger from the north"
        }
    )
    print(f"Character JSON: {character_json}")

async def example_image_generation():
    """Example of using the image generator for various purposes."""
    print("\n🖼️ IMAGE GENERATION EXAMPLES")
    print("=" * 50)
    
    image_gen = ImageGenerator()
    
    # 1. Single image generation
    print("\n1. Single image generation:")
    image_url = await image_gen.generate_image("A majestic dragon in a fantasy forest")
    print(f"Image URL: {image_url[:50]}...")
    
    # 2. Batch image generation
    print("\n2. Batch image generation:")
    prompts = [
        "A brave knight in shining armor",
        "A wise wizard with a long beard",
        "A mystical forest with ancient trees"
    ]
    image_urls = await image_gen.generate_images_batch(prompts)
    print(f"Generated {len(image_urls)} images")
    
    # 3. Generate and save image
    print("\n3. Generate and save image:")
    success = await image_gen.generate_and_save_image(
        "A fantasy castle on a mountain peak",
        "test/fantasy_castle.webp"
    )
    print(f"Image saved: {success}")

async def example_using_prompts_and_schemas():
    """Example of using the prompt and schema loaders."""
    print("\n📋 PROMPT AND SCHEMA EXAMPLES")
    print("=" * 50)
    
    # 1. Load prompts
    print("\n1. Loading prompts:")
    character_prompt = prompt_loader.get_character_generation_prompt()
    print(f"Character prompt length: {len(character_prompt)} characters")
    
    lore_prompt = prompt_loader.get_lore_generation_prompt()
    print(f"Lore prompt length: {len(lore_prompt)} characters")
    
    # 2. Load schemas
    print("\n2. Loading schemas:")
    character_schema = schema_loader.get_character_schema()
    print(f"Character schema has {len(character_schema.get('required', []))} required fields")
    
    encounter_schema = schema_loader.get_encounter_schema()
    print(f"Encounter schema has {len(encounter_schema.get('required', []))} required fields")
    
    # 3. Validate data
    print("\n3. Data validation:")
    test_character = {
        "name": "Test Character",
        "class": "Warrior",
        "level": 1
    }
    is_valid = schema_loader.validate_character_data(test_character)
    print(f"Test character is valid: {is_valid}")
    
    if not is_valid:
        errors = schema_loader.get_character_validation_errors(test_character)
        print(f"Validation errors: {errors}")

async def example_character_generation_workflow():
    """Example of a complete character generation workflow."""
    print("\n🧙‍♂️ COMPLETE CHARACTER GENERATION WORKFLOW")
    print("=" * 50)
    
    text_gen = TextGenerator()
    image_gen = ImageGenerator()
    
    # 1. Generate character using template
    print("\n1. Generating character JSON:")
    character_template = prompt_loader.get_character_generation_prompt()
    character_schema = schema_loader.get_character_schema()
    
    character_json = await text_gen.generate_json_with_template(
        character_template,
        {
            "character_name": "Aragorn",
            "character_description": "A ranger from the north, heir to the throne of Gondor",
            "character_schema": str(character_schema)
        }
    )
    print(f"Generated character: {character_json.get('name', 'Unknown')}")
    
    # 2. Generate character lore
    print("\n2. Generating character lore:")
    lore_template = prompt_loader.get_lore_generation_prompt()
    lore = await text_gen.generate_with_template(
        lore_template,
        {
            "character_name": character_json.get("name", ""),
            "character_description": character_json.get("description", ""),
            "character_background": character_json.get("background", ""),
            "character_personality": character_json.get("personality", ""),
            "character_json": str(character_json)
        }
    )
    print(f"Generated lore: {lore[:100]}...")
    
    # 3. Generate profile image
    print("\n3. Generating profile image:")
    image_template = prompt_loader.get_profile_picture_prompt()
    image_prompt = prompt_loader.format_prompt(
        image_template,
        character_name=character_json.get("name", ""),
        character_description=character_json.get("description", ""),
        character_race=character_json.get("race", ""),
        character_class=character_json.get("class", "")
    )
    
    image_url = await image_gen.generate_image(image_prompt)
    print(f"Generated image: {image_url[:50]}...")
    
    print("\n✅ Complete character generation workflow finished!")

async def main():
    """Main example function."""
    print("🚀 AI CONTENT GENERATION FACTORY EXAMPLES")
    print("=" * 60)
    
    try:
        await example_text_generation()
        await example_image_generation()
        await example_using_prompts_and_schemas()
        await example_character_generation_workflow()
        
        print("\n🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {str(e)}")
        logger.error(f"Example error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
