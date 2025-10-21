# micro_consent_pipeline/utils/logger.py
# Purpose: Configure and provide logging utilities

"""
Logger utility for consistent logging across the application with JSON structured logging.
"""

import logging
import uuid
from typing import Dict, List, Optional

from pythonjsonlogger import jsonlogger


def setup_json_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Set up a JSON logger with the specified name and level.

    Args:
        name (str): The name of the logger.
        level (str): The logging level (e.g., 'DEBUG', 'INFO').

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    logger.handlers.clear()

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with the specified name and level.

    Args:
        name (str): The name of the logger.
        level (str): The logging level (e.g., 'DEBUG', 'INFO').

    Returns:
        logging.Logger: Configured logger instance.
    """
    return setup_json_logger(name, level)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: Logger instance.
    """
    return logging.getLogger(name)


def generate_request_id() -> str:
    """
    Generate a unique request ID.

    Returns:
        str: Unique request ID.
    """
    return str(uuid.uuid4())[:8]


def log_inference_summary(count: int, elapsed_time: float, categories: List[str], request_id: Optional[str] = None) -> None:
    """
    Log a summary of inference results.

    Args:
        count (int): Number of items processed.
        elapsed_time (float): Time taken in seconds.
        categories (List[str]): List of categories assigned.
        request_id (Optional[str]): Request ID for tracking.
    """
    logger = get_logger(__name__)
    extra = {
        "duration_ms": elapsed_time * 1000,
        "items": count,
        "categories": list(set(categories)),
        "request_id": request_id or generate_request_id()
    }
    logger.info("Processed %d clauses in %.2f seconds", count, elapsed_time, extra=extra)


def log_pipeline_summary(duration: float, total_items: int, categories: Dict[str, int], request_id: Optional[str] = None) -> None:
    """
    Log a summary of the pipeline run.

    Args:
        duration (float): Total duration in seconds.
        total_items (int): Total items processed.
        categories (Dict[str, int]): Count of items per category.
        request_id (Optional[str]): Request ID for tracking.
    """
    logger = get_logger(__name__)
    extra = {
        "duration_ms": duration * 1000,
        "items": total_items,
        "categories": categories,
        "request_id": request_id or generate_request_id()
    }
    logger.info("Pipeline completed in %.2f seconds, processed %d items", duration, total_items, extra=extra)