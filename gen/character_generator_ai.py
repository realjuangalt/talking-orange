# server/character_generator_ai.py
import json
import os
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional
from datetime import datetime
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

# Use Flask's logging system
logger = logging.getLogger(__name__)

class AICharacterGenerator:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.root_dir = os.path.dirname(os.path.dirname(__file__))  # AIRPGrok/ root

    def load_meta_prompt(self, prompt_type: str) -> str:
        """Load meta prompt from prompts/ folder in root"""
        try:
            prompt_file = os.path.join(self.root_dir, 'prompts', f"{prompt_type}_meta.txt")
            with open(prompt_file, 'r') as f:
                content = f.read()
                logger.debug(f"Loaded meta prompt {prompt_type} from {prompt_file}")
                return content
        except Exception as e:
            logger.error(f"Failed to load meta prompt {prompt_type}: {e}")
            return ""

    def load_schema(self) -> str:
        """Load character schema from schemas directory - REQUIRES minified version"""
        try:
            # Use the new character schema instead of the full game state schema
            schema_file = os.path.join(self.root_dir, 'schemas', 'character_schema.min.json')
            if not os.path.exists(schema_file):
                logger.error(f"Character schema not found at {schema_file}")
                logger.error("CRITICAL: Character schema is required for character generation.")
                raise FileNotFoundError(f"Required character schema not found: {schema_file}")
            
            with open(schema_file, 'r') as f:
                content = f.read()
                logger.debug(f"Loaded character schema from {schema_file}")
                return content
        except Exception as e:
            logger.error(f"Failed to load character schema: {e}")
            raise

    async def make_api_call(self, endpoint: str, model: str, prompt: str, is_image: bool = False) -> Optional[str]:
        """Make API call to Venice AI"""
        try:
            api_key = os.getenv("VENICE_KEY", "")
            if not api_key:
                logger.error("No VENICE_KEY found in environment")
                raise ValueError("Missing VENICE_KEY")

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            logger.debug(f"API Call - Model: {model}, Endpoint: {endpoint}, Is Image: {is_image}")
            
            # Log the input prompt to ai_inputs.log
            ai_inputs_logger = logging.getLogger('ai_inputs')
            ai_inputs_logger.info(f"AI INPUT - Model: {model}, Endpoint: {endpoint}, Is Image: {is_image}, Prompt Length: {len(prompt)}")
            ai_inputs_logger.info(f"AI INPUT CONTENT: {prompt}")

            if is_image:
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
                endpoint = "https://api.venice.ai/api/v1/image/generate"
            else:
                payload = {
                    "frequency_penalty": 0,
                    "n": 1,
                    "presence_penalty": 0,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "venice_parameters": {"include_venice_system_prompt": True},
                    "parallel_tool_calls": True,
                    "model": model,
                    "messages": [{"content": prompt, "role": "user"}]
                }

            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, headers=headers, json=payload) as response:
                    logger.debug(f"API response status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        if is_image:
                            images = data.get("images", [])
                            if images:
                                logger.debug(f"Image generation successful, {len(images)} images")
                                return images[0]
                            logger.warning("No images in response")
                            return None
                        else:
                            response_content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                            logger.debug(f"Text response length: {len(response_content)}")
                            return response_content
                    else:
                        error_text = await response.text()
                        logger.error(f"API call failed with status {response.status}: {error_text}")
                        raise Exception(f"API call failed: {error_text}")
        except Exception as e:
            logger.error(f"API call error: {str(e)}", exc_info=True)
            raise

    def create_character_folder(self, character_name: str) -> str:
        """Create character-specific folder in root/characters/"""
        try:
            safe_name = "".join(c for c in character_name if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = f"{safe_name}_{timestamp}"
            folder_path = os.path.join(self.root_dir, "characters", folder_name)
            os.makedirs(folder_path, exist_ok=True)
            logger.debug(f"Created folder: {folder_path}")
            return folder_path
        except Exception as e:
            logger.error(f"Failed to create folder: {e}")
            raise

    async def generate_character(self, character_name: str, character_description: str, progress_callback=None) -> Optional[str]:
        """Generate a complete character using AI"""
        logger.info(f"Starting generation for {character_name}")
        
        # Log user input in character generator
        user_input_logger = logging.getLogger('user_inputs')
        user_input_logger.info(f"CHARACTER GENERATOR - Processing: Name='{character_name}', Description='{character_description}'")
        try:
            # Step 1: Generate character JSON
            if progress_callback:
                progress_callback(1, "Generating character stats and abilities...")
            logger.debug("Step 1: Generating character JSON")
            character_json = await self.generate_character_json(character_name, character_description)
            if not character_json:
                logger.warning("Character JSON generation failed")
                return None

            # Step 2: Generate character lore
            if progress_callback:
                progress_callback(2, "Creating character backstory and lore...")
            logger.debug("Step 2: Generating lore")
            lore_content = await self.generate_character_lore(character_json)
            if not lore_content:
                logger.warning("Lore generation failed")
                return None

            # Step 3: Generate image prompt
            if progress_callback:
                progress_callback(3, "Generating image description...")
            logger.debug("Step 3: Generating image prompt")
            image_prompt = await self.generate_image_prompt(character_json, lore_content)
            if not image_prompt:
                logger.warning("Image prompt generation failed")
                return None

            # Step 4: Generate profile picture
            if progress_callback:
                progress_callback(4, "Creating character portrait...")
            logger.debug("Step 4: Generating profile picture")
            profile_image_url = await self.generate_profile_picture(image_prompt)
            # Continue even if image fails (non-critical)

            # Save files
            folder_path = self.create_character_folder(character_name)
            if not folder_path:
                logger.warning("Folder creation failed")
                return None

            # Save user prompt input
            user_prompt_path = os.path.join(folder_path, "user_prompt.txt")
            user_prompt_content = f"Name: {character_name}\nDescription: {character_description}"
            with open(user_prompt_path, 'w') as f:
                f.write(user_prompt_content)
            logger.info(f"User prompt saved to: {user_prompt_path}")

            # Save character JSON
            char_file_path = os.path.join(folder_path, "character.json")
            with open(char_file_path, 'w') as f:
                json.dump(character_json, f, indent=2)
            logger.info(f"Character JSON saved to: {char_file_path}")

            # Save lore
            lore_file_path = os.path.join(folder_path, "lore.md")
            with open(lore_file_path, 'w') as f:
                f.write(lore_content)
            logger.info(f"Lore saved to: {lore_file_path}")

            # Save image prompt
            prompt_file_path = os.path.join(folder_path, "image_prompt.txt")
            with open(prompt_file_path, 'w') as f:
                f.write(image_prompt)
            logger.info(f"Image prompt saved to: {prompt_file_path}")

            # Save image if generated
            if profile_image_url:
                image_file_path = os.path.join(folder_path, "profile_image.webp")
                try:
                    import base64
                    image_data = base64.b64decode(profile_image_url)
                    with open(image_file_path, 'wb') as f:
                        f.write(image_data)
                    logger.info(f"Profile image saved to: {image_file_path}")
                except Exception as e:
                    logger.error(f"Failed to save profile image: {e}")

            logger.info(f"Character generation completed: {folder_path}")
            return folder_path

        except Exception as e:
            logger.error(f"Character generation failed: {str(e)}", exc_info=True)
            raise

    async def generate_character_json(self, character_name: str, character_description: str) -> Optional[Dict[str, Any]]:
        """Generate character JSON using AI"""
        try:
            meta_prompt = self.load_meta_prompt("character_generation")
            schema = self.load_schema()
            if not meta_prompt or not schema:
                logger.warning("Missing prompt or schema")
                return None

            prompt = meta_prompt.format(
                character_name=character_name,
                character_description=character_description
            ) + f"\n\nJSON SCHEMA:\n{schema}"
            logger.debug(f"Character JSON prompt length: {len(prompt)}")

            api_settings = self.config.get('ai_settings', {}).get('character_generation', {})
            endpoint = api_settings.get('endpoint', '')
            model = api_settings.get('model', '')

            response = await self.make_api_call(endpoint, model, prompt)
            if not response:
                return None

            try:
                cleaned_response = response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[3:]
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]
                character_data = json.loads(cleaned_response.strip())
                logger.debug("Parsed character JSON successfully")
                return character_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse character JSON: {e}, Response: {response}")
                return None

        except Exception as e:
            logger.error(f"Character JSON generation failed: {str(e)}", exc_info=True)
            return None

    async def generate_character_lore(self, character_json: Dict[str, Any]) -> Optional[str]:
        """Generate character lore using AI"""
        try:
            meta_prompt = self.load_meta_prompt("lore_generation")
            if not meta_prompt:
                logger.warning("Empty lore meta prompt")
                return None

            prompt = meta_prompt.format(character_json=json.dumps(character_json, indent=2))
            api_settings = self.config.get('ai_settings', {}).get('lore_sheet', {})
            endpoint = api_settings.get('endpoint', '')
            model = api_settings.get('model', '')

            response = await self.make_api_call(endpoint, model, prompt)
            return response

        except Exception as e:
            logger.error(f"Lore generation failed: {str(e)}", exc_info=True)
            return None

    async def generate_image_prompt(self, character_json: Dict[str, Any], lore_content: str) -> Optional[str]:
        """Generate image prompt using AI"""
        try:
            meta_prompt = self.load_meta_prompt("profile_picture_prompt")
            if not meta_prompt:
                logger.warning("Empty image prompt meta")
                return None

            prompt = meta_prompt.format(
                character_lore=lore_content,
                character_json=json.dumps(character_json, indent=2)
            )
            api_settings = self.config.get('ai_settings', {}).get('image_prompts', {})
            endpoint = api_settings.get('endpoint', '')
            model = api_settings.get('model', '')

            response = await self.make_api_call(endpoint, model, prompt)
            return response

        except Exception as e:
            logger.error(f"Image prompt generation failed: {str(e)}", exc_info=True)
            return None

    async def generate_profile_picture(self, image_prompt: str) -> Optional[str]:
        """Generate profile picture using AI"""
        try:
            api_settings = self.config.get('ai_settings', {}).get('profile_pictures', {})
            endpoint = api_settings.get('endpoint', '')
            model = api_settings.get('model', '')

            response = await self.make_api_call(endpoint, model, image_prompt, is_image=True)
            return response

        except Exception as e:
            logger.error(f"Profile picture generation failed: {str(e)}", exc_info=True)
            return None