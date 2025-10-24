# AI Content Generation Factory

A modular AI content generation system for creating D&D characters, encounters, and other game content using Venice AI services.

## 🏗️ Architecture

The system is built with modular components that can be used independently or combined for complex workflows:

### Core Modules
- **`api_client.py`** - Centralized API communication with Venice AI
- **`prompt_loader.py`** - Load and format prompt templates
- **`schema_loader.py`** - Load and validate JSON schemas
- **`text_generator.py`** - Text-to-text AI generation
- **`image_generator.py`** - Text-to-image AI generation

### Content Generators
- **`character_generator_v2.py`** - Generate D&D characters with stats, lore, and images
- **`encounter_generator_v2.py`** - Generate encounters with NPCs, environments, and tactical positioning

### Utilities
- **`cli_test.py`** - Interactive command-line interface for testing the system
- **`example_usage.py`** - Code examples for using the modules

## 🚀 Quick Start

### 1. Setup
```bash
# Install dependencies
pip install -r ../requirements.txt

# Set up environment variables
# Create .env file with:
# VENICE_KEY=your_venice_api_key
```

### 2. Run the CLI Test
```bash
python cli_test.py
```

This will start an interactive menu where you can:
- Generate characters with custom descriptions and art styles
- Generate encounters with NPCs, environments, and tactical positioning
- All inputs are automatically saved to the generated content folders

### 3. Use Individual Modules

#### Generate a Character
```python
from character_generator_v2 import CharacterGeneratorV2

async def create_character():
    generator = CharacterGeneratorV2()
    
    character_dir = await generator.generate_character(
        character_name="Aragorn the Ranger",
        character_description="A skilled ranger from the north",
        graphical_style="realistic"
    )
    
    print(f"Character created in: {character_dir}")

# Run the async function
import asyncio
asyncio.run(create_character())
```

#### Generate an Encounter
```python
from encounter_generator_v2 import EncounterGeneratorV2

async def create_encounter():
    generator = EncounterGeneratorV2()
    
    encounter_dir = await generator.generate_encounter(
        encounter_name="Goblin Ambush",
        encounter_description="Goblins attack from the trees",
        difficulty="medium",
        environment="forest",
        graphical_style="fantasy art",
        npc_descriptions="Goblin archer, Goblin warrior, Goblin shaman"
    )
    
    print(f"Encounter created in: {encounter_dir}")

# Run the async function
import asyncio
asyncio.run(create_encounter())
```

## 📁 File Structure

```
gen/
├── api_client.py              # Venice AI API client
├── prompt_loader.py           # Prompt template management
├── schema_loader.py           # JSON schema validation
├── text_generator.py          # Text-to-text AI generation
├── image_generator.py         # Text-to-image AI generation
├── character_generator_v2.py  # Character generation
├── encounter_generator_v2.py  # Encounter generation
├── cli_test.py               # Command-line interface
├── example_usage.py          # Usage examples
├── config.json               # API configuration
├── prompts/                  # Prompt templates
│   ├── character_generation_meta.txt
│   ├── profile_picture_prompt_meta.txt
│   ├── tactical_positioning_meta.txt
│   └── ...
├── schemas/                  # JSON schemas
│   ├── character_schema.json
│   ├── encounter_schema.json
│   └── ...
└── test/                     # Generated content output
    ├── Character_Name_20250906_123456/
    │   ├── character.json
    │   ├── profile_image.webp
    │   ├── lore.md
    │   ├── image_prompt.txt
    │   ├── user_inputs.txt
    │   └── user_inputs.json
    └── Encounter_Name_20250906_123456/
        ├── encounter.json
        ├── environment_image.webp
        ├── lore.md
        ├── npcs.json
        ├── user_inputs.txt
        └── user_inputs.json
```

## 🎯 Content Types

### Characters
Each character generation creates:
- **`character.json`** - Complete D&D 5e character sheet
- **`profile_image.webp`** - AI-generated character portrait
- **`lore.md`** - Character background and story
- **`image_prompt.txt`** - Prompt used for image generation
- **`user_inputs.txt`** - Human-readable input summary
- **`user_inputs.json`** - Machine-readable input data

### Encounters
Each encounter generation creates:
- **`encounter.json`** - Encounter data with tactical positioning
- **`environment_image.webp`** - AI-generated environment image
- **`lore.md`** - Encounter background and context
- **`npcs.json`** - Complete character sheets for all NPCs
- **`user_inputs.txt`** - Human-readable input summary
- **`user_inputs.json`** - Machine-readable input data

## 🖥️ CLI Test Interface

The `cli_test.py` provides an interactive command-line interface for testing the AI content generation system.

### Running the CLI
```bash
python cli_test.py
```

### CLI Features

#### Main Menu
```
============================================================
🎲 AI CONTENT GENERATION FACTORY - CLI TEST
============================================================
Test the modular AI content generation system
============================================================

What would you like to generate?
1. Character
2. Encounter
3. Exit
```

#### Character Generation
When you select option 1, the CLI will prompt for:
- **Character Name**: The name of the character
- **Character Description**: Physical description, background, personality
- **Graphical Style**: Art style for the character image (realistic, anime, pixel art, etc.)

**Example Character Input:**
```
Enter character name: Legolas the Cyborg
Enter character description: A futuristic elf ranger with cybernetic enhancements, wields laser arrows and has a glowing cybernetic eye
Enter graphical style for character image: anime
```

#### Encounter Generation
When you select option 2, the CLI will prompt for:
- **Encounter Name**: Name of the encounter
- **Encounter Description**: What happens in this encounter
- **Environment**: Location type (forest, cave, dungeon, etc.)
- **Difficulty**: Challenge level (easy, medium, hard, deadly)
- **Graphical Style**: Art style for encounter images
- **NPC Descriptions**: Comma-separated list of NPCs to generate

**Example Encounter Input:**
```
Enter encounter name: Goblin Ambush
Enter encounter description: Goblins attack from the trees as the party travels through the forest
Enter environment: forest
Enter difficulty: medium
Enter graphical style: fantasy art
Enter NPC descriptions: Goblin archer, Goblin warrior, Goblin shaman
```

### Generated Content Structure

#### Character Output
Each character generates a folder named `{Character_Name}_{timestamp}/` containing:
- `character.json` - Complete D&D 5e character sheet
- `profile_image.webp` - AI-generated character portrait
- `lore.md` - Character background story
- `image_prompt.txt` - Prompt used for image generation
- `user_inputs.txt` - Human-readable input summary
- `user_inputs.json` - Machine-readable input data

#### Encounter Output
Each encounter generates a folder named `{Encounter_Name}_{timestamp}/` containing:
- `encounter.json` - Encounter data with tactical positioning
- `environment_image.webp` - AI-generated environment image
- `lore.md` - Encounter background and context
- `npcs.json` - Complete character sheets for all NPCs
- `user_inputs.txt` - Human-readable input summary
- `user_inputs.json` - Machine-readable input data

### Progress Tracking
The CLI shows real-time progress for each generation step:
```
  Step 1: Generating character stats and abilities...
  Step 2: Generating character lore...
  Step 3: Generating profile image...
  Step 4: Saving character files...
  Step 5: Character generation complete!
```

### User Input Tracking
All user inputs are automatically saved to both text and JSON formats in the generated content folder, providing complete traceability of what was requested.

### Error Handling
The CLI includes comprehensive error handling:
- API connection issues
- Schema validation errors
- Image generation failures
- File system errors

All errors are logged and displayed to the user with helpful messages.

## 🔧 Customization

### Adding New Content Types
1. Create a new generator class (e.g., `item_generator_v2.py`)
2. Use the core modules (`text_generator`, `image_generator`, etc.)
3. Define your JSON schema in `schemas/`
4. Create prompt templates in `prompts/`
5. Add CLI integration in `cli_test.py`

### Modifying Prompts
Edit files in the `prompts/` directory. Templates support variables like:
- `{character_name}` - Character name
- `{character_description}` - Character description
- `{graphical_style}` - Art style preference
- `{encounter_lore}` - Encounter background
- `{npc_descriptions}` - NPC descriptions

### Custom Schemas
Add JSON schemas to the `schemas/` directory. The system will automatically validate generated content against these schemas.

## 🎨 Supported Art Styles

The system supports various graphical styles for image generation:
- `realistic` - Photorealistic images
- `anime` - Anime/manga style
- `pixel art` - 8-bit pixel art
- `watercolor` - Watercolor painting
- `oil painting` - Oil painting style
- `digital art` - Digital artwork
- `fantasy art` - Fantasy illustration
- And many more!

## 🔍 Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Ensure `.env` file exists with `VENICE_KEY=your_key`
   - Check that the key is valid and has sufficient credits

2. **Schema Validation Errors**
   - Check that your prompt templates include all required schema fields
   - Verify the schema files are properly formatted JSON

3. **Image Generation Fails**
   - Ensure prompts are under 1500 characters for Venice AI
   - Check that the graphical style is supported

4. **Missing Dependencies**
   - Run `pip install -r ../requirements.txt`
   - Ensure you're using Python 3.8+

### Debug Mode
Enable detailed logging by setting the log level:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Examples

See `example_usage.py` for comprehensive code examples showing how to:
- Use individual modules
- Create custom workflows
- Handle errors gracefully
- Process generated content

## 🤝 Contributing

When adding new features:
1. Follow the modular architecture
2. Add comprehensive error handling
3. Include user input tracking
4. Update this README
5. Add examples to `example_usage.py`

## 📄 License

This project is part of the ChatDND system. See the main project for licensing information.
