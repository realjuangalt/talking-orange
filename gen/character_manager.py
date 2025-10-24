import json
import os
import logging
from typing import Dict, Any, Optional

class CharacterManager:
    def __init__(self):
        self.characters_dir = "characters"
        self.ensure_characters_directory()
        
    def ensure_characters_directory(self):
        """Ensure the characters directory exists"""
        if not os.path.exists(self.characters_dir):
            os.makedirs(self.characters_dir)
            
    def create_character(self, character_data: Dict[str, Any]) -> bool:
        """Create a new character and save to file"""
        try:
            character_name = character_data.get('name', 'Unknown')
            
            # Create base character file
            base_filename = f"base-{character_name}.json"
            base_path = os.path.join(self.characters_dir, base_filename)
            
            # Create character file
            char_filename = f"{character_name}.json"
            char_path = os.path.join(self.characters_dir, char_filename)
            
            # Save base character data
            with open(base_path, 'w') as f:
                json.dump(character_data, f, indent=2)
                
            # Save current character data (same as base initially)
            with open(char_path, 'w') as f:
                json.dump(character_data, f, indent=2)
                
            logging.info(f"Character {character_name} created successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error creating character: {e}")
            return False
            
    def load_character(self, character_name: str) -> Optional[Dict[str, Any]]:
        """Load a character from file"""
        try:
            char_filename = f"{character_name}.json"
            
            # First try to find the character in subdirectories (new structure)
            if os.path.exists(self.characters_dir):
                for item in os.listdir(self.characters_dir):
                    item_path = os.path.join(self.characters_dir, item)
                    if os.path.isdir(item_path):
                        char_path = os.path.join(item_path, char_filename)
                        if os.path.exists(char_path):
                            with open(char_path, 'r') as f:
                                character_data = json.load(f)
                            logging.info(f"Character {character_name} loaded successfully from {item_path}")
                            return character_data
            
            # Fallback to flat file structure (legacy)
            char_path = os.path.join(self.characters_dir, char_filename)
            if os.path.exists(char_path):
                with open(char_path, 'r') as f:
                    character_data = json.load(f)
                logging.info(f"Character {character_name} loaded successfully")
                return character_data
            else:
                logging.warning(f"Character file {char_filename} not found in any subdirectory or root")
                return None
                
        except Exception as e:
            logging.error(f"Error loading character {character_name}: {e}")
            return None
            
    def save_character(self, character_name: str, character_data: Dict[str, Any]) -> bool:
        """Save character data to file"""
        try:
            char_filename = f"{character_name}.json"
            char_path = os.path.join(self.characters_dir, char_filename)
            
            with open(char_path, 'w') as f:
                json.dump(character_data, f, indent=2)
                
            logging.info(f"Character {character_name} saved successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error saving character {character_name}: {e}")
            return False
            
    def get_all_characters(self) -> list:
        """Get list of all available characters"""
        try:
            characters = []
            if os.path.exists(self.characters_dir):
                for item in os.listdir(self.characters_dir):
                    item_path = os.path.join(self.characters_dir, item)
                    if os.path.isdir(item_path):
                        # Check if this directory contains a character JSON file
                        for filename in os.listdir(item_path):
                            if filename.endswith('.json') and not filename.startswith('base-'):
                                character_name = filename[:-5]  # Remove .json extension
                                characters.append(character_name)
                                break
                    elif item.endswith('.json') and not item.startswith('base-'):
                        # Legacy support for flat file structure
                        character_name = item[:-5]  # Remove .json extension
                        characters.append(character_name)
            return characters
            
        except Exception as e:
            logging.error(f"Error getting character list: {e}")
            return []
            
    def delete_character(self, character_name: str) -> bool:
        """Delete a character and its files"""
        try:
            base_filename = f"base-{character_name}.json"
            char_filename = f"{character_name}.json"
            
            base_path = os.path.join(self.characters_dir, base_filename)
            char_path = os.path.join(self.characters_dir, char_filename)
            
            # Delete both files if they exist
            if os.path.exists(base_path):
                os.remove(base_path)
            if os.path.exists(char_path):
                os.remove(char_path)
                
            logging.info(f"Character {character_name} deleted successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error deleting character {character_name}: {e}")
            return False
            
    def reset_character_to_base(self, character_name: str) -> bool:
        """Reset character data to base values"""
        try:
            base_filename = f"base-{character_name}.json"
            char_filename = f"{character_name}.json"
            
            base_path = os.path.join(self.characters_dir, base_filename)
            char_path = os.path.join(self.characters_dir, char_filename)
            
            if os.path.exists(base_path) and os.path.exists(char_path):
                # Load base data
                with open(base_path, 'r') as f:
                    base_data = json.load(f)
                    
                # Save as current character data
                with open(char_path, 'w') as f:
                    json.dump(base_data, f, indent=2)
                    
                logging.info(f"Character {character_name} reset to base values")
                return True
            else:
                logging.warning(f"Base or character file not found for {character_name}")
                return False
                
        except Exception as e:
            logging.error(f"Error resetting character {character_name}: {e}")
            return False 