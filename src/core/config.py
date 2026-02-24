"""Configuration management for Stamp Collection Toolset.

Uses Pydantic Settings to load configuration from environment files:
- .env.app: Application defaults (committed)
- .env.keys: API keys and secrets (gitignored)
- .env.local: User-specific overrides (gitignored)
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment files."""

    model_config = SettingsConfigDict(
        env_file=(".env.app", ".env.keys", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )

    # ==========================================================================
    # Database Settings
    # ==========================================================================
    DATABASE_PATH: str = Field(
        default="data/stamps.db",
        description="Path to SQLite database file",
    )

    # ==========================================================================
    # Scraping Settings
    # ==========================================================================
    SCRAPE_DELAY_SECONDS: float = Field(
        default=1.5,
        description="Delay between scraping requests (polite crawling)",
    )
    SCRAPE_RETRY_COUNT: int = Field(
        default=3,
        description="Number of retry attempts for failed scrapes",
    )
    SCRAPE_ERROR_BEHAVIOR: str = Field(
        default="skip",
        description="Error behavior: 'skip' to continue, 'abort' to stop",
    )
    SCRAPE_CHECKPOINT_FILE: str = Field(
        default="data/scrape_checkpoint.json",
        description="Path to checkpoint file for resuming scrapes",
    )

    # Browser settings for Playwright
    BROWSER_HEADLESS: bool = Field(
        default=True,
        description="Run browser in headless mode",
    )
    BROWSER_TIMEOUT: int = Field(
        default=60000,
        description="Browser timeout in milliseconds",
    )

    # ==========================================================================
    # RAG Settings
    # ==========================================================================
    RAG_MATCH_AUTO_THRESHOLD: float = Field(
        default=0.9,
        description="Similarity score threshold for auto-accepting matches (0-1)",
    )
    RAG_MATCH_MIN_THRESHOLD: float = Field(
        default=0.5,
        description="Minimum similarity score to consider a match (0-1)",
    )
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model name",
    )
    EMBEDDING_DIMENSIONS: int = Field(
        default=1536,
        description="Embedding vector dimensions",
    )

    # ==========================================================================
    # Vision Settings (Groq)
    # ==========================================================================
    GROQ_MODEL: str = Field(
        default="llama-3.2-11b-vision-preview",
        description="Groq vision model for stamp descriptions",
    )
    GROQ_RATE_LIMIT_PER_MINUTE: int = Field(
        default=30,
        description="Groq API rate limit (requests per minute)",
    )
    VISION_PROMPT_FILE: str = Field(
        default="config/llava_prompt.txt",
        description="Path to vision prompt template file",
    )

    # ==========================================================================
    # Object Detection Settings (YOLO)
    # ==========================================================================
    YOLO_MODEL_PATH: str = Field(
        default="models/yolov8n.pt",
        description="Path to YOLOv8 model weights",
    )
    YOLO_CONFIDENCE_THRESHOLD: float = Field(
        default=0.5,
        description="Minimum confidence for stamp detection (0-1)",
    )

    # ==========================================================================
    # Camera Settings
    # ==========================================================================
    CAMERA_INDEX: int = Field(
        default=0,
        description="Camera device index for OpenCV",
    )

    # ==========================================================================
    # Browser Automation Settings (CDP)
    # ==========================================================================
    CHROME_CDP_URL: str = Field(
        default="http://localhost:9222",
        description="Chrome DevTools Protocol URL for browser automation",
    )

    # ==========================================================================
    # Colnect Settings
    # ==========================================================================
    COLNECT_BASE_URL: str = Field(
        default="https://colnect.com",
        description="Colnect base URL",
    )
    DEFAULT_THEMES: str = Field(
        default="Space,Space Traveling,Astronomy,Rockets,Satellites,Scientists",
        description="Default stamp themes to scrape (comma-separated)",
    )

    # ==========================================================================
    # API Keys (from .env.keys)
    # ==========================================================================
    SUPABASE_URL: Optional[str] = Field(
        default=None,
        description="Supabase project URL",
    )
    SUPABASE_KEY: Optional[str] = Field(
        default=None,
        description="Supabase service role key",
    )
    OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        description="OpenAI API key for embeddings",
    )
    GROQ_API_KEY: Optional[str] = Field(
        default=None,
        description="Groq API key for vision",
    )

    # ==========================================================================
    # Logging Settings
    # ==========================================================================
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    LOG_FORMAT: str = Field(
        default="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        description="Log message format",
    )
    LOG_DIR: str = Field(
        default="data/logs",
        description="Directory for log files",
    )
    LOG_MAX_SIZE_MB: int = Field(
        default=10,
        description="Maximum log file size in MB before rotation",
    )
    LOG_BACKUP_COUNT: int = Field(
        default=3,
        description="Number of backup log files to keep",
    )
    LOG_FILE_NAME: str = Field(
        default="stamp-tools.log",
        description="Main application log filename",
    )
    LOG_ERROR_FILE_NAME: str = Field(
        default="errors.log",
        description="Error log filename",
    )

    # ==========================================================================
    # Computed Properties
    # ==========================================================================
    @computed_field
    @property
    def database_path(self) -> Path:
        """Full path to SQLite database."""
        return Path(self.DATABASE_PATH)

    @computed_field
    @property
    def log_path(self) -> Path:
        """Full path to log directory."""
        return Path(self.LOG_DIR)

    @computed_field
    @property
    def yolo_model_path(self) -> Path:
        """Full path to YOLO model."""
        return Path(self.YOLO_MODEL_PATH)

    @computed_field
    @property
    def vision_prompt_path(self) -> Path:
        """Full path to vision prompt template."""
        return Path(self.VISION_PROMPT_FILE)

    @computed_field
    @property
    def themes_list(self) -> list[str]:
        """Default themes as a list."""
        return [t.strip() for t in self.DEFAULT_THEMES.split(",")]

    def validate_api_keys(self) -> dict[str, bool]:
        """Check which API keys are configured."""
        return {
            "supabase": bool(self.SUPABASE_URL and self.SUPABASE_KEY),
            "openai": bool(self.OPENAI_API_KEY),
            "groq": bool(self.GROQ_API_KEY),
        }


# Singleton pattern for settings
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset settings singleton (useful for testing)."""
    global _settings
    _settings = None
