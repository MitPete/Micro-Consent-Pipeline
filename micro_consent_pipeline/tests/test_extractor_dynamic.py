# micro_consent_pipeline/tests/test_extractor_dynamic.py
# Purpose: Test dynamic HTML extraction with Playwright

"""
Test dynamic HTML extraction functionality.
"""

import pytest
from unittest.mock import patch, MagicMock

from micro_consent_pipeline.config.settings import Settings
from micro_consent_pipeline.ingestion.extractor import ConsentExtractor


class TestDynamicExtraction:
    """Test cases for dynamic HTML extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.settings = Settings()
        self.settings.enable_js_render = True
        self.settings.js_render_timeout = 30

    def test_extractor_init_with_js_enabled(self):
        """Test extractor initialization with JS rendering enabled."""
        extractor = ConsentExtractor(self.settings, enable_js=True)
        assert extractor.enable_js is True

    def test_extractor_init_with_js_disabled(self):
        """Test extractor initialization with JS rendering disabled."""
        extractor = ConsentExtractor(self.settings, enable_js=False)
        assert extractor.enable_js is False

    def test_extractor_init_uses_settings_default(self):
        """Test extractor initialization uses settings default when enable_js not specified."""
        extractor = ConsentExtractor(self.settings)
        assert extractor.enable_js == self.settings.enable_js_render

    @patch('micro_consent_pipeline.ingestion.extractor.requests.get')
    def test_fetch_static_html(self, mock_get):
        """Test static HTML fetching."""
        mock_response = MagicMock()
        mock_response.text = '<html><body>Test content</body></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        extractor = ConsentExtractor(self.settings)
        result = extractor._fetch_static_html('http://example.com')

        assert result == '<html><body>Test content</body></html>'
        mock_get.assert_called_once_with('http://example.com', timeout=self.settings.request_timeout)

    @patch('micro_consent_pipeline.ingestion.extractor.sync_playwright')
    def test_fetch_dynamic_html(self, mock_sync_playwright):
        """Test dynamic HTML fetching with Playwright."""
        # Mock the Playwright context
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.content.return_value = '<html><body>Dynamic content</body></html>'
        mock_browser.new_page.return_value = mock_page
        mock_browser.close.return_value = None

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        extractor = ConsentExtractor(self.settings)
        result = extractor._fetch_dynamic_html('http://example.com')

        assert result == '<html><body>Dynamic content</body></html>'
        mock_page.goto.assert_called_once_with('http://example.com', timeout=30000)  # 30 seconds in ms

    @patch('micro_consent_pipeline.ingestion.extractor.sync_playwright')
    def test_dynamic_rendering_fallback_on_failure(self, mock_sync_playwright):
        """Test that dynamic rendering falls back to static on failure."""
        # Mock Playwright to raise an exception
        mock_sync_playwright.side_effect = Exception("Browser failed")

        # Mock static request
        with patch('micro_consent_pipeline.ingestion.extractor.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = '<html><body>Fallback content</body></html>'
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            extractor = ConsentExtractor(self.settings, enable_js=True)
            result = extractor.load_source('http://example.com')

            # Should fall back to static and return the HTML content
            assert result == '<html><body>Fallback content</body></html>'

    def test_load_source_with_js_disabled(self):
        """Test load_source uses static fetching when JS is disabled."""
        with patch('micro_consent_pipeline.ingestion.extractor.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = '<html><body>Static content</body></html>'
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            extractor = ConsentExtractor(self.settings, enable_js=False)
            result = extractor.load_source('http://example.com')

            assert result == '<html><body>Static content</body></html>'