import json
import os
import logging
import random
from typing import Dict, Any, Optional, List

class EncounterManager:
    def __init__(self):
        self.encounters_dir = "encounters"
        self.ensure_encounters_directory()
        
        # Predefined encounter templates
        self.encounter_templates = {
            'forest': {
                'environment': 'A dense forest with ancient trees and thick underbrush',
                'enemies': ['Goblin', 'Wolf', 'Bandit'],
                'difficulty': 'easy'
            },
            'cave': {
                'environment': 'A dark cave with stalactites and mysterious sounds',
                'enemies': ['Kobold', 'Giant Spider', 'Cave Bear'],
                'difficulty': 'medium'
            },
            'dungeon': {
                'environment': 'A stone dungeon with torches and ancient runes',
                'enemies': ['Skeleton', 'Orc', 'Troll'],
                'difficulty': 'hard'
            },
            'tavern': {
                'environment': 'A rowdy tavern with dim lighting and wooden tables',
                'enemies': ['Drunk Patron', 'Thief', 'Bounty Hunter'],
                'difficulty': 'easy'
            }
        }
        
    def ensure_encounters_directory(self):
        """Ensure the encounters directory exists"""
        if not os.path.exists(self.encounters_dir):
            os.makedirs(self.encounters_dir)
            
    def create_encounter(self, environment: str, enemies: List[str], difficulty: str = 'medium') -> Dict[str, Any]:
        """Create a new encounter"""
        encounter_data = {
            'id': self.generate_encounter_id(),
            'environment': environment,
            'enemies': enemies,
            'difficulty': difficulty,
            'status': 'pending',
            'created_at': self.get_timestamp()
        }
        
        return encounter_data
        
    def save_encounter(self, encounter_data: Dict[str, Any]) -> bool:
        """Save encounter data to file"""
        try:
            encounter_id = encounter_data.get('id', 'unknown')
            filename = f"encounter-{encounter_id}.json"
            filepath = os.path.join(self.encounters_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(encounter_data, f, indent=2)
                
            logging.info(f"Encounter {encounter_id} saved successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error saving encounter: {e}")
            return False
            
    def load_encounter(self, encounter_id: str) -> Optional[Dict[str, Any]]:
        """Load encounter data from file"""
        try:
            filename = f"encounter-{encounter_id}.json"
            filepath = os.path.join(self.encounters_dir, filename)
            
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    encounter_data = json.load(f)
                logging.info(f"Encounter {encounter_id} loaded successfully")
                return encounter_data
            else:
                logging.warning(f"Encounter file {filepath} not found")
                return None
                
        except Exception as e:
            logging.error(f"Error loading encounter {encounter_id}: {e}")
            return None
            
    def generate_random_encounter(self) -> Dict[str, Any]:
        """Generate a random encounter using templates"""
        try:
            # Select random template
            template_key = random.choice(list(self.encounter_templates.keys()))
            template = self.encounter_templates[template_key]
            
            # Generate random enemies
            num_enemies = random.randint(1, 3)
            selected_enemies = random.sample(template['enemies'], min(num_enemies, len(template['enemies'])))
            
            # Create encounter
            encounter_data = self.create_encounter(
                environment=template['environment'],
                enemies=selected_enemies,
                difficulty=template['difficulty']
            )
            
            logging.info(f"Random encounter generated: {encounter_data['id']}")
            return encounter_data
            
        except Exception as e:
            logging.error(f"Error generating random encounter: {e}")
            return self.create_encounter("Unknown location", ["Unknown enemy"])
            
    def start_encounter(self, encounter_data: Dict[str, Any]) -> bool:
        """Start an encounter"""
        try:
            encounter_data['status'] = 'active'
            encounter_data['started_at'] = self.get_timestamp()
            
            # Save updated encounter data
            return self.save_encounter(encounter_data)
            
        except Exception as e:
            logging.error(f"Error starting encounter: {e}")
            return False
            
    def end_encounter(self, encounter_data: Dict[str, Any], result: str = 'completed') -> bool:
        """End an encounter"""
        try:
            encounter_data['status'] = 'completed'
            encounter_data['result'] = result
            encounter_data['ended_at'] = self.get_timestamp()
            
            # Save updated encounter data
            return self.save_encounter(encounter_data)
            
        except Exception as e:
            logging.error(f"Error ending encounter: {e}")
            return False
            
    def get_all_encounters(self) -> List[Dict[str, Any]]:
        """Get list of all encounters"""
        try:
            encounters = []
            if os.path.exists(self.encounters_dir):
                for filename in os.listdir(self.encounters_dir):
                    if filename.startswith('encounter-') and filename.endswith('.json'):
                        filepath = os.path.join(self.encounters_dir, filename)
                        with open(filepath, 'r') as f:
                            encounter_data = json.load(f)
                            encounters.append(encounter_data)
            return encounters
            
        except Exception as e:
            logging.error(f"Error getting encounter list: {e}")
            return []
            
    def delete_encounter(self, encounter_id: str) -> bool:
        """Delete an encounter file"""
        try:
            filename = f"encounter-{encounter_id}.json"
            filepath = os.path.join(self.encounters_dir, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                logging.info(f"Encounter {encounter_id} deleted successfully")
                return True
            else:
                logging.warning(f"Encounter file {filepath} not found")
                return False
                
        except Exception as e:
            logging.error(f"Error deleting encounter {encounter_id}: {e}")
            return False
            
    def generate_encounter_id(self) -> str:
        """Generate a unique encounter ID"""
        import time
        import uuid
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        return f"{timestamp}-{unique_id}"
        
    def get_timestamp(self) -> str:
        """Get current timestamp as string"""
        from datetime import datetime
        return datetime.now().isoformat()
        
    def validate_encounter_data(self, encounter_data: Dict[str, Any]) -> bool:
        """Validate encounter data structure"""
        required_fields = ['environment', 'enemies']
        
        for field in required_fields:
            if field not in encounter_data:
                logging.error(f"Missing required field: {field}")
                return False
                
        if not isinstance(encounter_data['enemies'], list):
            logging.error("Enemies field must be a list")
            return False
            
        if len(encounter_data['enemies']) == 0:
            logging.error("Enemies list cannot be empty")
            return False
            
        return True 