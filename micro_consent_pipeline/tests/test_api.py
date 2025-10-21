# micro_consent_pipeline/tests/test_api.py
# Purpose: Unit tests for the FastAPI endpoints

"""
Tests for the FastAPI application.
"""

import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from api.app import app

# Mock the settings to include the test API key
@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings with test API key."""
    with patch('api.app.settings') as mock_settings:
        mock_settings.api_key = 'test-api-key-12345'
        mock_settings.cors_origins = ['http://localhost:3000', 'http://localhost:8501']
        mock_settings.max_payload_bytes = 10485760
        mock_settings.request_timeout = 30
        yield mock_settings

client = TestClient(app)


def test_health_endpoint():
    """
    Test the health check endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_analyze_endpoint():
    """
    Test the analyze endpoint with sample HTML.
    """
    test_html = """
    <html>
    <body>
        <button>Accept All</button>
        <button>Reject All</button>
        <a href="#">Privacy Policy</a>
    </body>
    </html>
    """

    response = client.post(
        "/analyze",
        json={"source": test_html, "output_format": "json"},
        headers={"X-API-Key": "test-api-key-12345"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["total_items"] > 0
    assert "items" in data
    assert "categories" in data

    # Check item structure
    for item in data["items"]:
        assert "text" in item
        assert "category" in item
        assert "confidence" in item
        assert "type" in item
        assert "element" in item


def test_analyze_endpoint_empty_content():
    """
    Test the analyze endpoint with empty content.
    """
    response = client.post(
        "/analyze",
        json={"source": "", "output_format": "json"},
        headers={"X-API-Key": "test-api-key-12345"}
    )

    # Empty content should be rejected with validation error
    assert response.status_code == 422  # Validation error


def test_analyze_endpoint_invalid_request():
    """
    Test the analyze endpoint with invalid request.
    """
    response = client.post(
        "/analyze",
        json={},  # Missing required fields
        headers={"X-API-Key": "test-api-key-12345"}
    )

    assert response.status_code == 422  # Validation error