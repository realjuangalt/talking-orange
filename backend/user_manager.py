"""
User Management Module
Handles user directory structure and file paths for multi-user, multi-project system.

Directory structure:
- users/{user_id}/
  - {project_name}/
    - media/      (project-specific media files: targets, images, videos)
    - ai/         (AI audio responses for this project)
    - user-input/ (user audio inputs for this project)
"""

import os
import logging
import traceback
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

def get_user_base_path(user_id: str) -> str:
    """
    Get the base path for a user's directory.
    
    Args:
        user_id: Unique user identifier
        
    Returns:
        Absolute path to user's base directory
    """
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    user_base = os.path.join(backend_dir, 'users', user_id)
    return user_base

def get_project_base_path(user_id: str, project_name: str) -> str:
    """
    Get the base path for a user's project directory.
    
    Args:
        user_id: Unique user identifier
        project_name: Project name/identifier
        
    Returns:
        Absolute path to project's base directory
    """
    user_base = get_user_base_path(user_id)
    return os.path.join(user_base, project_name)

def ensure_project_directories(user_id: str, project_name: str) -> dict:
    """
    Ensure all required directories exist for a user's project.
    Creates the directory structure if it doesn't exist.
    
    Directory structure:
    - users/{user_id}/{project_name}/
      - media/      (project-specific media files)
      - ai/         (AI audio responses)
      - user-input/ (user audio inputs)
      - prompts/    (project-specific prompt files)
    
    Args:
        user_id: Unique user identifier
        project_name: Project name/identifier
        
    Returns:
        Dictionary with paths to project directories:
        {
            'base': base path,
            'user_input': path to user input directory,
            'ai': path to AI audio directory,
            'media': path to media directory,
            'prompts': path to prompts directory
        }
    """
    project_base = get_project_base_path(user_id, project_name)
    
    directories = {
        'base': project_base,
        'user_input': os.path.join(project_base, 'user-input'),
        'ai': os.path.join(project_base, 'ai'),
        'media': os.path.join(project_base, 'media'),
        'targets': os.path.join(project_base, 'media', 'targets'),  # Target images and .mind files
        'prompts': os.path.join(project_base, 'prompts')
    }
    
    # Create all directories
    for name, path in directories.items():
        try:
            os.makedirs(path, exist_ok=True)
            # Set permissions (755)
            try:
                os.chmod(path, 0o755)
            except Exception as chmod_error:
                # chmod might fail on some systems, but that's okay
                logger.warning(f"⚠️ Could not set permissions for {path}: {chmod_error}")
            logger.debug(f"✅ Project directory created/verified: {name} = {path}")
        except Exception as e:
            logger.error(f"❌ Failed to create project directory {name} at {path}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    return directories

def ensure_user_directories(user_id: str, project_name: Optional[str] = None) -> dict:
    """
    Legacy function for backward compatibility.
    If project_name is provided, uses project structure.
    Otherwise, creates a default 'default' project.
    
    Args:
        user_id: Unique user identifier
        project_name: Optional project name (defaults to 'default')
        
    Returns:
        Dictionary with paths to directories
    """
    if project_name is None:
        project_name = 'default'
    return ensure_project_directories(user_id, project_name)

def get_user_audio_path(user_id: str, filename: str, audio_type: str = 'user', project_name: Optional[str] = None) -> str:
    """
    Get the full path for a user audio file.
    
    Args:
        user_id: Unique user identifier
        filename: Audio filename
        audio_type: 'user' for user input, 'ai' for AI response
        project_name: Optional project name (defaults to 'default')
        
    Returns:
        Full path to the audio file
    """
    if audio_type not in ['user', 'ai']:
        raise ValueError(f"Invalid audio_type: {audio_type}. Must be 'user' or 'ai'")
    
    if project_name is None:
        project_name = 'default'
    
    directories = ensure_project_directories(user_id, project_name)
    
    if audio_type == 'user':
        audio_dir = directories['user_input']
    else:
        audio_dir = directories['ai']
    
    return os.path.join(audio_dir, filename)

def get_user_media_path(user_id: str, filename: str, project_name: Optional[str] = None) -> str:
    """
    Get the full path for a user media file.
    
    Args:
        user_id: Unique user identifier
        filename: Media filename
        project_name: Optional project name (defaults to 'default')
        
    Returns:
        Full path to the media file
    """
    if project_name is None:
        project_name = 'default'
    
    directories = ensure_project_directories(user_id, project_name)
    return os.path.join(directories['media'], filename)

def get_project_prompts_path(user_id: str, project_name: str, filename: Optional[str] = None) -> str:
    """
    Get the full path for a project prompt file.
    
    Args:
        user_id: Unique user identifier
        project_name: Project name
        filename: Optional prompt filename (if None, returns prompts directory path)
        
    Returns:
        Full path to the prompt file or prompts directory
    """
    directories = ensure_project_directories(user_id, project_name)
    if filename:
        return os.path.join(directories['prompts'], filename)
    return directories['prompts']

def get_user_media_url(user_id: str, filename: str, project_name: Optional[str] = None) -> str:
    """
    Get the URL path for serving user media files.
    
    Args:
        user_id: Unique user identifier
        filename: Media filename
        project_name: Optional project name (defaults to 'default')
        
    Returns:
        URL path for the media file
    """
    if project_name:
        return f"/api/users/{user_id}/{project_name}/media/{filename}"
    return f"/api/users/{user_id}/media/{filename}"

def get_user_audio_url(user_id: str, filename: str, audio_type: str = 'user', project_name: Optional[str] = None) -> str:
    """
    Get the URL path for serving user audio files.
    
    Args:
        user_id: Unique user identifier
        filename: Audio filename
        audio_type: 'user' for user input, 'ai' for AI response
        project_name: Optional project name (defaults to 'default')
        
    Returns:
        URL path for the audio file
    """
    if audio_type not in ['user', 'ai']:
        raise ValueError(f"Invalid audio_type: {audio_type}. Must be 'user' or 'ai'")
    
    if project_name:
        return f"/api/users/{user_id}/{project_name}/audio/{audio_type}/{filename}"
    return f"/api/users/{user_id}/audio/{audio_type}/{filename}"

def user_exists(user_id: str) -> bool:
    """
    Check if a user directory exists.
    
    Args:
        user_id: Unique user identifier
        
    Returns:
        True if user directory exists, False otherwise
    """
    user_base = get_user_base_path(user_id)
    return os.path.exists(user_base) and os.path.isdir(user_base)

def project_exists(user_id: str, project_name: str) -> bool:
    """
    Check if a project directory exists.
    
    Args:
        user_id: Unique user identifier
        project_name: Project name/identifier
        
    Returns:
        True if project directory exists, False otherwise
    """
    project_base = get_project_base_path(user_id, project_name)
    return os.path.exists(project_base) and os.path.isdir(project_base)

def list_user_projects(user_id: str) -> list:
    """
    List all projects for a user.
    
    Args:
        user_id: Unique user identifier
        
    Returns:
        List of project names
    """
    user_base = get_user_base_path(user_id)
    if not os.path.exists(user_base):
        return []
    
    projects = []
    for item in os.listdir(user_base):
        item_path = os.path.join(user_base, item)
        if os.path.isdir(item_path):
            projects.append(item)
    
    return projects

def get_user_id_from_session(session_id: Optional[str] = None) -> str:
    """
    Generate or extract user ID from session.
    For now, uses session_id directly as user_id.
    In the future, this can be enhanced to map sessions to persistent user IDs.
    
    Args:
        session_id: Session identifier (optional)
        
    Returns:
        User ID string
    """
    if session_id:
        # For now, use session_id as user_id
        # In the future, this could map to a persistent user ID
        return session_id
    
    # Generate a temporary user ID if no session provided
    import time
    import random
    return f"temp_user_{int(time.time())}_{random.randint(1000, 9999)}"

def list_user_files(user_id: str, project_name: Optional[str] = None, file_type: str = 'all') -> dict:
    """
    List files in a user's project directories.
    
    Args:
        user_id: Unique user identifier
        project_name: Optional project name (defaults to 'default')
        file_type: 'all', 'user', 'ai', or 'media'
        
    Returns:
        Dictionary with lists of files:
        {
            'user': [list of user audio files],
            'ai': [list of AI audio files],
            'media': [list of media files]
        }
    """
    if project_name is None:
        project_name = 'default'
    
    if not project_exists(user_id, project_name):
        return {'user': [], 'ai': [], 'media': []}
    
    directories = ensure_project_directories(user_id, project_name)
    result = {}
    
    if file_type in ['all', 'user']:
        user_dir = directories['user_input']
        if os.path.exists(user_dir):
            try:
                result['user'] = [f for f in os.listdir(user_dir) if os.path.isfile(os.path.join(user_dir, f))]
            except Exception as e:
                logger.error(f"Error listing user files in {user_dir}: {e}")
                result['user'] = []
        else:
            result['user'] = []
    
    if file_type in ['all', 'ai']:
        ai_dir = directories['ai']
        if os.path.exists(ai_dir):
            try:
                result['ai'] = [f for f in os.listdir(ai_dir) if os.path.isfile(os.path.join(ai_dir, f))]
            except Exception as e:
                logger.error(f"Error listing AI files in {ai_dir}: {e}")
                result['ai'] = []
        else:
            result['ai'] = []
    
    if file_type in ['all', 'media']:
        media_dir = directories['media']
        if os.path.exists(media_dir):
            try:
                # List only files, not directories
                # Exclude target source images (they're in targets/ subdirectory or have target_source_ prefix)
                all_files = [f for f in os.listdir(media_dir) if os.path.isfile(os.path.join(media_dir, f))]
                # Filter out target source images and only include content files
                result['media'] = [f for f in all_files if not f.startswith('target_source_')]
            except Exception as e:
                logger.error(f"Error listing media files in {media_dir}: {e}")
                result['media'] = []
        else:
            result['media'] = []
    
    return result

def detect_project_from_path(file_path: str) -> Optional[tuple]:
    """
    Detect user_id and project_name from a file path.
    
    Args:
        file_path: Full file path
        
    Returns:
        Tuple of (user_id, project_name) if detected, None otherwise
    """
    # Normalize path
    file_path = os.path.normpath(file_path)
    parts = file_path.split(os.sep)
    
    # Look for 'users' in path
    if 'users' not in parts:
        return None
    
    users_index = parts.index('users')
    if users_index + 1 < len(parts):
        user_id = parts[users_index + 1]
        if users_index + 2 < len(parts):
            project_name = parts[users_index + 2]
            return (user_id, project_name)
    
    return None
