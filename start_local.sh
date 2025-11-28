#!/bin/bash

# Talking Orange AR - Local Development Server
# Usage: ./start_local.sh [--device cpu|gpu] [--model small|medium]
# Examples:
#   ./start_local.sh                    # Auto-detect GPU, use medium model
#   ./start_local.sh --device cpu       # Force CPU mode
#   ./start_local.sh --device gpu       # Force GPU mode (if available)
#   ./start_local.sh --model small      # Use small model
#   ./start_local.sh --device cpu --model small  # CPU + small model

cd "$(dirname "$0")"
source venv/bin/activate

# Default values
WHISPER_DEVICE="cpu"
WHISPER_MODEL="small"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --device)
            WHISPER_DEVICE="$2"
            shift 2
            ;;
        --model)
            WHISPER_MODEL="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--device cpu|gpu] [--model small|medium]"
            echo ""
            echo "Options:"
            echo "  --device cpu|gpu    Force CPU or GPU mode (default: auto-detect)"
            echo "  --model small|medium Whisper model size (default: medium)"
            echo ""
            echo "Examples:"
            echo "  $0                           # Auto-detect GPU, use medium model"
            echo "  $0 --device cpu              # Force CPU mode"
            echo "  $0 --device gpu --model small # GPU + small model"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate model
if [[ "$WHISPER_MODEL" != "small" && "$WHISPER_MODEL" != "medium" ]]; then
    echo "Error: Model must be 'small' or 'medium'"
    exit 1
fi

# Validate device
if [[ "$WHISPER_DEVICE" != "auto" && "$WHISPER_DEVICE" != "cpu" && "$WHISPER_DEVICE" != "gpu" ]]; then
    echo "Error: Device must be 'auto', 'cpu', or 'gpu'"
    exit 1
fi

# Set environment variables
export WHISPER_MODEL_NAME="$WHISPER_MODEL"

if [[ "$WHISPER_DEVICE" == "cpu" ]]; then
    export WHISPER_FORCE_CPU="true"
    echo "🔧 Forcing CPU mode"
elif [[ "$WHISPER_DEVICE" == "gpu" ]]; then
    export WHISPER_FORCE_CPU="false"
    echo "🔧 GPU mode (will use GPU if available)"
else
    export WHISPER_FORCE_CPU="false"
    echo "🔧 Auto-detecting device (GPU if available, else CPU)"
fi

echo "🔧 Whisper model: $WHISPER_MODEL"
echo "🚀 Starting backend server..."
echo ""

cd backend
python3 app.py

