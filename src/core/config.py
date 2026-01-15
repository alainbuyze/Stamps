"""Configuration management using Pydantic Settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment files."""

    model_config = SettingsConfigDict(
        env_file=(".env.app", ".env.keys", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )

    # Output settings
    OUTPUT_DIR: str = Field(default="./output", description="Output directory for generated guides")
    CACHE_DIR: str = Field(default="./cache", description="Cache directory for downloaded pages")

    # Scraping settings
    RATE_LIMIT_SECONDS: float = Field(default=2.0, description="Delay between requests")
    BROWSER_HEADLESS: bool = Field(default=True, description="Run browser in headless mode")
    BROWSER_TIMEOUT: int = Field(default=30000, description="Browser timeout in milliseconds")

    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format",
    )


# Singleton pattern for settings
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
