#!/bin/bash
# Server diagnostic script
# Run this on your server to check audio permissions and paths

echo "🔍 Server Audio Diagnostic"
echo "=========================="
echo ""

# Check if we're in the right directory
if [ ! -f "backend/app.py" ]; then
    echo "❌ Error: Must run from project root directory"
    echo "   Current directory: $(pwd)"
    exit 1
fi

echo "📁 Project root: $(pwd)"
echo ""

# Check directories
echo "📂 Checking directories..."
echo "  backend/users/:"
if [ -d "backend/users" ]; then
    ls -ld backend/users
    echo "    Writable: $([ -w backend/users ] && echo 'YES' || echo 'NO')"
    USER_COUNT=$(find backend/users -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
    echo "    User directories: $USER_COUNT"
    if [ "$USER_COUNT" -gt 0 ]; then
        echo "    Sample users:"
        find backend/users -mindepth 1 -maxdepth 1 -type d | head -3 | while read user_dir; do
            echo "      - $(basename "$user_dir")"
        done
    fi
else
    echo "    ⚠️  Does not exist (will be created on first use)"
fi

echo ""
echo "  Legacy backend/data/ (deprecated):"
if [ -d "backend/data" ]; then
    echo "    ⚠️  Legacy directory still exists (for backward compatibility)"
    echo "    New files should use user-specific directories"
else
    echo "    ✅ Legacy directory removed (using new user system)"
fi

echo ""
echo "🧪 Testing write permissions..."
TEST_USER_DIR="backend/users/test_write_$(date +%s)"
mkdir -p "$TEST_USER_DIR/data/ai" 2>/dev/null
TEST_FILE="$TEST_USER_DIR/data/ai/test.tmp"
if echo "test" > "$TEST_FILE" 2>/dev/null; then
    echo "  ✅ Can write to user directories"
    rm -rf "$TEST_USER_DIR"
else
    echo "  ❌ Cannot write to user directories"
    echo "  💡 Try: chmod 755 backend/users"
    echo "  💡 Or: chown -R \$(whoami) backend/users"
    [ -d "$TEST_USER_DIR" ] && rm -rf "$TEST_USER_DIR" 2>/dev/null
fi

echo ""
echo "👤 Current user: $(whoami)"
echo "   UID: $(id -u)"
echo "   GID: $(id -g)"

echo ""
echo "💾 Disk space:"
df -h . | tail -1

echo ""
echo "🐍 Python diagnostic:"
cd backend
if [ -f "check_audio_permissions.py" ]; then
    python3 check_audio_permissions.py
else
    echo "  ⚠️ check_audio_permissions.py not found"
fi

