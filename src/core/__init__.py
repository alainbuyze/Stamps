"""Core module - configuration, logging, and error handling."""

from src.core.config import Settings, get_settings
from src.core.errors import (
    ExtractionError,
    GenerationError,
    PageNotFoundError,
    PageTimeoutError,
    ScrapingError,
)

__all__ = [
    "Settings",
    "get_settings",
    "ScrapingError",
    "PageNotFoundError",
    "PageTimeoutError",
    "ExtractionError",
    "GenerationError",
]
