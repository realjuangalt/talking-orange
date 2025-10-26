"""
Image Generator
Generic text-to-image AI generation module.
Provides basic image generation capabilities that can be used by specific generators.
"""

import asyncio
import aiohttp
import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)
try:
    from .api_client import VeniceAPIClient, generate_image_async
except ImportError:
    try:
        from api_client import VeniceAPIClient, generate_image_async
    except ImportError:
        # Fallback for when running from server context
        import sys
        import os
        gen_dir = os.path.join(os.path.dirname(__file__))
        if gen_dir not in sys.path:
            sys.path.insert(0, gen_dir)
        from api_client import VeniceAPIClient, generate_image_async

class ImageGenerator:
    """Generic image generation module for all text-to-image AI processes."""
    
    def __init__(self):
        """Initialize the image generator."""
        self.api_client = VeniceAPIClient()
    
    async def _generate_image_internal(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid"
    ) -> str:
        """Internal image generation method."""
        try:
            # Parse size
            width, height = map(int, size.split('x'))
            
            # Use API client as async context manager
            async with VeniceAPIClient() as api_client:
                result = await api_client.make_api_call(
                    endpoint="image",
                    data={
                        "prompt": prompt,
                        "width": width,
                        "height": height,
                        "quality": quality,
                        "style": style
                    }
                )
            
            if result:
                # Result is now the base64 string directly from the API client
                return result
            else:
                raise Exception(f"Invalid API response: {result}")
                
        except Exception as e:
            logger.error(f"Image generation error: {str(e)}")
            raise
    
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
        return await self._generate_image_internal(prompt, size, quality, style)
    
    async def generate_images_batch(
        self,
        prompts: List[str],
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid"
    ) -> List[str]:
        """
        Generate multiple images from a list of prompts.
        
        Args:
            prompts: List of image prompts
            size: Image size
            quality: Image quality
            style: Image style
            
        Returns:
            List of image URLs or base64 data
        """
        images = []
        for prompt in prompts:
            image_url = await self.generate_image(prompt, size, quality, style)
            images.append(image_url)
        
        return images

    async def _generate_images_batch_internal(
        self,
        prompts: List[str],
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid"
    ) -> List[str]:
        """Internal method to generate multiple images from a list of prompts."""
        tasks = []
        for prompt in prompts:
            task = self._generate_image_internal(prompt, size, quality, style)
            tasks.append(task)
        
        return await asyncio.gather(*tasks)

    async def _generate_and_save_image_internal(
        self,
        prompt: str,
        save_path: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid"
    ) -> bool:
        """Internal method to generate and save an image from a text prompt."""
        try:
            # Generate image
            image_url = await self._generate_image_internal(prompt, size, quality, style)
            
            # Download and save
            return await self.download_image(image_url, save_path)
            
        except Exception as e:
            logger.error(f"Generate and save image error: {str(e)}")
            return False
    
    async def download_image(
        self,
        image_url: str,
        save_path: str
    ) -> bool:
        """
        Download image from URL to local file.
        
        Args:
            image_url: URL of the image
            save_path: Local path to save the image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        with open(save_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        return True
                    else:
                        return False
        except Exception as e:
            print(f"Error downloading image: {str(e)}")
            return False
    
    async def generate_and_save_image(
        self,
        prompt: str,
        save_path: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid"
    ) -> bool:
        """
        Generate and save image from prompt.
        
        Args:
            prompt: Image prompt
            save_path: Local path to save the image
            size: Image size
            quality: Image quality
            style: Image style
            
        Returns:
            True if successful, False otherwise
        """
        try:
            image_url = await self.generate_image(prompt, size, quality, style)
            return await self.download_image(image_url, save_path)
        except Exception as e:
            print(f"Error generating and saving image: {str(e)}")
            return False

# Global instance for easy access
image_generator = ImageGenerator()

# Convenience functions
async def generate_image_async(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid"
) -> str:
    """Generate image using Venice AI."""
    return await image_generator._generate_image_internal(prompt, size, quality, style)

async def generate_images_batch_async(
    prompts: List[str],
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid"
) -> List[str]:
    """Generate multiple images from a list of prompts."""
    return await image_generator._generate_images_batch_internal(prompts, size, quality, style)

async def download_image_async(
    image_url: str,
    save_path: str
) -> bool:
    """Download image from URL to local file."""
    return await image_generator.download_image(image_url, save_path)

async def generate_and_save_image_async(
    prompt: str,
    save_path: str,
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid"
) -> bool:
    """Generate and save image from prompt."""
    return await image_generator._generate_and_save_image_internal(
        prompt, save_path, size, quality, style
    )

# Synchronous wrappers for backward compatibility
def generate_image(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid"
) -> str:
    """Synchronous wrapper for image generation."""
    return asyncio.run(generate_image_async(prompt, size, quality, style))

def generate_images_batch(
    prompts: List[str],
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid"
) -> List[str]:
    """Synchronous wrapper for batch image generation."""
    return asyncio.run(generate_images_batch_async(prompts, size, quality, style))

def download_image(
    image_url: str,
    save_path: str
) -> bool:
    """Synchronous wrapper for image download."""
    return asyncio.run(download_image_async(image_url, save_path))

def generate_and_save_image(
    prompt: str,
    save_path: str,
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid"
) -> bool:
    """Synchronous wrapper for generate and save image."""
    return asyncio.run(generate_and_save_image_async(
        prompt, save_path, size, quality, style
    ))
