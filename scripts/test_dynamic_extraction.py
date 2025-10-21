#!/usr/bin/env python3
# scripts/test_dynamic_extraction.py
# Purpose: Test script to demonstrate dynamic HTML extraction with Playwright

"""
Test script to demonstrate dynamic HTML extraction functionality.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from micro_consent_pipeline.config.settings import Settings
from micro_consent_pipeline.ingestion.extractor import ConsentExtractor


def test_dynamic_extraction():
    """Test dynamic extraction with a simple HTML string."""
    print("Testing dynamic HTML extraction...")

    # Create settings with JS rendering enabled
    settings = Settings()
    settings.enable_js_render = True
    settings.js_render_timeout = 10

    # Create extractor with JS enabled
    extractor = ConsentExtractor(settings, enable_js=True)

    # Test with a simple HTML string (not a URL, so it will use static extraction)
    html_content = """
    <html>
    <body>
        <h1>Test Page</h1>
        <button id="accept-btn" onclick="acceptCookies()">Accept Cookies</button>
        <input type="checkbox" id="consent-checkbox"> I agree to terms
        <div class="consent-banner">
            <p>This site uses cookies. Please accept our terms.</p>
        </div>
    </body>
    </html>
    """

    # Load the HTML content
    result = extractor.load_source(html_content)
    print(f"Loaded content type: {type(result)}")
    print(f"Content length: {len(result) if isinstance(result, str) else 'N/A'}")

    # Extract consent elements
    elements = extractor.from_html(result)
    print(f"Extracted {len(elements)} consent elements:")
    for elem in elements:
        print(f"  - {elem}")

    print("Dynamic extraction test completed successfully!")


if __name__ == "__main__":
    test_dynamic_extraction()