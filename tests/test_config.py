"""Tests for configuration management."""

from src.core.config import Settings, get_settings


def test_settings_defaults():
    """Test that settings have correct default values.

    Note: Settings are loaded from .env files if present, so we test
    that settings exist and have reasonable types rather than exact values.
    """
    settings = Settings()

    assert settings.OUTPUT_DIR == "./output"
    assert settings.CACHE_DIR == "./cache"
    assert settings.RATE_LIMIT_SECONDS >= 0
    assert settings.BROWSER_HEADLESS is True
    assert settings.BROWSER_TIMEOUT >= 30000  # At least 30 seconds
    assert settings.LOG_LEVEL in ("DEBUG", "INFO", "WARNING", "ERROR")
    # Retry settings
    assert settings.SCRAPE_MAX_RETRIES >= 1
    assert settings.SCRAPE_RETRY_DELAY > 0
    assert settings.SCRAPE_RETRY_BACKOFF >= 1.0


def test_get_settings_singleton():
    """Test that get_settings returns the same instance."""
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2
