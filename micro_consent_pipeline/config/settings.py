# micro_consent_pipeline/config/settings.py
# Purpose: Manage application settings and environment variables

"""
Settings module for loading configuration from environment variables.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """
    Application settings loaded from environment variables.
    """

    def __init__(self) -> None:
        """
        Initialize settings with default values from environment variables.
        """
        self.database_url: Optional[str] = os.getenv('DATABASE_URL')
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
        self.nlp_model: str = os.getenv('NLP_MODEL', 'en_core_web_sm')
        self.debug_logging: bool = os.getenv('DEBUG_LOGGING', 'false').lower() == 'true'
        self.request_timeout: int = int(os.getenv('REQUEST_TIMEOUT', '10'))
        self.input_format: str = os.getenv('INPUT_FORMAT', 'auto')
        self.default_model: str = os.getenv('DEFAULT_MODEL', 'en_core_web_sm')
        self.language_support: str = os.getenv('LANGUAGE_SUPPORT', 'en')
        self.min_confidence: float = float(os.getenv('MIN_CONFIDENCE', '0.5'))
        self.output_dir: str = os.getenv('OUTPUT_DIR', 'outputs')
        self.default_format: str = os.getenv('DEFAULT_FORMAT', 'json')
        self.pipeline_timeout: int = int(os.getenv('PIPELINE_TIMEOUT', '300'))
        self.fastapi_port: int = int(os.getenv('FASTAPI_PORT', '8000'))
        self.streamlit_port: int = int(os.getenv('STREAMLIT_PORT', '8501'))

        # Observability settings
        self.enable_tracing: bool = os.getenv('ENABLE_TRACING', 'false').lower() == 'true'
        self.otel_exporter_otlp_endpoint: str = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4317')
        self.service_name: str = os.getenv('SERVICE_NAME', 'micro-consent-pipeline')

        # Security settings
        self.api_key: Optional[str] = os.getenv('API_KEY')
        self.allowed_origins: str = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:8501')
        self.max_payload_bytes: int = int(os.getenv('MAX_PAYLOAD_BYTES', '10485760'))  # 10MB default
        self.request_timeout: int = int(os.getenv('REQUEST_TIMEOUT', '30'))  # Override existing with security focus
        self.cors_origins: list = [origin.strip() for origin in self.allowed_origins.split(',') if origin.strip()]

        # Database settings
        self.database_url: str = os.getenv('DATABASE_URL', 'sqlite:///data/micro_consent.db')
        self.database_echo: bool = os.getenv('DATABASE_ECHO', 'false').lower() == 'true'

        # Async job queue settings
        self.redis_url: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.job_timeout: int = int(os.getenv('JOB_TIMEOUT', '300'))  # 5 minutes default
        self.result_ttl: int = int(os.getenv('RESULT_TTL', '3600'))  # 1 hour default