#!/usr/bin/env python3
"""
Diagnostic script to check audio file permissions and paths.
Run this on the server to diagnose audio save issues.
Now checks user-specific directories.
"""

import os
import sys
from pathlib import Path

# Add backend to path to import user_manager
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from user_manager import ensure_user_directories, get_user_base_path
except ImportError:
    print("⚠️  Could not import user_manager - using fallback checks")
    ensure_user_directories = None

def check_audio_permissions():
    """Check if audio directories exist and are writable."""
    print("🔍 Audio Permissions Diagnostic (Multi-User System)")
    print("=" * 50)
    
    # Get backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"📁 Backend directory: {backend_dir}")
    print(f"📁 Backend directory exists: {os.path.exists(backend_dir)}")
    print(f"📁 Backend directory writable: {os.access(backend_dir, os.W_OK)}")
    print()
    
    # Check users directory
    users_dir = os.path.join(backend_dir, 'users')
    print("📂 Users Directory Structure:")
    print(f"  users/: {users_dir}")
    print(f"    Exists: {os.path.exists(users_dir)}")
    if os.path.exists(users_dir):
        print(f"    Writable: {os.access(users_dir, os.W_OK)}")
        print(f"    Permissions: {oct(os.stat(users_dir).st_mode)[-3:]}")
        print(f"    Owner: {os.stat(users_dir).st_uid}")
        print(f"    Group: {os.stat(users_dir).st_gid}")
        
        # List existing user directories
        user_dirs = [d for d in os.listdir(users_dir) if os.path.isdir(os.path.join(users_dir, d))]
        if user_dirs:
            print(f"    Existing users: {len(user_dirs)}")
            for user_id in user_dirs[:5]:  # Show first 5
                print(f"      - {user_id}")
            if len(user_dirs) > 5:
                print(f"      ... and {len(user_dirs) - 5} more")
        else:
            print(f"    No user directories yet (will be created on first use)")
    else:
        print(f"    ⚠️ Directory does not exist - will be created on first use")
    print()
    
    # Test with a sample user
    print("🧪 Testing user directory creation and write permissions:")
    test_user_id = "test_diagnostic_user"
    try:
        if ensure_user_directories:
            # Use user_manager to create test directories
            directories = ensure_user_directories(test_user_id)
            test_ai_dir = directories['data_ai']
            test_file = os.path.join(test_ai_dir, 'test_write.tmp')
            
            # Try to write
            with open(test_file, 'w') as f:
                f.write('test')
            
            # Check if file was created
            if os.path.exists(test_file):
                print(f"  ✅ Successfully created user directories for: {test_user_id}")
                print(f"  ✅ Successfully wrote test file: {test_file}")
                file_size = os.path.getsize(test_file)
                print(f"  ✅ File size: {file_size} bytes")
                
                # Clean up
                os.unlink(test_file)
                print(f"  ✅ Test file cleaned up")
                
                # Clean up test user directory
                import shutil
                test_user_base = get_user_base_path(test_user_id)
                if os.path.exists(test_user_base):
                    shutil.rmtree(test_user_base)
                    print(f"  ✅ Test user directory cleaned up")
            else:
                print(f"  ❌ Test file was not created!")
        else:
            # Fallback: test users directory directly
            os.makedirs(users_dir, exist_ok=True)
            test_file = os.path.join(users_dir, 'test_write.tmp')
            with open(test_file, 'w') as f:
                f.write('test')
            if os.path.exists(test_file):
                os.unlink(test_file)
                print(f"  ✅ Can write to users directory")
            else:
                print(f"  ❌ Cannot write to users directory")
            
    except PermissionError as e:
        print(f"  ❌ Permission denied: {e}")
        print(f"  💡 Try: chmod 755 {users_dir}")
        print(f"  💡 Or: chown -R $(whoami) {users_dir}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        print(f"  Traceback: {traceback.format_exc()}")
    print()
    
    # Check legacy data directories (for backward compatibility)
    data_dir = os.path.join(backend_dir, 'data')
    if os.path.exists(data_dir):
        print("📂 Legacy Data Directories (deprecated):")
        print(f"  data/: {data_dir}")
        print(f"    ⚠️  Legacy directory still exists (for backward compatibility)")
        print(f"    New files should use user-specific directories")
    print()
    
    # Check current user
    print("👤 Current User Info:")
    print(f"  Username: {os.getenv('USER', 'unknown')}")
    print(f"  UID: {os.getuid()}")
    print(f"  GID: {os.getgid()}")
    print()
    
    # Check working directory
    print("📂 Working Directory:")
    print(f"  Current: {os.getcwd()}")
    print(f"  Expected backend: {backend_dir}")
    if os.getcwd() != backend_dir:
        print(f"  ⚠️ Warning: Working directory is not backend directory!")
        print(f"  💡 This might cause relative path issues")
    print()
    
    # Check disk space
    print("💾 Disk Space:")
    try:
        import shutil
        stat = shutil.disk_usage(backend_dir)
        free_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        print(f"  Total: {total_gb:.2f} GB")
        print(f"  Free: {free_gb:.2f} GB")
        if free_gb < 0.1:
            print(f"  ⚠️ Warning: Low disk space!")
    except Exception as e:
        print(f"  ⚠️ Could not check disk space: {e}")
    print()
    
    print("=" * 50)
    print("✅ Diagnostic complete!")

if __name__ == '__main__':
    check_audio_permissions()

