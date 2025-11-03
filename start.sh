#!/bin/bash
# Simple startup - activate venv and start backend

cd "$(dirname "$0")"

# Activate venv and start backend
source venv/bin/activate
python3 start_backend.py
