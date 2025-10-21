#!/usr/bin/env python3
"""
Main entry point for Micro-Consent Pipeline CLI
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from micro_consent_pipeline.cli import main

if __name__ == "__main__":
    sys.exit(main())