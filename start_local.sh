#!/bin/bash

# Talking Orange AR - Local Development Server
# Usage: ./start_local.sh [--device cpu|gpu|auto] [--model small|medium]
# Examples:
#   ./start_local.sh                    # Auto-detect GPU (default), use small model
#   ./start_local.sh --device gpu       # Force GPU mode (if available)
#   ./start_local.sh --device cpu       # Force CPU mode
#   ./start_local.sh --model medium     # Use medium model
#   ./start_local.sh --device gpu --model medium  # GPU + medium model

cd "$(dirname "$0")"
source venv/bin/activate

# Default values - auto-detect GPU by default
WHISPER_DEVICE="auto"
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
            echo "  --device cpu|gpu|auto    Device mode (default: auto - detects GPU if available)"
            echo "  --model small|medium     Whisper model size (default: small)"
            echo ""
            echo "Examples:"
            echo "  $0                           # Auto-detect GPU (default), use small model"
            echo "  $0 --device gpu              # Force GPU mode (if available)"
            echo "  $0 --device cpu              # Force CPU mode"
            echo "  $0 --device gpu --model medium # GPU + medium model"
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
    echo "🔧 GPU mode requested - will use GPU if available"
    # Set PyTorch CUDA memory allocation config to help with fragmentation
    export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
    echo "💾 Set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to reduce memory fragmentation"
    # Check if CUDA is available and show memory info
    python3 -c "import torch; \
        if torch.cuda.is_available(): \
            print('✅ CUDA available:', torch.cuda.is_available()); \
            print('✅ CUDA device count:', torch.cuda.device_count()); \
            for i in range(torch.cuda.device_count()): \
                props = torch.cuda.get_device_properties(i); \
                total_mem = props.total_memory / (1024**3); \
                allocated = torch.cuda.memory_allocated(i) / (1024**3); \
                reserved = torch.cuda.memory_reserved(i) / (1024**3); \
                free = total_mem - reserved; \
                print(f'   GPU {i} ({props.name}): {total_mem:.2f} GB total, {reserved:.2f} GB reserved, {free:.2f} GB free'); \
        else: \
            print('⚠️  CUDA not available')" 2>/dev/null || echo "⚠️  Could not check CUDA availability (PyTorch may not be installed)"
else
    export WHISPER_FORCE_CPU="false"
    echo "🔧 Auto-detecting device (GPU if available, else CPU)"
    # Set PyTorch CUDA memory allocation config to help with fragmentation
    export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
    # Check if CUDA is available and show memory info
    python3 -c "import torch; \
        if torch.cuda.is_available(): \
            print('✅ CUDA available:', torch.cuda.is_available()); \
            print('✅ CUDA device count:', torch.cuda.device_count()); \
            for i in range(torch.cuda.device_count()): \
                props = torch.cuda.get_device_properties(i); \
                total_mem = props.total_memory / (1024**3); \
                allocated = torch.cuda.memory_allocated(i) / (1024**3); \
                reserved = torch.cuda.memory_reserved(i) / (1024**3); \
                free = total_mem - reserved; \
                print(f'   GPU {i} ({props.name}): {total_mem:.2f} GB total, {reserved:.2f} GB reserved, {free:.2f} GB free'); \
        else: \
            print('⚠️  CUDA not available')" 2>/dev/null || echo "⚠️  Could not check CUDA availability (PyTorch may not be installed)"
fi

echo "🔧 Whisper model: $WHISPER_MODEL"
echo "🚀 Starting backend server..."
echo ""

# Set DEBUG mode for development (enables Flask debug mode and detailed logging)
export DEBUG=true

cd backend
python3 app.py

