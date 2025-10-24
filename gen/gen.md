# AI Content Generation Factory Design Document

## Overview
Modular building blocks extracted from existing character and encounter generators. Each module handles a fundamental AI process (text-to-text, text-to-image, etc.) with inputs determining the specific purpose. These building blocks can be combined to create custom generation workflows.

## Core Philosophy
- **Process-Based Modules**: Each module handles one fundamental AI process type
- **Input-Driven Purpose**: The same module handles different purposes based on inputs
- **Extracted from Existing Code**: Built from actual processes in current generators
- **Composable**: Easy to combine modules for complex workflows

## Fundamental Building Blocks (Based on Existing Code)

### Text-to-Text Module (`text_generator.py`)
**Generic text generation capabilities:**
- Basic text generation
- JSON generation and parsing
- Template-based generation with variable substitution
- Any other text-to-text AI calls

**Key Methods:**
- `generate_text(prompt: str, system_prompt: str, model: str) -> str`
- `generate_json(prompt: str, system_prompt: str, model: str) -> dict/list`
- `generate_with_template(template: str, template_vars: dict) -> str`
- `generate_json_with_template(template: str, template_vars: dict) -> dict/list`

### Text-to-Image Module (`image_generator.py`)
**Generic image generation capabilities:**
- Single image generation
- Batch image generation
- Image downloading and saving
- Any other text-to-image AI calls

**Key Methods:**
- `generate_image(prompt: str, size: str, quality: str, style: str) -> str`
- `generate_images_batch(prompts: list, size: str, quality: str, style: str) -> list`
- `download_image(image_url: str, save_path: str) -> bool`
- `generate_and_save_image(prompt: str, save_path: str) -> bool`

### Utility Modules
- **`api_client.py`**: Standardized API calls to Venice AI - A centralized module that handles all API communication with the Venice AI service, including authentication, request formatting, error handling, and response processing. This consolidates the API call logic from the existing generators into a single, reusable component.

- **`prompt_loader.py`**: Load prompts from prompts/ directory - A utility module that loads and manages prompt templates from the /prompts directory, providing a centralized way to access and modify the various prompt templates used for different AI generation tasks (character generation, encounter creation, image prompts, etc.). This eliminates hardcoded prompts and makes it easy to update templates.

- **`schema_loader.py`**: Load JSON schemas from schemas/ directory - A utility module that loads and validates JSON schemas from the /schemas directory, ensuring that generated content conforms to the expected data structures. This provides validation for character data, encounter data, and other structured content, and makes it easy to update schemas without changing code.

## File Structure
```
/gen/
├── config.json                    # AI service configuration
├── config_manager.py             # Configuration handling
├── character_generator_ai.py     # Current character generation (to be refactored)
├── character_generator_v2.py     # New modular character generation
├── encounter_generator_ai.py     # Current encounter generation (to be refactored)
├── character_manager.py          # Character management utilities
├── encounter.py                  # Encounter management utilities
├── test_character_generator.py   # Test script for character generation
├── gen.md                        # This design document
├── prompts/                      # Prompt templates directory
│   ├── basic_image_prompt_template.txt
│   ├── character_generation_meta.txt
│   ├── encounter_environment_prompt.txt
│   ├── encounter_lore_meta.txt
│   ├── encounter_lore_random_meta.txt
│   ├── lore_generation_meta.txt
│   ├── npc_generation_meta.txt
│   ├── npc_image_prompt_meta.txt
│   ├── profile_picture_prompt_meta.txt
│   ├── random_environment_description.txt
│   ├── random-env-meta-prompt.txt
│   ├── schema_update_prompt.txt
│   └── tactical_positioning_meta.txt
├── schemas/                      # JSON schemas directory
│   ├── character_schema.json
│   ├── character_schema.min.json
│   ├── encounter_schema.json
│   ├── encounter_schema.min.json
│   ├── minify_schema.py
│   └── README.md
├── text_generator.py             # All text-to-text processes (to be created)
├── image_generator.py            # All text-to-image processes (to be created)
├── api_client.py                 # Standardized API calls (to be created)
├── prompt_loader.py              # Prompt loading utilities (to be created)
├── schema_loader.py              # Schema loading utilities (to be created)
├── test/                          # Test output directory
│   └── README.md                 # Test directory documentation
├── text_to_speech.py             # Voice synthesis (future)
├── speech_to_text.py             # Audio transcription (future)
├── text_to_video.py              # Video generation (future)
└── image_to_video.py             # Image-to-video (future)
```

## Usage Pattern
```python
# Import the building blocks
from gen.text_generator import TextGenerator
from gen.image_generator import ImageGenerator
from gen.prompt_loader import prompt_loader
from gen.schema_loader import schema_loader

# Initialize generators
text_gen = TextGenerator()
image_gen = ImageGenerator()

# Generic text generation
text = await text_gen.generate_text("Write a story about a dragon")
json_data = await text_gen.generate_json("Generate a character in JSON format")

# Template-based generation
template = prompt_loader.get_character_generation_prompt()
character_json = await text_gen.generate_json_with_template(
    template, 
    {"character_name": "Aragorn", "character_description": "A ranger"}
)

# Image generation
image_url = await image_gen.generate_image("A majestic dragon in a forest")
images = await image_gen.generate_images_batch(["dragon", "knight", "castle"])

# Download and save
success = await image_gen.generate_and_save_image(
    "A dragon", 
    "/path/to/dragon.jpg"
)
```

## Example Implementation: Character Generator V2

The new `character_generator_v2.py` demonstrates how to use the modular building blocks:

```python
from gen.character_generator_v2 import generate_character_async

# Generate a complete character
character_dir = await generate_character_async(
    "Aragorn",
    "A ranger from the north, heir to the throne of Gondor",
    output_dir="test"
)
```

**Key Features:**
- Uses `text_generator.py` for JSON and lore generation
- Uses `image_generator.py` for profile image generation
- Uses `prompt_loader.py` for prompt templates
- Uses `schema_loader.py` for data validation
- Saves all files to organized directory structure
- Includes progress callbacks and error handling

## Key Benefits
- **Unified Processes**: Same module handles all text or image generation
- **Purpose-Driven**: Inputs determine the specific use case
- **Extracted from Working Code**: Based on actual processes in current generators
- **Composable**: Easy to combine for complex workflows
- **Maintainable**: Single module per process type is easier to optimize
- **Modular**: Project-specific logic separated from generic AI capabilities

## Migration Strategy
1. Extract `make_api_call()` methods into `api_client.py`
2. Extract text generation methods into `text_generator.py`
3. Extract image generation methods into `image_generator.py`
4. Extract prompt/schema loading into utility modules
5. Update existing generators to use new building blocks

This approach provides maximum reusability while maintaining the proven patterns from your existing working code.
