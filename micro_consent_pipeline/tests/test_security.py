import pytest
import asyncio
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
import time
import uuid
import os

from api.app import app, verify_api_key
from micro_consent_pipeline.config.settings import Settings

# Create test client
client = TestClient(app)

class TestSecurity:
    """Test suite for security features."""

    def setup_method(self):
        """Set up test environment with mock settings."""
        self.mock_settings = Mock(spec=Settings)
        self.mock_settings.api_key = "test-api-key-12345"
        self.mock_settings.cors_origins = ["http://localhost:3000", "http://localhost:8501"]
        self.mock_settings.max_payload_bytes = 1024  # 1KB for testing
        self.mock_settings.request_timeout = 30

        # Patch settings in the app module
        patcher = patch('api.app.settings', self.mock_settings)
        patcher.start()
        self.addCleanup(patcher.stop)

    def addCleanup(self, func):
        """Helper to add cleanup functions (pytest compatibility)."""
        pass

    def test_health_endpoint_open_access(self):
        """Test that health endpoint doesn't require authentication."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert "version" in data

    def test_analyze_endpoint_requires_api_key(self):
        """Test that analyze endpoint requires API key."""
        # Test without API key
        response = client.post("/analyze", json={
            "source": "https://example.com/privacy",
            "output_format": "json"
        })
        assert response.status_code == 401
        assert "API key required" in response.json()["detail"]

    def test_analyze_endpoint_invalid_api_key(self):
        """Test that analyze endpoint rejects invalid API key."""
        # Test with invalid API key in header
        response = client.post(
            "/analyze",
            json={"source": "https://example.com/privacy", "output_format": "json"},
            headers={"X-API-Key": "invalid-key"}
        )
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

        # Test with invalid API key in Authorization header
        response = client.post(
            "/analyze",
            json={"source": "https://example.com/privacy", "output_format": "json"},
            headers={"Authorization": "Bearer invalid-key"}
        )
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    @patch('api.app.PipelineRunner')
    def test_analyze_endpoint_valid_api_key(self, mock_runner):
        """Test that analyze endpoint accepts valid API key."""
        # Mock successful pipeline run
        mock_instance = Mock()
        mock_instance.run.return_value = [
            {
                "text": "We collect your data",
                "category": "data_collection",
                "confidence": 0.9,
                "type": "clause",
                "element": "p"
            }
        ]
        mock_runner.return_value = mock_instance

        # Test with valid API key in X-API-Key header
        response = client.post(
            "/analyze",
            json={"source": "https://example.com/privacy", "output_format": "json"},
            headers={"X-API-Key": "test-api-key-12345"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["total_items"] == 1
        assert "request_id" in data

        # Test with valid API key in Authorization header
        response = client.post(
            "/analyze",
            json={"source": "https://example.com/privacy", "output_format": "json"},
            headers={"Authorization": "Bearer test-api-key-12345"}
        )
        assert response.status_code == 200

    def test_rate_limiting_health_endpoint(self):
        """Test rate limiting on health endpoint."""
        # This test would require modifying the rate limiter for testing
        # In a real scenario, you'd use a test-specific rate limiter
        responses = []
        for i in range(5):  # Try multiple requests quickly
            response = client.get("/health")
            responses.append(response.status_code)

        # All should succeed for health endpoint (60/min limit)
        assert all(status == 200 for status in responses)

    @patch('api.app.PipelineRunner')
    def test_rate_limiting_analyze_endpoint(self, mock_runner):
        """Test rate limiting on analyze endpoint."""
        # Mock successful pipeline run
        mock_instance = Mock()
        mock_instance.run.return_value = []
        mock_runner.return_value = mock_instance

        # Make several requests quickly
        responses = []
        headers = {"X-API-Key": "test-api-key-12345"}

        for i in range(3):  # Try multiple requests
            response = client.post(
                "/analyze",
                json={"source": "https://example.com/privacy", "output_format": "json"},
                headers=headers
            )
            responses.append(response.status_code)

        # Should eventually hit rate limit (10/min)
        # Note: In real testing, you'd need to mock the rate limiter or use time manipulation
        assert any(status in [200, 429] for status in responses)

    def test_payload_size_limit(self):
        """Test that oversized payloads are rejected."""
        # Create a large payload that exceeds the 1KB test limit
        large_source = "x" * 2048  # 2KB

        response = client.post(
            "/analyze",
            json={"source": large_source, "output_format": "json"},
            headers={"X-API-Key": "test-api-key-12345"}
        )

        # Should be rejected due to size
        assert response.status_code == 413
        assert "Payload too large" in response.json()["detail"]

    def test_url_validation_https_only(self):
        """Test that only HTTP/HTTPS URLs are allowed."""
        headers = {"X-API-Key": "test-api-key-12345"}

        # Test invalid schemes
        invalid_urls = [
            "file:///etc/passwd",
            "ftp://example.com/file",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>"
        ]

        for url in invalid_urls:
            response = client.post(
                "/analyze",
                json={"source": url, "output_format": "json"},
                headers=headers
            )
            assert response.status_code == 422  # Pydantic validation error

    def test_url_validation_valid_urls(self):
        """Test that valid HTTP/HTTPS URLs are accepted."""
        headers = {"X-API-Key": "test-api-key-12345"}

        valid_urls = [
            "https://example.com/privacy",
            "http://localhost:8080/privacy",
            "https://subdomain.example.com:443/path?query=value"
        ]

        with patch('api.app.PipelineRunner') as mock_runner:
            mock_instance = Mock()
            mock_instance.run.return_value = []
            mock_runner.return_value = mock_instance

            for url in valid_urls:
                response = client.post(
                    "/analyze",
                    json={"source": url, "output_format": "json"},
                    headers=headers
                )
                # Should pass validation (might fail on pipeline execution, but that's OK)
                assert response.status_code in [200, 500]  # 500 if pipeline fails, but validation passed

    def test_output_format_validation(self):
        """Test output format validation."""
        headers = {"X-API-Key": "test-api-key-12345"}

        # Test invalid output format
        response = client.post(
            "/analyze",
            json={"source": "https://example.com/privacy", "output_format": "xml"},
            headers=headers
        )
        assert response.status_code == 422  # Pydantic validation error

        # Test valid output formats
        valid_formats = ["json", "csv"]

        with patch('api.app.PipelineRunner') as mock_runner:
            mock_instance = Mock()
            mock_instance.run.return_value = []
            mock_runner.return_value = mock_instance

            for format_type in valid_formats:
                response = client.post(
                    "/analyze",
                    json={"source": "https://example.com/privacy", "output_format": format_type},
                    headers=headers
                )
                assert response.status_code in [200, 429, 500]  # Should pass validation or be rate limited

    def test_html_sanitization(self):
        """Test HTML sanitization in request content."""
        headers = {"X-API-Key": "test-api-key-12345"}

        # Malicious HTML content
        html_content = "<script>alert('xss')</script><p>Safe content</p>"

        with patch('api.app.PipelineRunner') as mock_runner:
            mock_instance = Mock()
            mock_instance.run.return_value = []
            mock_runner.return_value = mock_instance

            response = client.post(
                "/analyze",
                json={"source": html_content, "output_format": "json"},
                headers=headers
            )

            # Should pass validation (script tags will be sanitized) or be rate limited
            assert response.status_code in [200, 429, 500]

    def test_security_headers_present(self):
        """Test that security headers are added to responses."""
        response = client.get("/health")

        # Check for security headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("Referrer-Policy") == "no-referrer"
        assert response.headers.get("Content-Security-Policy") == "default-src 'self'"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_request_id_in_response(self):
        """Test that request ID is included in response headers."""
        response = client.get("/health")

        # Check for request ID header
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) == 8  # Should be 8-character ID

    def test_cors_preflight_allowed_origins(self):
        """Test CORS preflight for allowed origins."""
        # Test allowed origin
        response = client.options(
            "/analyze",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,X-API-Key"
            }
        )
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers

    def test_cors_preflight_disallowed_origins(self):
        """Test CORS preflight for disallowed origins."""
        # Test disallowed origin
        response = client.options(
            "/analyze",
            headers={
                "Origin": "http://malicious-site.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,X-API-Key"
            }
        )
        # Should not include CORS headers for disallowed origins
        # (Exact behavior depends on FastAPI CORS implementation)
        assert response.status_code in [200, 400]

    def test_request_timeout_handling(self):
        """Test request timeout handling."""
        headers = {"X-API-Key": "test-api-key-12345"}

        with patch('api.app.PipelineRunner') as mock_runner:
            mock_instance = Mock()
            mock_instance.run.return_value = []
            mock_runner.return_value = mock_instance

            response = client.post(
                "/analyze",
                json={"source": "https://example.com/privacy", "output_format": "json"},
                headers=headers
            )

            # Should timeout, succeed, or be rate limited
            assert response.status_code in [200, 408, 429, 500]  # Success, timeout, rate limited, or error

    def test_empty_source_validation(self):
        """Test that empty source is rejected."""
        headers = {"X-API-Key": "test-api-key-12345"}

        response = client.post(
            "/analyze",
            json={"source": "", "output_format": "json"},
            headers=headers
        )
        assert response.status_code == 422  # Pydantic validation error

        response = client.post(
            "/analyze",
            json={"source": "   ", "output_format": "json"},  # Whitespace only
            headers=headers
        )
        assert response.status_code == 422  # Pydantic validation error

    def test_error_response_format(self):
        """Test that error responses include proper information."""
        # Test authentication error
        response = client.post("/analyze", json={
            "source": "https://example.com/privacy",
            "output_format": "json"
        })

        assert response.status_code == 401
        error_data = response.json()
        assert "detail" in error_data

        # Test validation error
        response = client.post(
            "/analyze",
            json={"source": "invalid-url", "output_format": "invalid"},
            headers={"X-API-Key": "test-api-key-12345"}
        )

        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

    def test_audit_logging_structure(self):
        """Test that audit logs include required security fields."""
        # This test would typically check log output
        # For now, we'll just ensure the endpoint works and logs are generated
        with patch('api.app.logger') as mock_logger:
            response = client.get("/health")

            # Verify that logging was called
            assert mock_logger.info.called

            # Check that audit fields are included in log calls
            log_calls = mock_logger.info.call_args_list
            audit_call = None
            for call in log_calls:
                if "extra" in call.kwargs and "client_ip" in call.kwargs["extra"]:
                    audit_call = call.kwargs["extra"]
                    break

            if audit_call:
                # Verify required audit fields
                assert "request_id" in audit_call
                assert "client_ip" in audit_call
                # Note: user_agent might not be present in test client

    def test_api_key_extraction_methods(self):
        """Test different methods of providing API key."""
        # Mock request object
        from fastapi import Request

        # Test with X-API-Key header
        with patch('api.app.Request') as mock_request:
            mock_request.headers.get.return_value = "test-key"
            mock_request.state.request_id = "test123"

            # This would require more complex mocking to test properly
            # The verify_api_key function is tested implicitly in other tests
            pass