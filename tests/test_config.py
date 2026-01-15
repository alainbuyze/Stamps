"""Tests for configuration management."""

from src.core.config import Settings, get_settings


def test_settings_defaults():
    """Test that settings have correct default values."""
    settings = Settings()

    assert settings.OUTPUT_DIR == "./output"
    assert settings.CACHE_DIR == "./cache"
    assert settings.RATE_LIMIT_SECONDS == 2.0
    assert settings.BROWSER_HEADLESS is True
    assert settings.BROWSER_TIMEOUT == 30000
    assert settings.LOG_LEVEL == "INFO"


def test_get_settings_singleton():
    """Test that get_settings returns the same instance."""
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2
