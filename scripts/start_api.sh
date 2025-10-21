#!/bin/bash
# scripts/start_api.sh
# Purpose: Start the FastAPI server

echo "Starting Micro-Consent Pipeline API..."
cd "$(dirname "$0")/.."
source .venv/bin/activate
python api/app.py