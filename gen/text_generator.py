"""
Text Generator
Generic text-to-text AI generation module using the AI Content Generation Factory.
Handles all text generation tasks including JSON generation and template-based generation.
"""

import json
import logging
from typing import Dict, Any, Optional, List

# Import our modular building blocks
try:
    from .api_client import VeniceAPIClient
    from .prompt_loader import PromptLoader
    from .schema_loader import SchemaLoader
except ImportError:
    try:
        from api_client import VeniceAPIClient
        from prompt_loader import PromptLoader
        from schema_loader import SchemaLoader
    except ImportError:
        # Fallback for when running from server context
        import sys
        import os
        gen_dir = os.path.join(os.path.dirname(__file__))
        if gen_dir not in sys.path:
            sys.path.insert(0, gen_dir)
        from api_client import VeniceAPIClient
        from prompt_loader import PromptLoader
        from schema_loader import SchemaLoader

logger = logging.getLogger(__name__)

class TextGenerator:
    """
    Generic text-to-text AI generation module.
    Handles all text generation tasks using the Venice AI API.
    """
    
    def __init__(self):
        self.prompt_loader = PromptLoader()
        self.schema_loader = SchemaLoader()
    
    async def generate_text(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Generate text using the AI model.
        
        Args:
            prompt: The text prompt
            model: AI model to use
            max_tokens: Maximum tokens to generate
            temperature: Creativity level (0.0 to 1.0)
            
        Returns:
            Generated text or None if failed
        """
        try:
            return await self._generate_text_internal(
                prompt, model, max_tokens, temperature
            )
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            return None
    
    async def generate_json(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        model: str = "gpt-4o-mini",
        max_tokens: int = 2000,
        temperature: float = 0.3
    ) -> Optional[Dict[str, Any]]:
        """
        Generate JSON using the AI model.
        
        Args:
            prompt: The text prompt
            schema: Optional JSON schema for validation
            model: AI model to use
            max_tokens: Maximum tokens to generate
            temperature: Creativity level (0.0 to 1.0)
            
        Returns:
            Generated JSON data or None if failed
        """
        try:
            result = await self._generate_json_internal(
                prompt, model, max_tokens, temperature
            )
            
            if result and schema:
                # Validate against schema
                if not self.schema_loader.validate_data(result, schema):
                    errors = self.schema_loader.get_validation_errors(result, schema)
                    logger.error(f"Generated JSON is invalid: {errors}")
                    return None
            
            return result
        except Exception as e:
            logger.error(f"Error generating JSON: {str(e)}")
            return None
    
    async def generate_with_template(
        self,
        template: str,
        variables: Dict[str, str],
        model: str = "gpt-4o-mini",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Generate text using a template with variables.
        
        Args:
            template: Template string with {variable} placeholders
            variables: Dictionary of variables to substitute
            model: AI model to use
            max_tokens: Maximum tokens to generate
            temperature: Creativity level (0.0 to 1.0)
            
        Returns:
            Generated text or None if failed
        """
        try:
            # Format the template with variables
            prompt = self.prompt_loader.format_prompt(template, **variables)
            
            return await self._generate_text_internal(
                prompt, model, max_tokens, temperature
            )
        except Exception as e:
            logger.error(f"Error generating text with template: {str(e)}")
            return None
    
    async def generate_json_with_template(
        self,
        template: str,
        variables: Dict[str, str],
        schema: Optional[Dict[str, Any]] = None,
        model: str = "gpt-4o-mini",
        max_tokens: int = 2000,
        temperature: float = 0.3
    ) -> Optional[Dict[str, Any]]:
        """
        Generate JSON using a template with variables.
        
        Args:
            template: Template string with {variable} placeholders
            variables: Dictionary of variables to substitute
            schema: Optional JSON schema for validation
            model: AI model to use
            max_tokens: Maximum tokens to generate
            temperature: Creativity level (0.0 to 1.0)
            
        Returns:
            Generated JSON data or None if failed
        """
        try:
            # Format the template with variables
            prompt = self.prompt_loader.format_prompt(template, **variables)
            
            result = await self._generate_json_internal(
                prompt, model, max_tokens, temperature
            )
            
            if result and schema:
                # Validate against schema
                if not self.schema_loader.validate_data(result, schema):
                    errors = self.schema_loader.get_validation_errors(result, schema)
                    logger.error(f"Generated JSON is invalid: {errors}")
                    return None
            
            return result
        except Exception as e:
            logger.error(f"Error generating JSON with template: {str(e)}")
            return None
    
    async def _generate_text_internal(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float
    ) -> Optional[str]:
        """Internal method to generate text directly with API client."""
        try:
            async with VeniceAPIClient() as api_client:
                data = {
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
                result = await api_client.make_api_call(
                    endpoint="text",
                    data=data,
                    model=model
                )
                
                # Extract text content from API response
                if result and isinstance(result, dict):
                    choices = result.get("choices", [])
                    if choices and len(choices) > 0:
                        return choices[0].get("message", {}).get("content", "")
                
                return None
        except Exception as e:
            logger.error(f"Error in text generation: {str(e)}")
            return None
    
    async def _generate_json_internal(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float
    ) -> Optional[Dict[str, Any]]:
        """Internal method to generate JSON directly with API client."""
        try:
            async with VeniceAPIClient() as api_client:
                data = {
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
                result = await api_client.make_api_call(
                    endpoint="text",
                    data=data,
                    model=model
                )
                
                # Extract text content from API response
                if result and isinstance(result, dict):
                    choices = result.get("choices", [])
                    if choices and len(choices) > 0:
                        content = choices[0].get("message", {}).get("content", "")
                        if content:
                            # Clean up markdown formatting if present
                            content = content.strip()
                            if content.startswith("```json"):
                                content = content[7:]  # Remove ```json
                            if content.startswith("```"):
                                content = content[3:]   # Remove ```
                            if content.endswith("```"):
                                content = content[:-3]  # Remove trailing ```
                            content = content.strip()
                            
                            # Try to parse as JSON
                            try:
                                return json.loads(content)
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to parse JSON response: {str(e)}")
                                logger.error(f"Content was: {repr(content)}")
                                return None
                
                return None
        except Exception as e:
            logger.error(f"Error in JSON generation: {str(e)}")
            return None

# Convenience functions for easy usage
async def generate_text(
    prompt: str,
    model: str = "gpt-4o-mini",
    max_tokens: int = 1000,
    temperature: float = 0.7
) -> Optional[str]:
    """Generate text using the AI model."""
    generator = TextGenerator()
    return await generator.generate_text(prompt, model, max_tokens, temperature)

async def generate_json(
    prompt: str,
    schema: Optional[Dict[str, Any]] = None,
    model: str = "gpt-4o-mini",
    max_tokens: int = 2000,
    temperature: float = 0.3
) -> Optional[Dict[str, Any]]:
    """Generate JSON using the AI model."""
    generator = TextGenerator()
    return await generator.generate_json(prompt, schema, model, max_tokens, temperature)

async def generate_with_template(
    template: str,
    variables: Dict[str, str],
    model: str = "gpt-4o-mini",
    max_tokens: int = 1000,
    temperature: float = 0.7
) -> Optional[str]:
    """Generate text using a template with variables."""
    generator = TextGenerator()
    return await generator.generate_with_template(template, variables, model, max_tokens, temperature)

async def generate_json_with_template(
    template: str,
    variables: Dict[str, str],
    schema: Optional[Dict[str, Any]] = None,
    model: str = "gpt-4o-mini",
    max_tokens: int = 2000,
    temperature: float = 0.3
) -> Optional[Dict[str, Any]]:
    """Generate JSON using a template with variables."""
    generator = TextGenerator()
    return await generator.generate_json_with_template(template, variables, schema, model, max_tokens, temperature)
