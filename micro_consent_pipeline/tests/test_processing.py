# micro_consent_pipeline/tests/test_processing.py
# Purpose: Unit tests for the processing module

"""
Tests for the processing module.
"""

import pytest
from micro_consent_pipeline.config.settings import Settings
from micro_consent_pipeline.processing.nlp_processor import ClauseClassifier


def test_clause_classifier_initialization():
    """
    Test that the ClauseClassifier can be initialized and loads spaCy model.
    """
    settings = Settings()
    classifier = ClauseClassifier(settings=settings)
    assert classifier is not None
    assert classifier.nlp is not None


def test_classify_clauses():
    """
    Test classification of consent clauses.
    """
    settings = Settings()
    classifier = ClauseClassifier(settings=settings)
    consent_items = [
        {"text": "We use cookies for analytics"},
        {"text": "Accept ads from partners"},
        {"text": "Essential cookies for functionality"},
        {"text": "Some random text"}
    ]
    results = classifier.classify_clauses(consent_items)
    assert len(results) == 4
    for result in results:
        assert 'category' in result
        assert 'confidence' in result
        assert isinstance(result['confidence'], float)
        assert 0 <= result['confidence'] <= 1
        assert result['category'] != ''


def test_keyword_mapping():
    """
    Test keyword-based mapping.
    """
    settings = Settings()
    classifier = ClauseClassifier(settings=settings)
    # Test specific mappings via public method
    results = classifier.classify_clauses([{"text": "cookies"}])
    assert results[0]['category'] == 'Functional'
    assert results[0]['confidence'] == 0.8

    results = classifier.classify_clauses([{"text": "ads"}])
    assert results[0]['category'] == 'Advertising'

    results = classifier.classify_clauses([{"text": "analytics"}])
    assert results[0]['category'] == 'Analytics'

    results = classifier.classify_clauses([{"text": "unknown text"}])
    assert results[0]['category'] == 'Other'
    assert results[0]['confidence'] == 0.5


def test_detect_language():
    """
    Test language detection.
    """
    settings = Settings()
    classifier = ClauseClassifier(settings=settings)
    lang = classifier.detect_language("This is English text")
    assert isinstance(lang, str)
    assert len(lang) == 2  # Language code