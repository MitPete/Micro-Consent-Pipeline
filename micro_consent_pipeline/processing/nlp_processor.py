# micro_consent_pipeline/processing/nlp_processor.py
# Purpose: Process text data using NLP for consent analysis

"""
Module: nlp_processor.py
Purpose: Classify extracted consent elements into semantic categories using NLP and heuristics.
"""

import time
from typing import List, Dict, Any

import spacy
from langdetect import detect

from micro_consent_pipeline.config.settings import Settings
from micro_consent_pipeline.utils.logger import get_logger, log_inference_summary


class ClauseClassifier:
    """
    Class for classifying consent clauses into categories using NLP and heuristics.
    """

    def __init__(self, model_name: str = "en_core_web_sm", settings: Settings = None) -> None:
        """
        Initialize the ClauseClassifier with a spaCy model.

        Args:
            model_name (str): Name of the spaCy model to load.
            settings (Settings): Application settings.
        """
        self.settings = settings or Settings()
        self.logger = get_logger(__name__)
        try:
            self.nlp = spacy.load(model_name)
            self.logger.info("Loaded spaCy model: %s", model_name)
        except OSError:
            self.logger.warning("spaCy model %s not found, downloading...", model_name)
            spacy.cli.download(model_name)
            self.nlp = spacy.load(model_name)

        # Keyword mappings for rule-based classification
        self.keyword_categories = {
            'analytics': 'Analytics',
            'tracking': 'Analytics',
            'performance': 'Analytics',
            'ads': 'Advertising',
            'advertising': 'Advertising',
            'marketing': 'Advertising',
            'functional': 'Functional',
            'necessary': 'Functional',
            'cookies': 'Functional',
            'essential': 'Functional',
            'accept': 'Functional',
            'reject': 'Functional',
            'social': 'Social Media',
            'facebook': 'Social Media',
            'twitter': 'Social Media',
            'personalization': 'Personalization',
            'recommendations': 'Personalization',
            'privacy': 'Privacy',
            'policy': 'Privacy',
        }

    def classify_clauses(self, consent_items: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Classify consent clauses into categories.

        Args:
            consent_items (List[Dict[str, str]]): List of consent items with 'text' key.

        Returns:
            List[Dict[str, Any]]: Classified items with category and confidence.
        """
        self.logger.info("Starting classification of %d clauses", len(consent_items))
        start_time = time.time()
        results = []
        categories_assigned = []

        for item in consent_items:
            text = item.get('text', '')
            if not text:
                continue

            # Rule-based classification
            category, confidence = self._rule_based_classify(text)

            # Placeholder for model-based classification (to be implemented)
            # if confidence < self.settings.min_confidence:
            #     category, confidence = self._model_based_classify(text)

            result = {
                "text": text,
                "category": category,
                "confidence": confidence,
                **item  # Include original keys
            }
            results.append(result)
            categories_assigned.append(category)

        elapsed_time = time.time() - start_time
        log_inference_summary(len(results), elapsed_time, categories_assigned)
        return results

    def detect_language(self, text: str) -> str:
        """
        Detect the language of the text.

        Args:
            text (str): The text to analyze.

        Returns:
            str: Detected language code (e.g., 'en').
        """
        try:
            return detect(text)
        except Exception as e:
            self.logger.warning("Language detection failed: %s", str(e))
            return 'en'  # Default to English

    def _rule_based_classify(self, text: str) -> tuple[str, float]:
        """
        Rule-based classification using keywords.

        Args:
            text (str): The text to classify.

        Returns:
            tuple[str, float]: Category and confidence score.
        """
        text_lower = text.lower()
        for keyword, category in self.keyword_categories.items():
            if keyword in text_lower:
                return category, 0.8  # High confidence for keyword match

        # Default category
        return 'Other', 0.5