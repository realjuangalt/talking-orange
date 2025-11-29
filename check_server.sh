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
echo "  backend/data/ai/:"
if [ -d "backend/data/ai" ]; then
    ls -ld backend/data/ai
    echo "    Writable: $([ -w backend/data/ai ] && echo 'YES' || echo 'NO')"
else
    echo "    ❌ Does not exist"
fi

echo ""
echo "  backend/data/user/:"
if [ -d "backend/data/user" ]; then
    ls -ld backend/data/user
    echo "    Writable: $([ -w backend/data/user ] && echo 'YES' || echo 'NO')"
else
    echo "    ❌ Does not exist"
fi

echo ""
echo "🧪 Testing write permissions..."
TEST_FILE="backend/data/ai/test_write_$(date +%s).tmp"
mkdir -p backend/data/ai
if echo "test" > "$TEST_FILE" 2>/dev/null; then
    echo "  ✅ Can write to backend/data/ai/"
    rm -f "$TEST_FILE"
else
    echo "  ❌ Cannot write to backend/data/ai/"
    echo "  💡 Try: chmod 755 backend/data/ai"
    echo "  💡 Or: chown -R \$(whoami) backend/data"
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

