#!/bin/bash
# scripts/start_dashboard.sh
# Purpose: Start the Streamlit dashboard

echo "Starting Micro-Consent Pipeline Dashboard..."
cd "$(dirname "$0")/.."
source .venv/bin/activate
streamlit run dashboard/app.py --server.port 8501