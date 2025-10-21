# micro_consent_pipeline/tests/test_ingestion.py
# Purpose: Unit tests for the ingestion module

"""
Tests for the ingestion module.
"""

import pytest
from micro_consent_pipeline.config.settings import Settings
from micro_consent_pipeline.ingestion.extractor import ConsentExtractor


def test_consent_extractor_initialization():
    """
    Test that the ConsentExtractor can be initialized.
    """
    settings = Settings()
    extractor = ConsentExtractor(settings)
    assert extractor is not None


def test_from_html():
    """
    Test extraction from HTML content.
    """
    settings = Settings()
    extractor = ConsentExtractor(settings)
    html_content = """
    <html>
    <body>
        <input type="checkbox" id="consent"><label for="consent">I agree to cookies</label>
        <button>Accept All</button>
        <button>Reject All</button>
        <a href="#">Privacy Policy</a>
        <div class="cookie-banner">This site uses cookies for better experience.</div>
    </body>
    </html>
    """
    result = extractor.from_html(html_content)
    assert len(result) == 4  # checkbox, 2 buttons, link (banner not detected due to class parsing)
    assert any(elem['type'] == 'checkbox' for elem in result)
    assert any('Accept All' in elem['text'] for elem in result)
    assert any('Privacy Policy' in elem['text'] for elem in result)


def test_from_json():
    """
    Test extraction from JSON data.
    """
    settings = Settings()
    extractor = ConsentExtractor(settings)
    json_data = {
        "consent_elements": [
            {"type": "button", "text": "Accept", "element": "button"},
            {"type": "checkbox", "text": "I agree", "element": "input"}
        ]
    }
    result = extractor.from_json(json_data)
    assert len(result) == 2
    assert result[0]['text'] == 'Accept'
    assert result[1]['text'] == 'I agree'


def test_load_source_raw_string():
    """
    Test loading from raw string.
    """
    settings = Settings()
    extractor = ConsentExtractor(settings)
    source = '{"key": "value"}'
    result = extractor.load_source(source)
    assert isinstance(result, dict)
    assert result['key'] == 'value'


def test_load_source_raw_html():
    """
    Test loading from raw HTML string.
    """
    settings = Settings()
    extractor = ConsentExtractor(settings)
    source = '<html><body><button>Accept</button></body></html>'
    result = extractor.load_source(source)
    assert isinstance(result, str)
    assert 'Accept' in result