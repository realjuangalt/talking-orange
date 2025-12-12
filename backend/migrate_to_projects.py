#!/usr/bin/env python3
"""
Migration script to move existing user data from old structure to new project-based structure.

Old structure:
- users/{user_id}/media/
- users/{user_id}/data/user/
- users/{user_id}/data/ai/

New structure:
- users/{user_id}/{project_name}/media/
- users/{user_id}/{project_name}/user-input/
- users/{user_id}/{project_name}/ai/

This script will:
1. Detect users with old structure
2. Create a default project (or use specified project name)
3. Move data to new structure
4. Preserve old structure as backup
"""

import os
import shutil
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def migrate_user_to_projects(user_id: str, project_name: str = 'talking-orange', backup: bool = True):
    """
    Migrate a user's data from old structure to new project structure.
    
    Args:
        user_id: User identifier
        project_name: Project name to use (default: 'talking-orange')
        backup: Whether to keep old structure as backup (default: True)
    """
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    user_base = os.path.join(backend_dir, 'users', user_id)
    
    if not os.path.exists(user_base):
        logger.warning(f"⚠️  User directory does not exist: {user_base}")
        return False
    
    # Check if already migrated (has project directories)
    has_projects = False
    for item in os.listdir(user_base):
        item_path = os.path.join(user_base, item)
        if os.path.isdir(item_path):
            # Check if it looks like a project (has media, ai, or user-input)
            subdirs = [d for d in os.listdir(item_path) if os.path.isdir(os.path.join(item_path, d))]
            if any(d in ['media', 'ai', 'user-input'] for d in subdirs):
                logger.info(f"✅ User {user_id} already has project structure")
                return True
    
    # Check if old structure exists
    old_media = os.path.join(user_base, 'media')
    old_data_user = os.path.join(user_base, 'data', 'user')
    old_data_ai = os.path.join(user_base, 'data', 'ai')
    
    has_old_structure = (
        os.path.exists(old_media) or
        os.path.exists(old_data_user) or
        os.path.exists(old_data_ai)
    )
    
    if not has_old_structure:
        logger.info(f"ℹ️  User {user_id} has no data to migrate")
        return True
    
    logger.info(f"🔄 Migrating user {user_id} to project '{project_name}'...")
    
    # Create project directory structure
    project_base = os.path.join(user_base, project_name)
    project_media = os.path.join(project_base, 'media')
    project_user_input = os.path.join(project_base, 'user-input')
    project_ai = os.path.join(project_base, 'ai')
    
    os.makedirs(project_media, exist_ok=True)
    os.makedirs(project_user_input, exist_ok=True)
    os.makedirs(project_ai, exist_ok=True)
    
    # Migrate media
    if os.path.exists(old_media):
        logger.info(f"  📁 Migrating media from {old_media} to {project_media}")
        for item in os.listdir(old_media):
            src = os.path.join(old_media, item)
            dst = os.path.join(project_media, item)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                logger.info(f"    ✅ Copied {item}")
            elif os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
                logger.info(f"    ✅ Copied directory {item}/")
    
    # Migrate user input audio
    if os.path.exists(old_data_user):
        logger.info(f"  🎤 Migrating user input from {old_data_user} to {project_user_input}")
        for item in os.listdir(old_data_user):
            src = os.path.join(old_data_user, item)
            dst = os.path.join(project_user_input, item)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                logger.info(f"    ✅ Copied {item}")
    
    # Migrate AI audio
    if os.path.exists(old_data_ai):
        logger.info(f"  🤖 Migrating AI audio from {old_data_ai} to {project_ai}")
        for item in os.listdir(old_data_ai):
            src = os.path.join(old_data_ai, item)
            dst = os.path.join(project_ai, item)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                logger.info(f"    ✅ Copied {item}")
    
    # Backup old structure if requested
    if backup:
        backup_dir = os.path.join(user_base, '_backup_old_structure')
        if not os.path.exists(backup_dir):
            logger.info(f"  💾 Creating backup at {backup_dir}")
            os.makedirs(backup_dir, exist_ok=True)
            
            if os.path.exists(old_media):
                shutil.copytree(old_media, os.path.join(backup_dir, 'media'), dirs_exist_ok=True)
            if os.path.exists(os.path.join(user_base, 'data')):
                shutil.copytree(os.path.join(user_base, 'data'), os.path.join(backup_dir, 'data'), dirs_exist_ok=True)
    
    logger.info(f"✅ Migration complete for user {user_id}")
    return True

def migrate_all_users(project_name: str = 'talking-orange', backup: bool = True):
    """
    Migrate all users with old structure to new project structure.
    
    Args:
        project_name: Default project name to use
        backup: Whether to keep old structure as backup
    """
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    users_dir = os.path.join(backend_dir, 'users')
    
    if not os.path.exists(users_dir):
        logger.warning(f"⚠️  Users directory does not exist: {users_dir}")
        return
    
    logger.info(f"🔍 Scanning for users to migrate in {users_dir}...")
    
    migrated = 0
    skipped = 0
    
    for user_id in os.listdir(users_dir):
        user_path = os.path.join(users_dir, user_id)
        if not os.path.isdir(user_path):
            continue
        
        # Skip backup directories
        if user_id.startswith('_'):
            continue
        
        # Skip if already has project structure
        has_projects = False
        for item in os.listdir(user_path):
            item_path = os.path.join(user_path, item)
            if os.path.isdir(item_path):
                subdirs = [d for d in os.listdir(item_path) if os.path.isdir(os.path.join(item_path, d))]
                if any(d in ['media', 'ai', 'user-input'] for d in subdirs):
                    has_projects = True
                    break
        
        if has_projects:
            logger.info(f"⏭️  Skipping {user_id} (already has project structure)")
            skipped += 1
            continue
        
        # Check if has old structure
        old_media = os.path.join(user_path, 'media')
        old_data = os.path.join(user_path, 'data')
        
        if os.path.exists(old_media) or os.path.exists(old_data):
            if migrate_user_to_projects(user_id, project_name, backup):
                migrated += 1
        else:
            skipped += 1
    
    logger.info(f"\n📊 Migration Summary:")
    logger.info(f"  ✅ Migrated: {migrated} users")
    logger.info(f"  ⏭️  Skipped: {skipped} users")

if __name__ == '__main__':
    import sys
    
    # Default: migrate all users to 'talking-orange' project
    project_name = sys.argv[1] if len(sys.argv) > 1 else 'talking-orange'
    backup = '--no-backup' not in sys.argv
    
    logger.info("🚀 Starting migration to project-based structure...")
    logger.info(f"   Project name: {project_name}")
    logger.info(f"   Backup old structure: {backup}")
    logger.info("")
    
    migrate_all_users(project_name, backup)
    
    logger.info("\n✅ Migration complete!")

