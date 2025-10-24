#!/usr/bin/env python3
"""
Command Line Interface for testing AI Content Generation Factory
"""

import asyncio
import logging
import os
import sys
from typing import Optional, Dict

# Add the gen directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from character_generator_v2 import CharacterGeneratorV2
from encounter_generator_v2 import EncounterGeneratorV2

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

class ContentGenerationCLI:
    """Command line interface for content generation testing."""
    
    def __init__(self):
        self.character_generator = CharacterGeneratorV2()
        self.encounter_generator = EncounterGeneratorV2()
    
    def print_header(self):
        """Print the CLI header."""
        print("=" * 60)
        print("🎲 AI CONTENT GENERATION FACTORY - CLI TEST")
        print("=" * 60)
        print("Test the modular AI content generation system")
        print("=" * 60)
    
    def get_user_choice(self) -> str:
        """Get user's choice of what to generate."""
        print("\nWhat would you like to generate?")
        print("1. Character")
        print("2. Encounter")
        print("3. Exit")
        
        while True:
            choice = input("\nEnter your choice (1-3): ").strip()
            if choice in ['1', '2', '3']:
                return choice
            print("❌ Invalid choice. Please enter 1, 2, or 3.")
    
    def get_character_inputs(self) -> tuple[str, str, str]:
        """Get character generation inputs from user."""
        print("\n" + "=" * 40)
        print("🧙‍♂️ CHARACTER GENERATION")
        print("=" * 40)
        
        name = input("Enter character name: ").strip()
        while not name:
            print("❌ Character name cannot be empty.")
            name = input("Enter character name: ").strip()
        
        description = input("Enter character description: ").strip()
        while not description:
            print("❌ Character description cannot be empty.")
            description = input("Enter character description: ").strip()
        
        print("\nGraphical style examples: realistic, anime, pixel art, watercolor, oil painting, digital art, fantasy art, etc.")
        style = input("Enter graphical style for character image: ").strip()
        if not style:
            style = "fantasy art"  # Default style
            print(f"Using default style: {style}")
        
        return name, description, style
    
    def get_encounter_inputs(self) -> tuple[str, str, str, str, str, str]:
        """Get encounter generation inputs from user."""
        print("\n" + "=" * 40)
        print("🗡️ ENCOUNTER GENERATION")
        print("=" * 40)
        
        name = input("Enter encounter name: ").strip()
        while not name:
            print("❌ Encounter name cannot be empty.")
            name = input("Enter encounter name: ").strip()
        
        description = input("Enter encounter description: ").strip()
        while not description:
            print("❌ Encounter description cannot be empty.")
            description = input("Enter encounter description: ").strip()
        
        environment = input("Enter environment (e.g., forest, cave, dungeon): ").strip()
        while not environment:
            print("❌ Environment cannot be empty.")
            environment = input("Enter environment: ").strip()
        
        print("\nDifficulty levels: easy, medium, hard, deadly")
        difficulty = input("Enter difficulty: ").strip().lower()
        while difficulty not in ['easy', 'medium', 'hard', 'deadly']:
            print("❌ Invalid difficulty. Choose: easy, medium, hard, deadly")
            difficulty = input("Enter difficulty: ").strip().lower()
        
        print("\nGraphical style examples: realistic, anime, pixel art, watercolor, oil painting, digital art, fantasy art, etc.")
        style = input("Enter graphical style for encounter images: ").strip()
        if not style:
            style = "fantasy art"  # Default style
            print(f"Using default style: {style}")
        
        print("\nNPC descriptions (comma-separated, e.g., 'Ancient mummy priest, Desert warrior, Sand elemental'):")
        npc_descriptions = input("Enter NPC descriptions: ").strip()
        if not npc_descriptions:
            npc_descriptions = "Enemy warrior, Enemy mage, Enemy rogue"  # Default NPCs
            print(f"Using default NPCs: {npc_descriptions}")
        
        return name, description, environment, difficulty, style, npc_descriptions
    
    def progress_callback(self, step: int, message: str):
        """Progress callback for generation processes."""
        print(f"  Step {step}: {message}")
    
    async def generate_character(self, name: str, description: str, style: str) -> Optional[str]:
        """Generate a character and return the directory path."""
        print(f"\n🎭 Generating character: {name}")
        print(f"📝 Description: {description}")
        print(f"🎨 Style: {style}")
        print("-" * 50)
        
        try:
            character_dir = await self.character_generator.generate_character(
                character_name=name,
                character_description=description,
                graphical_style=style,
                progress_callback=self.progress_callback
            )
            
            if character_dir:
                # Save user inputs to file
                await self.save_user_inputs(character_dir, "character", {
                    "name": name,
                    "description": description,
                    "graphical_style": style
                })
                
                print(f"\n✅ Character generated successfully!")
                print(f"📁 Directory: {character_dir}")
                
                # List created files
                if os.path.exists(character_dir):
                    files = os.listdir(character_dir)
                    print(f"📄 Files: {', '.join(files)}")
                
                return character_dir
            else:
                print("\n❌ Character generation failed!")
                return None
                
        except Exception as e:
            print(f"\n❌ Character generation error: {str(e)}")
            logger.exception("Character generation failed")
            return None
    
    async def generate_encounter(self, name: str, description: str, environment: str, difficulty: str, style: str, npc_descriptions: str) -> Optional[str]:
        """Generate an encounter and return the directory path."""
        print(f"\n⚔️ Generating encounter: {name}")
        print(f"📍 Environment: {environment}")
        print(f"💀 Difficulty: {difficulty}")
        print(f"📝 Description: {description}")
        print(f"🎨 Style: {style}")
        print(f"👥 NPCs: {npc_descriptions}")
        print("-" * 50)
        
        try:
            encounter_dir = await self.encounter_generator.generate_encounter(
                encounter_name=name,
                encounter_description=description,
                difficulty=difficulty,
                environment=environment,
                graphical_style=style,
                npc_descriptions=npc_descriptions,
                progress_callback=self.progress_callback
            )
            
            if encounter_dir:
                # Save user inputs to file
                await self.save_user_inputs(encounter_dir, "encounter", {
                    "name": name,
                    "description": description,
                    "environment": environment,
                    "difficulty": difficulty,
                    "graphical_style": style,
                    "npc_descriptions": npc_descriptions
                })
                
                print(f"\n✅ Encounter generated successfully!")
                print(f"📁 Directory: {encounter_dir}")
                
                # List created files
                if os.path.exists(encounter_dir):
                    files = os.listdir(encounter_dir)
                    print(f"📄 Files: {', '.join(files)}")
                
                return encounter_dir
            else:
                print("\n❌ Encounter generation failed!")
                return None
                
        except Exception as e:
            print(f"\n❌ Encounter generation error: {str(e)}")
            logger.exception("Encounter generation failed")
            return None
    
    async def save_user_inputs(self, content_dir: str, content_type: str, inputs: Dict[str, str]) -> None:
        """
        Save user inputs to a file in the content directory.
        
        Args:
            content_dir: Directory where content was generated
            content_type: Type of content (character, encounter)
            inputs: Dictionary of user inputs
        """
        try:
            import json
            from datetime import datetime
            
            # Create user inputs data
            user_inputs_data = {
                "content_type": content_type,
                "generated_at": datetime.now().isoformat(),
                "user_inputs": inputs
            }
            
            # Save to file
            inputs_file = os.path.join(content_dir, "user_inputs.txt")
            with open(inputs_file, 'w') as f:
                f.write(f"# User Inputs for {content_type.title()} Generation\n")
                f.write(f"Generated at: {user_inputs_data['generated_at']}\n\n")
                
                for key, value in inputs.items():
                    f.write(f"{key.replace('_', ' ').title()}: {value}\n")
            
            # Also save as JSON for programmatic access
            json_file = os.path.join(content_dir, "user_inputs.json")
            with open(json_file, 'w') as f:
                json.dump(user_inputs_data, f, indent=2)
            
            logger.info(f"User inputs saved to {inputs_file} and {json_file}")
            
        except Exception as e:
            logger.error(f"Failed to save user inputs: {str(e)}")
    
    async def run(self):
        """Main CLI loop."""
        self.print_header()
        
        while True:
            choice = self.get_user_choice()
            
            if choice == '1':  # Character
                name, description, style = self.get_character_inputs()
                await self.generate_character(name, description, style)
                
            elif choice == '2':  # Encounter
                name, description, environment, difficulty, style, npc_descriptions = self.get_encounter_inputs()
                await self.generate_encounter(name, description, environment, difficulty, style, npc_descriptions)
                
            elif choice == '3':  # Exit
                print("\n👋 Goodbye!")
                break
            
            # Ask if user wants to continue
            print("\n" + "=" * 60)
            continue_choice = input("Would you like to generate something else? (y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes']:
                print("\n👋 Goodbye!")
                break

async def main():
    """Main entry point."""
    cli = ContentGenerationCLI()
    await cli.run()

if __name__ == "__main__":
    asyncio.run(main())
