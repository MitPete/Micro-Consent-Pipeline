# micro_consent_pipeline/__init__.py
# Purpose: Initialize the micro_consent_pipeline package

"""
Micro-Consent Pipeline Package.

This package provides a lightweight privacy consent analysis pipeline.
"""

import os
from pathlib import Path

# Read version from VERSION file
_version_file = Path(__file__).parent.parent / "VERSION"
try:
    __version__ = _version_file.read_text().strip()
except FileNotFoundError:
    __version__ = "unknown"

from .pipeline_runner import PipelineRunner

__all__ = ["PipelineRunner"]