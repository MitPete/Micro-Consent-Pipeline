# micro_consent_pipeline/ingestion/extractor.py
# Purpose: Extract data from various sources for consent analysis

"""
Module: extractor.py
Purpose: Extract consent-related UI text and metadata from HTML/JSON inputs for downstream processing.
"""

import json
import os
from typing import List, Dict, Union

import requests
from bs4 import BeautifulSoup

from micro_consent_pipeline.config.settings import Settings
from micro_consent_pipeline.utils.logger import get_logger


class ConsentExtractor:
    """
    Class for extracting consent-related elements from HTML or JSON sources.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the ConsentExtractor with settings.

        Args:
            settings (Settings): Application settings.
        """
        self.settings = settings
        self.logger = get_logger(__name__)

    def load_source(self, source: str) -> Union[str, dict]:
        """
        Load content from a source, auto-detecting if it's a URL, file, or raw string.

        Args:
            source (str): The source to load from.

        Returns:
            Union[str, dict]: The loaded content as string or dict.
        """
        self.logger.info("Loading source: %s", source)
        if source.startswith(('http://', 'https://')):
            self.logger.debug("Fetching URL: %s", source)
            response = requests.get(source, timeout=self.settings.request_timeout)
            response.raise_for_status()
            content = response.text
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return content
        elif os.path.isfile(source):
            self.logger.debug("Reading file: %s", source)
            with open(source, 'r', encoding='utf-8') as f:
                content = f.read()
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return content
        else:
            self.logger.debug("Treating as raw content")
            try:
                return json.loads(source)
            except json.JSONDecodeError:
                return source

    def from_html(self, html_content: str) -> List[Dict[str, str]]:
        """
        Extract consent elements from HTML content.

        Args:
            html_content (str): The HTML content to parse.

        Returns:
            List[Dict[str, str]]: List of extracted elements.
        """
        self.logger.info("Starting HTML extraction")
        soup = BeautifulSoup(html_content, 'html.parser')
        elements: List[Dict[str, str]] = []

        # Extract checkboxes with labels
        for checkbox in soup.find_all('input', {'type': 'checkbox'}):
            label = checkbox.find_next('label')
            if label:
                text = label.get_text(strip=True)
                if text:
                    elements.append({
                        "type": "checkbox",
                        "text": text,
                        "element": "input"
                    })

        # Extract buttons
        buttons = soup.find_all('button')
        inputs = soup.find_all('input', {'type': ['submit', 'button']})
        for button in buttons + inputs:
            text = button.get('value') or button.get_text(strip=True)
            if text and any(word in text.lower() for word in ['accept', 'reject', 'consent', 'agree', 'decline', 'manage', 'preferences']):
                elements.append({
                    "type": "button",
                    "text": text,
                    "element": "button"
                })

        # Extract links related to privacy/consent
        for link in soup.find_all('a'):
            text = link.get_text(strip=True)
            if text and any(word in text.lower() for word in ['privacy', 'cookie', 'consent', 'policy', 'preferences']):
                elements.append({
                    "type": "link",
                    "text": text,
                    "element": "a"
                })

        # Extract cookie banner text
        for div in soup.find_all(['div', 'section'], class_=lambda c: c and any(word in ' '.join(c).lower() for word in ['cookie', 'consent', 'gdpr'])):
            text = div.get_text(strip=True)
            if text and len(text) > 10:  # Avoid too short texts
                elements.append({
                    "type": "banner",
                    "text": text,
                    "element": "div"
                })

        self.logger.info("Extracted %d elements from HTML", len(elements))
        return elements

    def from_json(self, json_data: dict) -> List[Dict[str, str]]:
        """
        Extract consent elements from JSON data.

        Args:
            json_data (dict): The JSON data to parse.

        Returns:
            List[Dict[str, str]]: List of extracted elements.
        """
        self.logger.info("Starting JSON extraction")
        elements: List[Dict[str, str]] = []

        # Look for common consent-related keys
        consent_keys = ['consent_elements', 'buttons', 'checkboxes', 'links', 'banners']
        for key in consent_keys:
            if key in json_data and isinstance(json_data[key], list):
                for item in json_data[key]:
                    if isinstance(item, dict) and 'text' in item:
                        elements.append({
                            "type": item.get('type', 'unknown'),
                            "text": item['text'],
                            "element": item.get('element', 'unknown')
                        })

        # If no specific keys, flatten dict values that are lists of dicts
        if not elements:
            for value in json_data.values():
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and 'text' in item:
                            elements.append({
                                "type": item.get('type', 'unknown'),
                                "text": item['text'],
                                "element": item.get('element', 'unknown')
                            })

        self.logger.info("Extracted %d elements from JSON", len(elements))
        return elements