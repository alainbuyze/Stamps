"""Tests for custom exceptions."""

import pytest

from src.core.errors import (
    ExtractionError,
    GenerationError,
    PageNotFoundError,
    PageTimeoutError,
    ScrapingError,
)


def test_scraping_error_hierarchy():
    """Test that scraping errors inherit correctly."""
    assert issubclass(PageNotFoundError, ScrapingError)
    assert issubclass(PageTimeoutError, ScrapingError)


def test_scraping_error_message():
    """Test that errors preserve their messages."""
    error = ScrapingError("test message")
    assert str(error) == "test message"


def test_page_not_found_error():
    """Test PageNotFoundError."""
    error = PageNotFoundError("Page not found: https://example.com")
    assert "Page not found" in str(error)


def test_page_timeout_error():
    """Test PageTimeoutError."""
    error = PageTimeoutError("Timeout loading page")
    assert "Timeout" in str(error)


def test_extraction_error():
    """Test ExtractionError is independent."""
    error = ExtractionError("Failed to extract content")
    assert not isinstance(error, ScrapingError)
    assert "extract" in str(error).lower()


def test_generation_error():
    """Test GenerationError is independent."""
    error = GenerationError("Failed to generate guide")
    assert not isinstance(error, ScrapingError)
    assert "generate" in str(error).lower()
