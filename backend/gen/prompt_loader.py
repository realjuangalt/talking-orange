"""
Prompt Loader
Utility module for loading and managing prompt templates from the prompts/ directory.
Provides centralized access to prompt templates and eliminates hardcoded prompts.
"""

import os
from typing import Dict, Optional
from pathlib import Path

class PromptLoader:
    """Loads and manages prompt templates from the prompts directory."""
    
    def __init__(self, prompts_dir: str = None, user_id: str = None, project_name: str = None):
        """
        Initialize the prompt loader.
        
        Args:
            prompts_dir: Path to the prompts directory (if None, will use project-specific or default)
            user_id: User identifier for project-specific prompts
            project_name: Project name for project-specific prompts
        """
        if prompts_dir is None:
            # Try to use project-specific prompts if user_id and project_name provided
            if user_id and project_name:
                try:
                    # Import here to avoid circular dependencies
                    import sys
                    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if backend_dir not in sys.path:
                        sys.path.insert(0, backend_dir)
                    from user_manager import get_project_prompts_path
                    prompts_dir = get_project_prompts_path(user_id, project_name)
                    # If project prompts don't exist, fall back to default
                    if not os.path.exists(prompts_dir):
                        prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
                except Exception as e:
                    # Fallback to default if project prompts unavailable
                    prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
            else:
                # Default to gen/prompts directory
                prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
        
        self.prompts_dir = Path(prompts_dir)
        self._cache = {}
        self.user_id = user_id
        self.project_name = project_name
        
        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_dir}")
    
    def load_prompt(self, filename: str) -> str:
        """
        Load a prompt template from file.
        
        Args:
            filename: Name of the prompt file
            
        Returns:
            Prompt template content
            
        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        # Check cache first
        if filename in self._cache:
            return self._cache[filename]
        
        prompt_path = self.prompts_dir / filename
        
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                self._cache[filename] = content
                return content
        except Exception as e:
            raise Exception(f"Error loading prompt {filename}: {str(e)}")
    
    def get_character_generation_prompt(self) -> str:
        """Get character generation meta prompt."""
        return self.load_prompt("character_generation_meta.txt")
    
    def get_encounter_generation_prompt(self) -> str:
        """Get encounter generation prompt."""
        return self.load_prompt("tactical_positioning_meta.txt")
    
    def get_encounter_lore_prompt(self) -> str:
        """Get encounter lore generation prompt."""
        return self.load_prompt("encounter_lore_meta.txt")
    
    def get_encounter_lore_random_prompt(self) -> str:
        """Get random encounter lore generation prompt."""
        return self.load_prompt("encounter_lore_random_meta.txt")
    
    def get_lore_generation_prompt(self) -> str:
        """Get general lore generation prompt."""
        return self.load_prompt("lore_generation_meta.txt")
    
    def get_npc_generation_prompt(self) -> str:
        """Get NPC generation prompt."""
        return self.load_prompt("npc_generation_meta.txt")
    
    def get_profile_picture_prompt(self) -> str:
        """Get profile picture generation prompt."""
        return self.load_prompt("profile_picture_prompt_meta.txt")
    
    def get_npc_image_prompt(self) -> str:
        """Get NPC image generation prompt."""
        return self.load_prompt("npc_image_prompt_meta.txt")
    
    def get_encounter_environment_prompt(self) -> str:
        """Get encounter environment prompt."""
        return self.load_prompt("encounter_environment_prompt.txt")
    
    def get_environment_image_prompt(self) -> str:
        """Get environment image generation prompt."""
        return self.load_prompt("encounter_environment_prompt.txt")
    
    def get_basic_image_prompt_template(self) -> str:
        """Get basic image prompt template."""
        return self.load_prompt("basic_image_prompt_template.txt")
    
    def get_random_environment_prompt(self) -> str:
        """Get random environment description prompt."""
        return self.load_prompt("random_environment_description.txt")
    
    def get_random_env_meta_prompt(self) -> str:
        """Get random environment meta prompt."""
        return self.load_prompt("random-env-meta-prompt.txt")
    
    def get_tactical_positioning_prompt(self) -> str:
        """Get tactical positioning prompt."""
        return self.load_prompt("tactical_positioning_meta.txt")
    
    def get_schema_update_prompt(self) -> str:
        """Get schema update prompt."""
        return self.load_prompt("schema_update_prompt.txt")
    
    def format_prompt(self, template: str, **kwargs) -> str:
        """
        Format a prompt template with variables.
        
        Args:
            template: Prompt template string
            **kwargs: Variables to substitute
            
        Returns:
            Formatted prompt
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable in prompt: {e}")
        except Exception as e:
            raise Exception(f"Error formatting prompt: {str(e)}")
    
    def clear_cache(self):
        """Clear the prompt cache."""
        self._cache.clear()
    
    def list_available_prompts(self) -> list:
        """
        List all available prompt files.
        
        Returns:
            List of prompt filenames
        """
        return [f.name for f in self.prompts_dir.glob("*.txt")]

# Global instance for easy access - lazy loaded
_prompt_loader = None

def get_prompt_loader(user_id: str = None, project_name: str = None):
    """
    Get a prompt loader instance, optionally project-specific.
    
    Args:
        user_id: User identifier for project-specific prompts
        project_name: Project name for project-specific prompts
        
    Returns:
        PromptLoader instance
    """
    global _prompt_loader
    # If project-specific, create new instance (don't cache globally)
    if user_id and project_name:
        return PromptLoader(user_id=user_id, project_name=project_name)
    # Otherwise use cached global instance
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader

# Default global instance (for backward compatibility)
prompt_loader = get_prompt_loader()

# Convenience functions
def load_prompt(filename: str) -> str:
    """Load a prompt template by filename."""
    return prompt_loader.load_prompt(filename)

def get_character_generation_prompt() -> str:
    """Get character generation meta prompt."""
    return prompt_loader.get_character_generation_prompt()

def get_encounter_generation_prompt() -> str:
    """Get encounter generation prompt."""
    return prompt_loader.get_encounter_generation_prompt()

def get_encounter_lore_prompt() -> str:
    """Get encounter lore generation prompt."""
    return prompt_loader.get_encounter_lore_prompt()

def get_encounter_lore_random_prompt() -> str:
    """Get random encounter lore generation prompt."""
    return prompt_loader.get_encounter_lore_random_prompt()

def get_lore_generation_prompt() -> str:
    """Get general lore generation prompt."""
    return prompt_loader.get_lore_generation_prompt()

def get_npc_generation_prompt() -> str:
    """Get NPC generation prompt."""
    return prompt_loader.get_npc_generation_prompt()

def get_profile_picture_prompt() -> str:
    """Get profile picture generation prompt."""
    return prompt_loader.get_profile_picture_prompt()

def get_npc_image_prompt() -> str:
    """Get NPC image generation prompt."""
    return prompt_loader.get_npc_image_prompt()

def get_encounter_environment_prompt() -> str:
    """Get encounter environment prompt."""
    return prompt_loader.get_encounter_environment_prompt()

def get_environment_image_prompt() -> str:
    """Get environment image generation prompt."""
    return prompt_loader.get_environment_image_prompt()

def get_basic_image_prompt_template() -> str:
    """Get basic image prompt template."""
    return prompt_loader.get_basic_image_prompt_template()

def get_random_environment_prompt() -> str:
    """Get random environment description prompt."""
    return prompt_loader.get_random_environment_prompt()

def get_random_env_meta_prompt() -> str:
    """Get random environment meta prompt."""
    return prompt_loader.get_random_env_meta_prompt()

def get_tactical_positioning_prompt() -> str:
    """Get tactical positioning prompt."""
    return prompt_loader.get_tactical_positioning_prompt()

def get_schema_update_prompt() -> str:
    """Get schema update prompt."""
    return prompt_loader.get_schema_update_prompt()

def format_prompt(template: str, **kwargs) -> str:
    """Format a prompt template with variables."""
    return prompt_loader.format_prompt(template, **kwargs)
