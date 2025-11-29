#!/usr/bin/env python3
"""
Diagnostic script to check audio file permissions and paths.
Run this on the server to diagnose audio save issues.
"""

import os
import sys
from pathlib import Path

def check_audio_permissions():
    """Check if audio directories exist and are writable."""
    print("🔍 Audio Permissions Diagnostic")
    print("=" * 50)
    
    # Get backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"📁 Backend directory: {backend_dir}")
    print(f"📁 Backend directory exists: {os.path.exists(backend_dir)}")
    print(f"📁 Backend directory writable: {os.access(backend_dir, os.W_OK)}")
    print()
    
    # Check data directories
    data_dir = os.path.join(backend_dir, 'data')
    data_ai_dir = os.path.join(data_dir, 'ai')
    data_user_dir = os.path.join(data_dir, 'user')
    
    print("📂 Data Directories:")
    print(f"  data/: {data_dir}")
    print(f"    Exists: {os.path.exists(data_dir)}")
    if os.path.exists(data_dir):
        print(f"    Writable: {os.access(data_dir, os.W_OK)}")
        print(f"    Permissions: {oct(os.stat(data_dir).st_mode)[-3:]}")
        print(f"    Owner: {os.stat(data_dir).st_uid}")
        print(f"    Group: {os.stat(data_dir).st_gid}")
    print()
    
    print(f"  data/ai/: {data_ai_dir}")
    print(f"    Exists: {os.path.exists(data_ai_dir)}")
    if os.path.exists(data_ai_dir):
        print(f"    Writable: {os.access(data_ai_dir, os.W_OK)}")
        print(f"    Permissions: {oct(os.stat(data_ai_dir).st_mode)[-3:]}")
        print(f"    Owner: {os.stat(data_ai_dir).st_uid}")
        print(f"    Group: {os.stat(data_ai_dir).st_gid}")
    else:
        print(f"    ⚠️ Directory does not exist - will be created on first use")
    print()
    
    print(f"  data/user/: {data_user_dir}")
    print(f"    Exists: {os.path.exists(data_user_dir)}")
    if os.path.exists(data_user_dir):
        print(f"    Writable: {os.access(data_user_dir, os.W_OK)}")
        print(f"    Permissions: {oct(os.stat(data_user_dir).st_mode)[-3:]}")
        print(f"    Owner: {os.stat(data_user_dir).st_uid}")
        print(f"    Group: {os.stat(data_user_dir).st_gid}")
    else:
        print(f"    ⚠️ Directory does not exist - will be created on first use")
    print()
    
    # Test write
    print("🧪 Testing write permissions:")
    test_file = os.path.join(data_ai_dir, 'test_write.tmp')
    try:
        # Ensure directory exists
        os.makedirs(data_ai_dir, exist_ok=True)
        
        # Try to write
        with open(test_file, 'w') as f:
            f.write('test')
        
        # Check if file was created
        if os.path.exists(test_file):
            print(f"  ✅ Successfully wrote test file: {test_file}")
            file_size = os.path.getsize(test_file)
            print(f"  ✅ File size: {file_size} bytes")
            
            # Clean up
            os.unlink(test_file)
            print(f"  ✅ Test file cleaned up")
        else:
            print(f"  ❌ Test file was not created!")
            
    except PermissionError as e:
        print(f"  ❌ Permission denied: {e}")
        print(f"  💡 Try: chmod 755 {data_ai_dir}")
        print(f"  💡 Or: chown -R $(whoami) {data_dir}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        print(f"  Traceback: {traceback.format_exc()}")
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

