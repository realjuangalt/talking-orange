#!/usr/bin/env python3
"""
Encounter Generator V2
A fully modular encounter generation system using the AI Content Generation Factory.
Leverages all core modules for clean, maintainable code.
"""

import json
import os
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime as dt

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import our modular building blocks
try:
    from .api_client import VeniceAPIClient
    from .text_generator import TextGenerator
    from .image_generator import ImageGenerator
    from .prompt_loader import PromptLoader
    from .schema_loader import SchemaLoader
except ImportError:
    from api_client import VeniceAPIClient
    from text_generator import TextGenerator
    from image_generator import ImageGenerator
    from prompt_loader import PromptLoader
    from schema_loader import SchemaLoader

# Import configuration
try:
    from core.server.config_manager import ConfigManager
except ImportError:
    try:
        from config_manager import ConfigManager
    except ImportError:
        # Fallback for when running from gen directory
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core', 'server'))
        from config_manager import ConfigManager

class EncounterGeneratorV2:
    """
    Fully modular encounter generator using the AI Content Generation Factory.
    Generates encounters with NPCs, environment descriptions, and tactical positioning.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize modular components
        self.text_generator = TextGenerator()
        self.image_generator = ImageGenerator()
        self.prompt_loader = PromptLoader()
        self.schema_loader = SchemaLoader()
        
        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        
        # Set up logging for encounter generation
        self.user_inputs_logger = logging.getLogger('user_inputs')
        self.input_prompts_logger = logging.getLogger('user_prompts')
        self.ai_outputs_logger = logging.getLogger('ai_outputs')
        self.ai_inputs_logger = logging.getLogger('ai_inputs')
        
        # Set up paths
        self.root_dir = os.path.dirname(__file__)  # gen/ directory
        self.data_dir = os.path.join(os.path.dirname(self.root_dir), "data")
    
    def is_npc_images_enabled(self) -> bool:
        """Check if NPC images generation is enabled"""
        game_settings = self.config.get('game_settings', {})
        return game_settings.get('npc_images_enabled', False)
    
    def create_encounter_folder(self, session_id: str) -> str:
        """Create encounter folder using session ID - simple and reliable"""
        try:
            folder_name = f"encounter_{session_id}"
            folder_path = os.path.join(self.data_dir, "encounters", folder_name)
            os.makedirs(folder_path, exist_ok=True)
            self.logger.debug(f"Created encounter folder: {folder_path}")
            return folder_path
        except Exception as e:
            self.logger.error(f"Failed to create encounter folder: {e}")
            raise
    
    def _determine_combat_role(self, character: Dict[str, Any]) -> str:
        """Determine the combat role of a character based on their class and abilities"""
        class_type = character.get("class_type", "").lower()
        
        if class_type in ["fighter", "barbarian", "paladin"]:
            return "frontline"
        elif class_type in ["wizard", "sorcerer", "warlock"]:
            return "backline"
        elif class_type in ["cleric", "druid", "bard"]:
            return "midline"
        elif class_type in ["rogue", "monk", "ranger"]:
            return "flexible"
        else:
            return "balanced"
    
    def _determine_range_type(self, character: Dict[str, Any]) -> str:
        """Determine the range type of a character based on their class and abilities"""
        class_type = character.get("class_type", "").lower()
        
        if class_type in ["fighter", "barbarian", "paladin", "monk"]:
            return "melee"
        elif class_type in ["wizard", "sorcerer", "warlock"]:
            return "magic"
        elif class_type in ["ranger", "rogue"]:
            return "ranged"
        elif class_type in ["cleric", "druid", "bard"]:
            return "mixed"
        else:
            return "balanced"
    
    async def generate_encounter_positions(self, npcs_data: Dict[str, Any], encounter_lore: str, 
                                        environment: str, progress_callback=None) -> Optional[Dict[str, Any]]:
        """Generate tactical positioning for encounter using AI"""
        try:
            # Create minimal NPC summaries for positioning generation
            npc_summaries = []
            if npcs_data and 'npcs' in npcs_data:
                for npc in npcs_data['npcs']:
                    summary = {
                        "name": npc.get("name", "Unknown"),
                        "class_type": npc.get("class_type", "fighter"),
                        "hp": npc.get("hp", 10),
                        "ac": npc.get("ac", 10),
                        "speed": npc.get("speed", 30),
                        "combat_role": self._determine_combat_role(npc),
                        "range_type": self._determine_range_type(npc)
                    }
                    npc_summaries.append(summary)
            
            # Create sample player character summaries for positioning
            sample_players = [
                {"name": "Fighter", "class_type": "fighter", "combat_role": "frontline", "range_type": "melee"},
                {"name": "Wizard", "class_type": "wizard", "combat_role": "backline", "range_type": "magic"},
                {"name": "Cleric", "class_type": "cleric", "combat_role": "midline", "range_type": "magic"},
                {"name": "Rogue", "class_type": "rogue", "combat_role": "flexible", "range_type": "ranged"}
            ]
            
            # Load encounter schema for validation
            encounter_schema = self.schema_loader.get_encounter_schema_min()
            
            # Use text generator with template for positioning
            positioning_data = await self.text_generator.generate_json_with_template(
                template=self.prompt_loader.get_tactical_positioning_prompt(),
                variables={
                    "encounter_lore": encounter_lore,
                    "environment": environment,
                    "npcs_summary": json.dumps(npc_summaries, indent=2),
                    "sample_players": json.dumps(sample_players, indent=2)
                },
                schema=encounter_schema,
                model="gpt-4o-mini",
                max_tokens=2000,
                temperature=0.3
            )
            
            if positioning_data:
                self.logger.info(f"Successfully generated encounter positioning data")
                return positioning_data
            else:
                self.logger.error("Failed to generate positioning data")
                return None
                
        except Exception as e:
            self.logger.error(f"Positioning generation failed: {e}")
            return None
    
    async def generate_encounter(self, environment: str = None, enemies: str = None, progress_callback=None, session_id: str = None) -> Optional[str]:
        """Generate a complete encounter using AI - unified method for both random and custom encounters"""
        self.logger.info(f"[DEBUG] generate_encounter called with session_id: {session_id}")
        self.user_inputs_logger.info(f"[DEBUG] generate_encounter called with session_id: {session_id}")
        
        # Determine if this is a custom or random encounter
        is_custom = environment is not None and enemies is not None
        encounter_type = "custom" if is_custom else "random"
        
        # Log user input in encounter generator
        if is_custom:
            self.user_inputs_logger.info(f"ENCOUNTER GENERATOR - Processing: Environment='{environment}', Enemies='{enemies}'")
        else:
            self.user_inputs_logger.info("RANDOM ENCOUNTER GENERATOR - Processing random encounter with no user input")
        
        try:
            # CREATE FOLDER IMMEDIATELY at the start - before any generation
            folder_path = self.create_encounter_folder(session_id)
            self.user_inputs_logger.info(f"Created encounter folder at start: {folder_path}")
            
            # Log encounter generation start
            if is_custom:
                self.user_inputs_logger.info(f"Custom Encounter Generation Started - Environment: {environment}, Enemies: {enemies}")
            else:
                self.user_inputs_logger.info("Random Encounter Generation Started")
            
            # Step 1: Generate environment image prompt
            if progress_callback:
                progress_callback(1, "Creating environment description...")
            self.user_inputs_logger.info("Step 1: Generating environment image prompt")
            
            if is_custom:
                env_image_prompt = await self.generate_environment_image_prompt_from_input(environment)
            else:
                env_image_prompt = await self.generate_environment_image_prompt()
                
            if not env_image_prompt:
                self.ai_outputs_logger.error("Failed to generate environment image prompt")
                return None
            self.ai_outputs_logger.info(f"Environment Image Prompt: {env_image_prompt}")
            
            # Save environment image prompt IMMEDIATELY after generation
            prompt_file_path = os.path.join(folder_path, "environment_image_prompt.txt")
            with open(prompt_file_path, 'w') as f:
                f.write(env_image_prompt)
            self.user_inputs_logger.info(f"Environment image prompt saved immediately: {prompt_file_path}")
            
            # Step 2: Generate environment image
            if progress_callback:
                progress_callback(2, "Generating environment image...")
            self.user_inputs_logger.info("Step 2: Generating environment image")
            env_image_data = await self.generate_environment_image(env_image_prompt)
            if not env_image_data:
                self.ai_outputs_logger.error("Failed to generate environment image")
            else:
                self.ai_outputs_logger.info("Environment image generated (image data not logged)")
                # Save environment image IMMEDIATELY after generation
                image_file_path = os.path.join(folder_path, "environment_background.webp")
                import base64
                try:
                    image_data = base64.b64decode(env_image_data)
                    with open(image_file_path, 'wb') as f:
                        f.write(image_data)
                    self.user_inputs_logger.info(f"Environment image saved immediately: {image_file_path}")
                except Exception as e:
                    self.logger.error(f"Failed to save environment image: {e}")
            
            # Step 3: Generate encounter lore
            if progress_callback:
                progress_callback(3, "Creating encounter lore...")
            self.user_inputs_logger.info("Step 3: Generating encounter lore")
            
            if is_custom:
                encounter_lore = await self.generate_encounter_lore_with_input(env_image_prompt, environment, enemies)
            else:
                encounter_lore = await self.generate_encounter_lore(env_image_prompt)
                
            if not encounter_lore:
                self.ai_outputs_logger.error("Failed to generate encounter lore")
                return None
            self.ai_outputs_logger.info(f"Encounter Lore: {encounter_lore}")
            
            # --- Clean up AI response: remove code block markers ---
            cleaned_lore = encounter_lore.strip()
            if cleaned_lore.startswith('```json'):
                cleaned_lore = cleaned_lore[7:]
            if cleaned_lore.startswith('```'):
                cleaned_lore = cleaned_lore[3:]
            if cleaned_lore.endswith('```'):
                cleaned_lore = cleaned_lore[:-3]
            cleaned_lore = cleaned_lore.strip()

            # Parse encounter lore JSON to extract lore text
            lore_text = cleaned_lore  # Default to cleaned response
            
            import re
            try:
                # Try to parse as JSON
                lore_data = json.loads(cleaned_lore)
                if isinstance(lore_data, dict):
                    lore_text = lore_data.get('lore', cleaned_lore)
                    self.user_inputs_logger.info(f"Extracted lore text: {lore_text[:100]}...")
            except (json.JSONDecodeError, TypeError) as e:
                self.user_inputs_logger.info(f"Could not parse lore as JSON: {e}")
                # Try to extract lore using regex (multiline, robust)
                lore_match = re.search(r'"lore"\s*:\s*"([^"]+)"', cleaned_lore, re.DOTALL)
                if lore_match:
                    lore_text = lore_match.group(1)
                    self.user_inputs_logger.info(f"Extracted lore using regex: {lore_text[:100]}...")

            # Save encounter lore IMMEDIATELY after processing
            lore_file_path = os.path.join(folder_path, "encounter_lore.md")
            with open(lore_file_path, 'w') as f:
                f.write(lore_text)
            self.user_inputs_logger.info(f"Encounter lore saved immediately: {lore_file_path}")
            
            # Extract encounter name from lore (like character generation does)
            encounter_name = self.extract_encounter_name(encounter_lore, environment)  # Now always has a value
            self.user_inputs_logger.info(f"Extracted encounter name: {encounter_name}")
            
            # Save user prompt input IMMEDIATELY after folder creation
            user_prompt_path = os.path.join(folder_path, "user_prompt.txt")
            if is_custom:
                user_prompt_content = f"Environment: {environment}\nEnemies: {enemies}"
            else:
                # For random encounters, include the generated environment
                user_prompt_content = f"Random Encounter: AI generated environment - {environment}\nEnemies: Random enemies based on environment"
            with open(user_prompt_path, 'w') as f:
                f.write(user_prompt_content)
            self.user_inputs_logger.info(f"User prompt saved immediately: {user_prompt_path}")
            
            # Step 4: Generate NPCs
            if progress_callback:
                progress_callback(4, "Creating hostile NPCs...")
            self.user_inputs_logger.info("Step 4: Generating hostile NPCs")
            npcs_data = await self.generate_encounter_npcs(encounter_lore, folder_path, progress_callback)
            if not npcs_data:
                self.ai_outputs_logger.error("Failed to generate NPCs")
                return None
            self.ai_outputs_logger.info(f"NPCs JSON: {json.dumps(npcs_data)[:500]}... (truncated)")
            
            # Save NPCs data IMMEDIATELY after generation
            npcs_file_path = os.path.join(folder_path, "npcs.json")
            with open(npcs_file_path, 'w') as f:
                json.dump(npcs_data, f, indent=2)
            self.user_inputs_logger.info(f"NPCs data saved immediately: {npcs_file_path}")
            
            # Step 5: Generate NPC images (if enabled)
            if self.is_npc_images_enabled():
                if progress_callback:
                    progress_callback(5, "Generating NPC images...")
                self.user_inputs_logger.info("Step 5: Generating NPC images")
                await self.generate_npc_images(npcs_data, folder_path, progress_callback)
            
            # Step 6: Generate encounter positioning
            if progress_callback:
                progress_callback(6, "Generating tactical positioning...")
            self.user_inputs_logger.info("Step 6: Generating encounter positioning")
            
            positioning_data = await self.generate_encounter_positions(npcs_data, encounter_lore, environment, progress_callback)
            if positioning_data:
                # Save positioning data to encounter.json
                encounter_file_path = os.path.join(folder_path, "encounter.json")
                with open(encounter_file_path, 'w') as f:
                    json.dump(positioning_data, f, indent=2)
                self.user_inputs_logger.info(f"Encounter positioning data saved: {encounter_file_path}")
                self.ai_outputs_logger.info(f"Encounter positioning generated successfully")
            else:
                self.logger.warning("Failed to generate positioning data, continuing without positioning")
                self.user_inputs_logger.info("Positioning generation failed, continuing without positioning")
            
            # Note: All files are now saved immediately as they're generated
            # No need for bulk saving at the end

            # Create encounter summary
            encounter_data = {
                "name": encounter_name,
                "environment": environment,  # Now always has a value (custom or generated)
                "npc_count": len(npcs_data.get('npcs', [])) if isinstance(npcs_data, dict) else 0,
                "difficulty": "Medium",  # Default difficulty
                "description": lore_text[:200] + "..." if len(lore_text) > 200 else lore_text,
                "environment_image": "environment_background.webp" if env_image_data else None,
                "lore": lore_text,
                "npcs": npcs_data,
                "generated_at": dt.now().isoformat()
            }

            encounter_summary_path = os.path.join(folder_path, "encounter_summary.json")
            with open(encounter_summary_path, 'w') as f:
                json.dump(encounter_data, f, indent=2)
            self.user_inputs_logger.info(f"Encounter summary saved to: {encounter_summary_path}")
            
            self.user_inputs_logger.info(f"{encounter_type.capitalize()} encounter generation completed successfully: {folder_path}")
            self.user_inputs_logger.info(f"[DEBUG] About to return folder_path for session_id: {session_id}")
            # Return the folder path instead of encounter data (like character generation)
            return folder_path
        except Exception as e:
            self.logger.error(f"Encounter generation failed: {e}")
            self.ai_outputs_logger.error(f"Encounter generation failed: {e}")
            self.user_inputs_logger.error(f"[DEBUG] Exception in generate_encounter for session_id {session_id}: {e}")
            return None
    
    async def generate_random_encounter(self, progress_callback=None, session_id: str = None) -> Optional[str]:
        """Generate a complete random encounter using AI - compatibility method for server"""
        try:
            # Generate a random environment description using text generator
            random_environment = await self.text_generator.generate_text(
                prompt=self.prompt_loader.get_random_environment_prompt(),
                model="gpt-4o-mini",
                max_tokens=500,
                temperature=0.7
            )
            
            if not random_environment:
                self.logger.error("Failed to generate random environment description")
                return None
                
            self.logger.info(f"Generated random environment: {random_environment[:100]}...")
            
            # Now call the main generate_encounter method with the generated environment
            return await self.generate_encounter(random_environment, "Random enemies based on environment", progress_callback, session_id)
            
        except Exception as e:
            self.logger.error(f"Random encounter generation failed: {e}")
            return None
    
    async def generate_environment_image_prompt(self) -> Optional[str]:
        """Generate environment image prompt using AI"""
        try:
            return await self.text_generator.generate_text(
                prompt=self.prompt_loader.get_random_env_meta_prompt(),
                model="gpt-4o-mini",
                max_tokens=1000,
                temperature=0.7
            )
        except Exception as e:
            self.logger.error(f"Environment image prompt generation failed: {e}")
            return None

    async def generate_environment_image_prompt_from_input(self, environment: str) -> Optional[str]:
        """Generate environment image prompt from user input"""
        try:
            return await self.text_generator.generate_with_template(
                template=self.prompt_loader.get_encounter_environment_prompt(),
                variables={"user_environment": environment},
                model="gpt-4o-mini",
                max_tokens=1000,
                temperature=0.7
            )
        except Exception as e:
            self.logger.error(f"Environment image prompt generation from input failed: {e}")
            return None
            
    async def generate_environment_image(self, image_prompt: str) -> Optional[str]:
        """Generate environment image using AI"""
        try:
            return await self.image_generator.generate_image(
                prompt=image_prompt,
                size="1024x1024",
                quality="standard",
                style="vivid"
            )
        except Exception as e:
            self.logger.error(f"Environment image generation failed: {e}")
            return None
            
    async def generate_encounter_lore(self, env_image_prompt: str) -> Optional[str]:
        """Generate encounter lore using AI"""
        try:
            return await self.text_generator.generate_with_template(
                template=self.prompt_loader.get_encounter_lore_random_prompt(),
                variables={"env_image_prompt": env_image_prompt},
                model="gpt-4o-mini",
                max_tokens=2000,
                temperature=0.7
            )
        except Exception as e:
            self.logger.error(f"Encounter lore generation failed: {e}")
            return None

    async def generate_encounter_lore_with_input(self, env_image_prompt: str, environment: str, enemies: str) -> Optional[str]:
        """Generate encounter lore using AI with user input"""
        try:
            return await self.text_generator.generate_with_template(
                template=self.prompt_loader.get_encounter_lore_prompt(),
                variables={
                    "env_image_prompt": env_image_prompt,
                    "user_environment": environment,
                    "user_enemies": enemies
                },
                model="gpt-4o-mini",
                max_tokens=2000,
                temperature=0.7
            )
        except Exception as e:
            self.logger.error(f"Encounter lore generation with input failed: {e}")
            return None
            
    async def generate_encounter_npcs(self, encounter_lore: str, encounter_folder: str = None, progress_callback=None) -> Optional[Dict[str, Any]]:
        """Generate NPCs for the encounter using AI"""
        try:
            # Load character schema for validation
            character_schema = self.schema_loader.get_character_schema_min()
            
            # Use text generator with template for NPC generation
            npcs_data = await self.text_generator.generate_json_with_template(
                template=self.prompt_loader.get_npc_generation_prompt(),
                variables={
                    "encounter_lore": encounter_lore,
                    "schema": json.dumps(character_schema, indent=2)
                },
                schema=None,  # Don't validate the top-level structure, we'll validate individual NPCs
                model="gpt-4o-mini",
                max_tokens=3000,
                temperature=0.3
            )
            
            # Validate individual NPCs against character schema
            if npcs_data and 'npcs' in npcs_data:
                for i, npc in enumerate(npcs_data['npcs']):
                    if not self.schema_loader.validate_data(npc, character_schema):
                        errors = self.schema_loader.get_validation_errors(npc, character_schema)
                        self.logger.warning(f"NPC {i} validation failed: {errors}")
                        # Continue anyway - the NPC might still be usable
            
            return npcs_data
        except Exception as e:
            self.logger.error(f"NPCs generation failed: {e}")
            return None
    
    async def generate_npc_images(self, npcs_data: Dict[str, Any], encounter_folder: str, progress_callback=None) -> None:
        """Generate images for each NPC in the encounter - optimized for speed"""
        try:
            if not isinstance(npcs_data, dict) or 'npcs' not in npcs_data:
                return
                
            npcs = npcs_data.get('npcs', [])
            if not isinstance(npcs, list):
                return
            
            # Store generated prompts for reference
            generated_prompts = {}
            
            # Create simple image prompts directly from NPC data (no LLM call needed)
            image_tasks = []
            for i, npc in enumerate(npcs):
                if not isinstance(npc, dict):
                    continue
                    
                npc_name = npc.get('name', f'Enemy {i+1}')
                self.logger.info(f"Preparing image generation for NPC {i}: {npc_name}")
                
                # Create a unique and detailed image prompt from NPC data
                class_type = npc.get('class_type', 'Warrior')
                description = npc.get('description', '')
                
                # Ensure description is not empty - NPCs should have descriptions from generation
                if not description or description.strip() == '':
                    self.logger.warning(f"NPC {npc_name} missing description - using fallback")
                    description = f"a {class_type} character"
                
                # Load basic image prompt template
                template = self.prompt_loader.get_basic_image_prompt_template()
                if not template:
                    self.logger.error("Failed to load basic image prompt template")
                    # Fallback to simple template
                    template = "Portrait of a {class_type} character, {description}, detailed fantasy art, dramatic lighting, high quality"
                
                # Build enhanced image prompt using template
                image_prompt = self.prompt_loader.format_prompt(template, class_type=class_type, description=description)
                
                # Log the enhanced prompt for debugging
                self.logger.info(f"Generated unique prompt for {npc_name}: {image_prompt[:100]}...")
                
                # Store the generated prompt
                generated_prompts[f"npc_{i}"] = {
                    "npc_name": npc_name,
                    "prompt": image_prompt
                }
                
                # Create task for concurrent image generation
                task = self._generate_single_npc_image(
                    i, npc_name, image_prompt, npc, encounter_folder, progress_callback, len(npcs)
                )
                image_tasks.append(task)
            
            # Generate all images concurrently
            if image_tasks:
                self.logger.info(f"Starting concurrent generation of {len(image_tasks)} NPC images")
                await asyncio.gather(*image_tasks, return_exceptions=True)
            
            # Save generated prompts for reference
            prompts_file_path = os.path.join(encounter_folder, "npc_image_prompts.json")
            try:
                with open(prompts_file_path, 'w') as f:
                    json.dump(generated_prompts, f, indent=2)
                self.logger.info(f"Saved NPC image prompts to: {prompts_file_path}")
            except Exception as e:
                self.logger.error(f"Failed to save NPC image prompts: {e}")
                
        except Exception as e:
            self.logger.error(f"NPC image generation failed: {e}")
    
    async def _generate_single_npc_image(self, index: int, npc_name: str, image_prompt: str, 
                                       npc: Dict[str, Any], folder_path: str, progress_callback=None, total_npcs: int = 0) -> None:
        """Generate a single NPC image - designed for concurrent execution"""
        try:
            # Update progress
            if progress_callback:
                progress_callback(4, f"Generating NPC image {index+1}/{total_npcs}...")
            
            # Generate image using the image generator
            self.logger.debug(f"Image generation request size: {len(image_prompt)} characters")
            image_data = await self.image_generator.generate_image(
                prompt=image_prompt,
                size="1024x1024",
                quality="standard",
                style="vivid"
            )
            
            if image_data:
                # Save NPC image IMMEDIATELY after generation
                try:
                    import base64
                    image_bytes = base64.b64decode(image_data)
                    image_file_path = os.path.join(folder_path, f"npc_{index}.webp")
                    with open(image_file_path, 'wb') as f:
                        f.write(image_bytes)
                    self.logger.info(f"NPC image saved immediately: {image_file_path}")
                except Exception as e:
                    self.logger.error(f"Failed to save NPC image {npc_name}: {e}")
            else:
                self.logger.warning(f"Failed to generate image for NPC {npc_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to generate image for NPC {npc_name}: {e}")

    def extract_encounter_name(self, lore_text: str, environment: str) -> str:
        """Extract encounter name from lore text (like character generation does)"""
        try:
            # Clean up the lore text first
            cleaned_lore = lore_text.strip()
            if cleaned_lore.startswith('```json'):
                cleaned_lore = cleaned_lore[7:]
            if cleaned_lore.startswith('```'):
                cleaned_lore = cleaned_lore[3:]
            if cleaned_lore.endswith('```'):
                cleaned_lore = cleaned_lore[:-3]
            cleaned_lore = cleaned_lore.strip()
            
            # Try to parse as JSON first
            try:
                lore_data = json.loads(cleaned_lore)
                if isinstance(lore_data, dict) and 'name' in lore_data:
                    encounter_name = lore_data['name']
                    # Return clean name without prefix
                    self.logger.info(f"Extracted encounter name from JSON: {encounter_name}")
                    return encounter_name
            except (json.JSONDecodeError, TypeError):
                pass
            
            # Try regex extraction as fallback
            import re
            name_match = re.search(r'"name"\s*:\s*"([^"]+)"', cleaned_lore, re.DOTALL)
            if name_match:
                encounter_name = name_match.group(1)
                # Return clean name without prefix
                self.logger.info(f"Extracted encounter name using regex: {encounter_name}")
                return encounter_name
            
            # Final fallback: create name from environment
            if environment == "Random Environment":
                encounter_name = "Random Encounter"
            else:
                safe_env = "".join(c for c in environment if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_env = safe_env.replace(' ', '_')
                encounter_name = f"Custom_{safe_env}"
            self.logger.info(f"Using fallback encounter name: {encounter_name}")
            return encounter_name
            
        except Exception as e:
            self.logger.error(f"Failed to extract encounter name: {e}")
            if environment == "Random Environment":
                return "Random Encounter"  # Final fallback for random
            else:
                return "Custom Encounter"  # Final fallback for custom

# Compatibility aliases for server
AIEncounterGenerator = EncounterGeneratorV2

# Compatibility function for server
async def generate_encounter_with_ai(environment: str = None, enemies: str = None, progress_callback=None, session_id: str = None) -> Optional[str]:
    """Compatibility function for server - generates encounter using v2 system"""
    generator = EncounterGeneratorV2()
    
    if environment and enemies:
        # Custom encounter
        return await generator.generate_encounter(
            environment=environment,
            enemies=enemies,
            progress_callback=progress_callback,
            session_id=session_id
        )
    else:
        # Random encounter
        return await generator.generate_random_encounter(progress_callback, session_id)

if __name__ == "__main__":
    print("Encounter Generator V2 - Ready for integration")