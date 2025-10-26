"""
API Client for Venice AI
Centralized module for all API communication with Venice AI service.
Handles authentication, request formatting, error handling, and response processing.
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VeniceAPIClient:
    """Centralized API client for Venice AI service."""
    
    def __init__(self):
        self.api_key = os.getenv('VENICE_KEY')
        self.base_url = "https://api.venice.ai/api/v1"
        self.session = None
        self.config = self._load_config()
        
        if not self.api_key:
            raise ValueError("VENICE_KEY not found in environment variables")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json."""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config.json: {e}")
            return {}
    
    def _get_model_for_endpoint(self, endpoint_type: str, fallback_model: str) -> str:
        """Get model from config for specific endpoint type."""
        try:
            ai_settings = self.config.get("ai_settings", {})
            endpoint_config = ai_settings.get(endpoint_type, {})
            return endpoint_config.get("model", fallback_model)
        except Exception:
            return fallback_model
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def make_api_call(
        self,
        endpoint: str,
        data: Dict[str, Any],
        model: str = "gpt-4o-mini",
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Make an API call to Venice AI.
        
        Args:
            endpoint: API endpoint (e.g., 'text', 'image')
            data: Request data
            model: Model to use
            max_tokens: Maximum tokens for text generation
            temperature: Temperature for generation
            
        Returns:
            API response data
            
        Raises:
            Exception: If API call fails
        """
        if not self.session:
            raise RuntimeError("API client not initialized. Use async context manager.")
        
        if endpoint == "text":
            url = f"{self.base_url}/chat/completions"
        elif endpoint == "image":
            url = f"{self.base_url}/image/generate"
        else:
            url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare request payload based on endpoint type
        if endpoint == "text":
            # Use config model or fallback to provided model
            text_model = self._get_model_for_endpoint("character_generation", model)
            payload = {
                "model": text_model,
                "messages": data.get("messages", []),
                "max_tokens": max_tokens,
                "temperature": temperature,
                "frequency_penalty": 0,
                "n": 1,
                "presence_penalty": 0,
                "top_p": 0.9,
                "venice_parameters": {"include_venice_system_prompt": True},
                "parallel_tool_calls": True
            }
        elif endpoint == "image":
            # Use config model for image generation
            image_model = self._get_model_for_endpoint("profile_pictures", model)
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
                "model": image_model,
                "prompt": data.get("prompt", "")
            }
        else:
            payload = data
        
        try:
            async with self.session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    # For image generation, return the first image from the images array
                    if endpoint == "image" and "images" in result and result["images"]:
                        return result["images"][0]
                    return result
                else:
                    error_text = await response.text()
                    raise Exception(f"API call failed with status {response.status}: {error_text}")
        
        except aiohttp.ClientError as e:
            raise Exception(f"Network error during API call: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse API response: {str(e)}")
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str = "gpt-4o-mini",
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text using Venice AI.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            model: Model to use
            max_tokens: Maximum tokens
            temperature: Temperature for generation
            
        Returns:
            Generated text
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {"messages": messages}
        response = await self.make_api_call("text", data, model, max_tokens, temperature)
        
        return response.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid"
    ) -> str:
        """
        Generate image using Venice AI.
        
        Args:
            prompt: Image prompt
            size: Image size
            quality: Image quality
            style: Image style
            
        Returns:
            Image URL or base64 data
        """
        data = {
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "style": style
        }
        
        response = await self.make_api_call("image", data)
        return response.get("data", [{}])[0].get("url", "")

# Convenience functions for easy usage
async def generate_text_async(
    prompt: str,
    system_prompt: str = "",
    model: str = "gpt-4o-mini",
    max_tokens: int = 4000,
    temperature: float = 0.7
) -> str:
    """Convenience function for text generation."""
    async with VeniceAPIClient() as client:
        return await client.generate_text(prompt, system_prompt, model, max_tokens, temperature)

async def generate_image_async(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid"
) -> str:
    """Convenience function for image generation."""
    async with VeniceAPIClient() as client:
        return await client.generate_image(prompt, size, quality, style)

# Synchronous wrappers for backward compatibility
def generate_text(
    prompt: str,
    system_prompt: str = "",
    model: str = "gpt-4o-mini",
    max_tokens: int = 4000,
    temperature: float = 0.7
) -> str:
    """Synchronous wrapper for text generation."""
    return asyncio.run(generate_text_async(prompt, system_prompt, model, max_tokens, temperature))

def generate_image(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid"
) -> str:
    """Synchronous wrapper for image generation."""
    return asyncio.run(generate_image_async(prompt, size, quality, style))
