import subprocess
import sys
from pathlib import Path

import pytest
from micro_consent_pipeline import __version__


def test_version_file_matches_package_version():
    version_file = Path(__file__).parents[2] / "VERSION"
    assert version_file.exists(), "VERSION file must exist"
    file_version = version_file.read_text().strip()
    assert file_version == __version__, f"VERSION file ({file_version}) != package version ({__version__})"


def test_cli_version_flag_outputs_version():
    # Run the CLI with --version
    res = subprocess.run([sys.executable, str(Path(__file__).parents[2] / 'main.py'), '--version'], capture_output=True, text=True)
    assert res.returncode == 0
    assert __version__ in res.stdout


def test_health_endpoint_returns_version():
    # Start the FastAPI app and query /health using TestClient
    from api.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        resp = client.get('/health')

    assert resp.status_code == 200
    data = resp.json()
    assert 'version' in data
    assert data['version'] == __version__
