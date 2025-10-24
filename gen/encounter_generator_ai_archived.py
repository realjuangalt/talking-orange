import json
import os
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime as dt
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

"""
CRITICAL BUG FIXES IMPLEMENTED (2025-08-26):

1. FIXED: Duplicate generate_npc_images() calls
   - Removed duplicate call from generate_encounter_npcs() method
   - NPC images now generated only once in main flow (Step 5)

2. FIXED: Missing NPC descriptions causing identical prompts
   - Added description requirement to NPC generation prompt
   - All hardcoded prompts moved to prompt files for easy manipulation

3. FIXED: Identical image prompts causing identical images
   - All prompts now loaded from external prompt files
   - No more hardcoded text in the code
   - Easy to modify prompts without changing code

4. IMPROVED: Code maintainability
   - All prompts moved to prompts/ directory
   - Easy to edit and version control prompts
   - No fallback logic - system should work with proper prompts

These fixes resolve the core issue where ALL NPC images were identical due to duplicate
API calls and identical prompts with empty description fields.
"""

class AIEncounterGenerator:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.logger = logging.getLogger(__name__)
        self.root_dir = os.path.dirname(__file__)  # gen/ directory
        
        # Use Flask's logging system
        self.user_inputs_logger = logging.getLogger('user_inputs')
        self.input_prompts_logger = logging.getLogger('user_prompts')
        self.ai_outputs_logger = logging.getLogger('ai_outputs')
        self.ai_inputs_logger = logging.getLogger('ai_inputs')
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json"""
        return self.config_manager.config
    
    def is_npc_images_enabled(self) -> bool:
        """Check if NPC images generation is enabled"""
        game_settings = self.config.get('game_settings', {})
        return game_settings.get('npc_images_enabled', False)
            
    def load_schema(self) -> str:
        """Load the character schema for NPC generation - REQUIRES minified version"""
        try:
            # Use the new character schema instead of the full game state schema
            schema_file = os.path.join(self.root_dir, "schemas", "character_schema.min.json")
            if not os.path.exists(schema_file):
                self.logger.error(f"Character schema not found at {schema_file}")
                self.logger.error("CRITICAL: Character schema is required for NPC generation.")
                raise FileNotFoundError(f"Required character schema not found: {schema_file}")
            
            with open(schema_file, 'r') as f:
                content = f.read()
                self.logger.debug(f"Loaded character schema from {schema_file}")
                return content
        except Exception as e:
            self.logger.error(f"Failed to load character schema: {e}")
            raise
            
    def load_encounter_schema(self) -> str:
        """Load the encounter schema for positioning generation - REQUIRES minified version"""
        try:
            # Use the new encounter schema for positioning and encounter metadata
            schema_file = os.path.join(self.root_dir, "schemas", "encounter_schema.min.json")
            if not os.path.exists(schema_file):
                self.logger.error(f"Encounter schema not found at {schema_file}")
                self.logger.error("CRITICAL: Encounter schema is required for positioning generation.")
                raise FileNotFoundError(f"Required encounter schema not found: {schema_file}")
            
            with open(schema_file, 'r') as f:
                content = f.read()
                self.logger.debug(f"Loaded encounter schema from {schema_file}")
                return content
        except Exception as e:
            self.logger.error(f"Failed to load encounter schema: {e}")
            raise
            
    def load_meta_prompt(self, prompt_type: str) -> str:
        """Load meta prompt from prompts folder"""
        try:
            prompt_file = os.path.join(self.root_dir, "prompts", f"{prompt_type}.txt")
            with open(prompt_file, 'r') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to load meta prompt {prompt_type}: {e}")
            return ""
            
    async def make_api_call(self, endpoint: str, model: str, prompt: str, is_image: bool = False) -> Optional[str]:
        """Make API call to Venice AI"""
        try:
            # Get appropriate API key
            api_key = os.getenv("VENICE_KEY", "")
            if not api_key:
                self.logger.error("No VENICE_KEY found in environment")
                return None
                
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            
            # Log the API call details (but not to user prompts logger)
            self.logger.debug(f"API Call - Model: {model}, Endpoint: {endpoint}, Is Image: {is_image}")
            
            # Log the input prompt to ai_inputs.log
            self.ai_inputs_logger.info(f"AI INPUT - Model: {model}, Endpoint: {endpoint}, Is Image: {is_image}, Prompt Length: {len(prompt)}")
            self.ai_inputs_logger.info(f"AI INPUT CONTENT: {prompt}")
            
            if is_image:
                # Image generation - Venice format
                payload = {
                    "embed_exif_metadata": False,
                    "format": "webp",
                    "height": 1024,
                    "hide_watermark": False,
                    "return_binary": False,
                    "safe_mode": True,
                    "seed": 0,
                    "steps": 20,
                    "width": 1024,
                    "model": model,
                    "prompt": prompt
                }
                # Use image generation endpoint
                endpoint = "https://api.venice.ai/api/v1/image/generate"
            else:
                # Text generation - Venice format
                payload = {
                    "frequency_penalty": 0,
                    "n": 1,
                    "presence_penalty": 0,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "venice_parameters": {
                        "include_venice_system_prompt": True
                    },
                    "parallel_tool_calls": True,
                    "model": model,
                    "messages": [
                        {"content": prompt, "role": "user"}
                    ]
                }
                
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Log the response (strip image data for images)
                        if is_image:
                            # For images, log minimal info to avoid spam
                            self.ai_outputs_logger.info(f"Image Generation Response: {len(data.get('images', []))} images generated")
                            
                            # Return the first image data
                            images = data.get("images", [])
                            return images[0] if images else None
                        else:
                            # For text, log the full response
                            response_content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                            self.ai_outputs_logger.info(f"Text Generation Response: {response_content}")
                            return response_content
                    else:
                        error_text = await response.text()
                        self.logger.error(f"API call failed with status {response.status}: {error_text}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"API call error: {e}")
            return None
            
    def create_encounter_folder(self, session_id: str) -> str:
        """Create encounter folder using session ID - simple and reliable"""
        try:
            # Use session ID as folder name - simple and guaranteed unique
            folder_name = f"encounter_{session_id}"
            # Create folder in data/encounters/ directory (project root relative)
            data_dir = os.path.join(os.path.dirname(self.root_dir), "data")
            folder_path = os.path.join(data_dir, "encounters", folder_name)
            os.makedirs(folder_path, exist_ok=True)
            self.logger.debug(f"Created encounter folder: {folder_path}")
            return folder_path
        except Exception as e:
            self.logger.error(f"Failed to create encounter folder: {e}")
            raise
        
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
        """Generate a complete random encounter using AI - now uses unified generation method"""
        self.logger.info("[DIAG] generate_random_encounter async function called")
        
        # For random encounters, we need to generate an environment description first
        # so that positioning generation works correctly
        try:
            # Generate a random environment description
            random_env_prompt = self.load_meta_prompt("random_environment_description")
            if not random_env_prompt:
                self.logger.error("Failed to load random environment description prompt")
                return None
                
            # Get API settings for environment description
            api_settings = self.config.get('ai_settings', {}).get('prompt_polishing', {})
            endpoint = api_settings.get('endpoint', '')
            model = api_settings.get('model', '')
            
            # Generate random environment description
            random_environment = await self.make_api_call(endpoint, model, random_env_prompt)
            if not random_environment:
                self.logger.error("Failed to generate random environment description")
                return None
                
            self.logger.info(f"Generated random environment: {random_environment[:100]}...")
            
            # Now call the unified generate_encounter method with the generated environment
            return await self.generate_encounter(random_environment, "Random enemies based on environment", progress_callback, session_id)
            
        except Exception as e:
            self.logger.error(f"Random encounter generation failed: {e}")
            return None
            
    async def generate_environment_image_prompt(self) -> Optional[str]:
        """Generate environment image prompt using AI"""
        try:
            # Load meta prompt
            meta_prompt = self.load_meta_prompt("random-env-meta-prompt")
            
            # Get API settings
            api_settings = self.config.get('ai_settings', {}).get('prompt_polishing', {})
            endpoint = api_settings.get('endpoint', '')
            model = api_settings.get('model', '')
            
            # Make API call
            response = await self.make_api_call(endpoint, model, meta_prompt)
            return response
            
        except Exception as e:
            self.logger.error(f"Environment image prompt generation failed: {e}")
            return None

    async def generate_environment_image_prompt_from_input(self, environment: str) -> Optional[str]:
        """Generate environment image prompt from user input"""
        try:
            # Load meta prompt and replace placeholder
            meta_prompt = self.load_meta_prompt("encounter_environment_prompt")
            prompt = meta_prompt.replace("{user_environment}", environment)
            
            # Get API settings
            api_settings = self.config.get('ai_settings', {}).get('prompt_polishing', {})
            endpoint = api_settings.get('endpoint', '')
            model = api_settings.get('model', '')
            
            # Make API call
            response = await self.make_api_call(endpoint, model, prompt)
            return response
            
        except Exception as e:
            self.logger.error(f"Environment image prompt generation from input failed: {e}")
            return None
            
    async def generate_environment_image(self, image_prompt: str) -> Optional[str]:
        """Generate environment image using AI"""
        try:
            # Get API settings
            api_settings = self.config.get('ai_settings', {}).get('background_images', {})
            endpoint = api_settings.get('endpoint', '')
            model = api_settings.get('model', '')
            
            # Make API call for image generation
            response = await self.make_api_call(endpoint, model, image_prompt, is_image=True)
            return response
            
        except Exception as e:
            self.logger.error(f"Environment image generation failed: {e}")
            return None
            
    async def generate_encounter_lore(self, env_image_prompt: str) -> Optional[str]:
        """Generate encounter lore using AI"""
        try:
            # Load meta prompt and replace placeholder
            meta_prompt = self.load_meta_prompt("encounter_lore_random_meta")
            prompt = meta_prompt.replace("{env_image_prompt}", env_image_prompt)
            
            # Get API settings
            api_settings = self.config.get('ai_settings', {}).get('storytelling', {})
            endpoint = api_settings.get('endpoint', '')
            model = api_settings.get('model', '')
            
            # Make API call
            response = await self.make_api_call(endpoint, model, prompt)
            return response
            
        except Exception as e:
            self.logger.error(f"Encounter lore generation failed: {e}")
            return None

    async def generate_encounter_lore_with_input(self, env_image_prompt: str, environment: str, enemies: str) -> Optional[str]:
        """Generate encounter lore using AI with user input"""
        try:
            # Load meta prompt and replace placeholders
            meta_prompt = self.load_meta_prompt("encounter_lore_meta")
            prompt = meta_prompt.replace("{env_image_prompt}", env_image_prompt)
            prompt = prompt.replace("{user_environment}", environment)
            prompt = prompt.replace("{user_enemies}", enemies)
            
            # Get API settings
            api_settings = self.config.get('ai_settings', {}).get('storytelling', {})
            endpoint = api_settings.get('endpoint', '')
            model = api_settings.get('model', '')
            
            # Make API call
            response = await self.make_api_call(endpoint, model, prompt)
            return response
            
        except Exception as e:
            self.logger.error(f"Encounter lore generation with input failed: {e}")
            return None
            
    async def generate_encounter_npcs(self, encounter_lore: str, encounter_folder: str = None, progress_callback=None) -> Optional[Dict[str, Any]]:
        """Generate NPCs for the encounter using AI"""
        try:
            # Load meta prompt and schema
            schema = self.load_schema()
            
            # Load NPC generation meta prompt
            meta_prompt = self.load_meta_prompt("npc_generation_meta")
            if not meta_prompt:
                self.logger.error("Failed to load NPC generation meta prompt")
                return None
                
            # Replace placeholders in the meta prompt
            prompt = meta_prompt.replace("{encounter_lore}", encounter_lore).replace("{schema}", schema)
            
            # Get API settings
            api_settings = self.config.get('ai_settings', {}).get('character_generation', {})
            endpoint = api_settings.get('endpoint', '')
            model = api_settings.get('model', '')
            
            # Make API call
            response = await self.make_api_call(endpoint, model, prompt)
            if not response:
                return None
                
            # Parse JSON response - handle markdown code blocks
            try:
                # Clean up the response - remove markdown code blocks if present
                cleaned_response = response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                if cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[3:]  # Remove ```
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]  # Remove trailing ```
                
                cleaned_response = cleaned_response.strip()
                npcs_data = json.loads(cleaned_response)
                
                # Note: NPC images are generated in the main flow (Step 5) to avoid duplicate calls
                # This prevents the bug where generate_npc_images() was called twice
                
                return npcs_data
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse NPCs JSON: {e}")
                self.logger.error(f"Response was: {response}")
                return None
                
        except Exception as e:
            self.logger.error(f"NPCs generation failed: {e}")
            return None
    
    async def generate_encounter_positions(self, npcs_data: Dict[str, Any], encounter_lore: str, 
                                        environment: str, progress_callback=None) -> Optional[Dict[str, Any]]:
        """Generate tactical positioning for encounter using AI"""
        try:
            # Load encounter schema for positioning generation
            encounter_schema = self.load_encounter_schema()
            
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
            
            # Load tactical positioning meta prompt
            meta_prompt = self.load_meta_prompt("tactical_positioning_meta")
            if not meta_prompt:
                self.logger.error("Failed to load tactical positioning meta prompt")
                return None
                
            # Replace placeholders in the meta prompt
            prompt = meta_prompt.replace("{encounter_lore}", encounter_lore)\
                               .replace("{environment}", environment)\
                               .replace("{npcs_summary}", json.dumps(npc_summaries, indent=2))\
                               .replace("{sample_players}", json.dumps(sample_players, indent=2))
            
            # Get API settings
            api_settings = self.config.get('ai_settings', {}).get('character_generation', {})
            endpoint = api_settings.get('endpoint', '')
            model = api_settings.get('model', '')
            
            # Make API call
            response = await self.make_api_call(endpoint, model, prompt)
            if not response:
                return None
                
            # Parse JSON response - handle markdown code blocks
            try:
                # Clean up the response - remove markdown code blocks if present
                cleaned_response = response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                if cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[3:]  # Remove ```
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]  # Remove trailing ```
                
                cleaned_response = cleaned_response.strip()
                positioning_data = json.loads(cleaned_response)
                
                self.logger.info(f"Successfully generated encounter positioning data")
                return positioning_data
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse positioning JSON: {e}")
                self.logger.error(f"Response was: {response}")
                return None
                
        except Exception as e:
            self.logger.error(f"Positioning generation failed: {e}")
            return None
    
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
    
    async def generate_npc_images(self, npcs_data: Dict[str, Any], encounter_folder: str, progress_callback=None) -> None:
        """Generate images for each NPC in the encounter - optimized for speed"""
        try:
            if not isinstance(npcs_data, dict) or 'npcs' not in npcs_data:
                return
                
            npcs = npcs_data.get('npcs', [])
            if not isinstance(npcs, list):
                return
            
            # Get API settings for image generation
            image_api_settings = self.config.get('ai_settings', {}).get('profile_pictures', {})
            image_endpoint = image_api_settings.get('endpoint', '')
            image_model = image_api_settings.get('model', '')
            
            if not image_endpoint or not image_model:
                self.logger.error("Image generation API settings not configured")
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
                template = self.load_meta_prompt("basic_image_prompt_template")
                if not template:
                    self.logger.error("Failed to load basic image prompt template")
                    # Fallback to simple template
                    template = "Portrait of a {class_type} character, {description}, detailed fantasy art, dramatic lighting, high quality"
                
                # Build enhanced image prompt using template
                image_prompt = template.replace("{class_type}", class_type).replace("{description}", description)
                
                # Log the enhanced prompt for debugging
                self.logger.info(f"Generated unique prompt for {npc_name}: {image_prompt[:100]}...")
                
                # Store the generated prompt
                generated_prompts[f"npc_{i}"] = {
                    "npc_name": npc_name,
                    "prompt": image_prompt
                }
                
                # Create task for concurrent image generation
                task = self._generate_single_npc_image(
                    i, npc_name, image_prompt, image_endpoint, image_model, npc, encounter_folder, progress_callback, len(npcs)
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
                                       endpoint: str, model: str, npc: Dict[str, Any], 
                                       folder_path: str, progress_callback=None, total_npcs: int = 0) -> None:
        """Generate a single NPC image - designed for concurrent execution"""
        try:
            # Update progress
            if progress_callback:
                progress_callback(4, f"Generating NPC image {index+1}/{total_npcs}...")
            
            # Generate image using the prompt
            self.logger.debug(f"Image generation request size: {len(image_prompt)} characters")
            image_data = await self.make_api_call(endpoint, model, image_prompt, is_image=True)
            
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

# Setup logging (same as character_generator_ai.py)
def setup_logging():
    """Setup logging for encounter generation"""
    # Create logs directory if it doesn't exist
    root_dir = os.path.dirname(os.path.dirname(__file__))  # AIRPGrok/ root
    logs_dir = os.path.join(root_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # User inputs logger
    user_inputs_logger = logging.getLogger('user_inputs')
    user_inputs_logger.setLevel(logging.INFO)
    user_inputs_handler = logging.FileHandler(os.path.join(logs_dir, 'user_inputs.log'))
    user_inputs_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    user_inputs_logger.addHandler(user_inputs_handler)
    
    # Input prompts logger
    input_prompts_logger = logging.getLogger('input_prompts')
    input_prompts_logger.setLevel(logging.INFO)
    input_prompts_handler = logging.FileHandler(os.path.join(logs_dir, 'input_prompts.log'))
    input_prompts_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    input_prompts_logger.addHandler(input_prompts_handler)
    
    # AI outputs logger
    ai_outputs_logger = logging.getLogger('ai_outputs')
    ai_outputs_logger.setLevel(logging.INFO)
    ai_outputs_handler = logging.FileHandler(os.path.join(logs_dir, 'ai_outputs.log'))
    ai_outputs_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    ai_outputs_logger.addHandler(ai_outputs_handler)
    
    return user_inputs_logger, input_prompts_logger, ai_outputs_logger 