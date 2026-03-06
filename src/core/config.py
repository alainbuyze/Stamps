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
    # Output Root Directory
    # ==========================================================================
    OUTPUT_ROOT_DIR: str = Field(
        default="data",
        description="Root directory for ALL execution output (database, logs, inspection, etc.)",
    )

    # ==========================================================================
    # Database Settings
    # ==========================================================================
    DATABASE_PATH: str = Field(
        default="stamps.db",
        description="Database filename (relative to OUTPUT_ROOT_DIR)",
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
        default="scrape_checkpoint.json",
        description="Checkpoint filename (relative to OUTPUT_ROOT_DIR)",
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
    YOLO_AUTO_DOWNLOAD: bool = Field(
        default=True,
        description="Auto-download YOLO model if not found",
    )

    # ==========================================================================
    # Vision LLM Detection Settings
    # ==========================================================================
    DETECTION_PRIMARY_PROVIDER: str = Field(
        default="roboflow",
        description="Primary detection provider: roboflow | roboflow_local | groq | claude_haiku | claude_sonnet",
    )
    DETECTION_FALLBACK_PROVIDER: str = Field(
        default="groq",
        description="Fallback detection provider: groq | claude_haiku | claude_sonnet",
    )
    DETECTION_ENABLE_FALLBACK: bool = Field(
        default=True,
        description="Enable fallback to secondary provider on failure",
    )
    DETECTION_MIN_DETECTIONS: int = Field(
        default=1,
        description="Minimum detections before triggering fallback",
    )
    DETECTION_FALLBACK_ON_PARSE_ERROR: bool = Field(
        default=True,
        description="Trigger fallback on JSON parse error",
    )
    DETECTION_FALLBACK_ON_API_ERROR: bool = Field(
        default=True,
        description="Trigger fallback on API error",
    )
    DETECTION_NMS_ENABLED: bool = Field(
        default=True,
        description="Enable Non-Maximum Suppression to filter duplicate detections",
    )
    DETECTION_NMS_IOU_THRESHOLD: float = Field(
        default=0.3,
        description="IoU threshold for NMS - boxes with IoU above this are merged (0.0-1.0)",
    )
    DETECTION_GROQ_TEMPERATURE: float = Field(
        default=0.1,
        description="Temperature for Groq detection calls",
    )
    DETECTION_GROQ_MAX_TOKENS: int = Field(
        default=1500,
        description="Max tokens for Groq detection response",
    )
    DETECTION_CLAUDE_MODEL_HAIKU: str = Field(
        default="claude-3-haiku-20240307",
        description="Claude Haiku model for detection",
    )
    DETECTION_CLAUDE_MODEL_SONNET: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Claude Sonnet model for detection",
    )
    DETECTION_CLAUDE_TEMPERATURE: float = Field(
        default=0.1,
        description="Temperature for Claude detection calls",
    )
    DETECTION_CLAUDE_MAX_TOKENS: int = Field(
        default=1500,
        description="Max tokens for Claude detection response",
    )


    # ==========================================================================
    # Roboflow Stamp Detector Settings
    # ==========================================================================
    ROBOFLOW_API_KEY: Optional[str] = Field(
        default=None,
        description='Roboflow API key — set in .env.keys',
    )
    ROBOFLOW_WORKSPACE: str = Field(
        default='',
        description='Roboflow workspace slug (visible in your project URL)',
    )
    ROBOFLOW_PROJECT: str = Field(
        default='stamp-detector',
        description='Roboflow project name',
    )
    ROBOFLOW_VERSION: int = Field(
        default=1,
        description='Roboflow model version to use/download',
    )
    ROBOFLOW_MODEL_PATH: str = Field(
        default='models/roboflow_stamp_detector.pt',
        description='Local path where downloaded .pt weights are cached',
    )
    ROBOFLOW_CONFIDENCE_THRESHOLD: float = Field(
        default=0.35,
        description='Minimum detection confidence for Roboflow model (0-1)',
    )

        # ==========================================================================
    # Preprocessing Settings
    # ==========================================================================
    PREPROCESSING_STRATEGY: str = Field(
        default="compress",
        description="Preprocessing strategy: original | downscale | compress | posterize | high_contrast | edge_enhanced | minimal",
    )
    PREPROCESSING_MAX_DIM: int = Field(
        default=640,
        description="Maximum dimension (width or height) for preprocessing",
    )
    PREPROCESSING_JPEG_QUALITY: int = Field(
        default=85,
        description="JPEG compression quality (0-100)",
    )
    PREPROCESSING_COLOR_LEVELS: int = Field(
        default=8,
        description="Color levels per channel for posterization (2-256)",
    )
    PREPROCESSING_CLAHE_CLIP_LIMIT: float = Field(
        default=2.0,
        description="CLAHE clip limit for contrast enhancement",
    )
    PREPROCESSING_CLAHE_GRID_SIZE: int = Field(
        default=8,
        description="CLAHE grid size for contrast enhancement",
    )
    PREPROCESSING_EDGE_WEIGHT: float = Field(
        default=0.3,
        description="Edge blend weight for edge_enhanced strategy",
    )

    # ==========================================================================
    # Identification Pipeline Settings
    # ==========================================================================
    IDENTIFICATION_DEFAULT_MODE: str = Field(
        default="auto",
        description="Default identification mode: auto | single | multi",
    )
    IDENTIFICATION_CROP_PADDING_PERCENT: float = Field(
        default=0.02,
        description="Padding around stamp crops as percentage (0.02 = 2%)",
    )
    IDENTIFICATION_MAX_MATCHES: int = Field(
        default=5,
        description="Maximum number of RAG matches to return per stamp",
    )
    IDENTIFICATION_DESCRIPTION_PROVIDER: str = Field(
        default="groq",
        description="Provider for stamp description generation: groq | openai",
    )

    # ==========================================================================
    # Inspection Settings
    # ==========================================================================
    INSPECTION_DIR: str = Field(
        default="inspection",
        description="Inspection subdirectory (relative to OUTPUT_ROOT_DIR)",
    )
    INSPECTION_SAVE_INTERMEDIATES: bool = Field(
        default=True,
        description="Save all intermediate images for debugging",
    )

    # ==========================================================================
    # Stamp Classifier Settings
    # ==========================================================================
    CLASSIFIER_MODE: str = Field(
        default="heuristic",
        description="Classifier mode: heuristic | model | both",
    )
    CLASSIFIER_CONFIDENCE_THRESHOLD: float = Field(
        default=0.6,
        description="Minimum confidence to accept as stamp (0-1)",
    )
    CLASSIFIER_COLOR_VARIANCE_WEIGHT: float = Field(
        default=0.35,
        description="Weight for color variance heuristic",
    )
    CLASSIFIER_EDGE_COMPLEXITY_WEIGHT: float = Field(
        default=0.30,
        description="Weight for edge complexity heuristic",
    )
    CLASSIFIER_SIZE_WEIGHT: float = Field(
        default=0.20,
        description="Weight for size plausibility heuristic",
    )
    CLASSIFIER_PERFORATION_WEIGHT: float = Field(
        default=0.15,
        description="Weight for perforation hint heuristic",
    )
    CLASSIFIER_MODEL_PATH: Optional[str] = Field(
        default=None,
        description="Path to trained classifier model (optional)",
    )

    # ==========================================================================
    # Feedback System Settings
    # ==========================================================================
    FEEDBACK_OUTPUT_DIR: str = Field(
        default="feedback",
        description="Feedback subdirectory (relative to OUTPUT_ROOT_DIR)",
    )
    FEEDBACK_SAVE_ORIGINAL: bool = Field(
        default=True,
        description="Save original captured image",
    )
    FEEDBACK_SAVE_ANNOTATED: bool = Field(
        default=True,
        description="Save annotated image with overlays",
    )
    FEEDBACK_SAVE_CROPS: bool = Field(
        default=True,
        description="Save individual stamp crops",
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
    ANTHROPIC_API_KEY: Optional[str] = Field(
        default=None,
        description="Anthropic API key for Claude fallback",
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
        default="logs",
        description="Logs subdirectory (relative to OUTPUT_ROOT_DIR)",
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
    # Computed Properties (combine OUTPUT_ROOT_DIR with relative paths)
    # ==========================================================================
    @computed_field
    @property
    def output_root_path(self) -> Path:
        """Full path to output root directory."""
        return Path(self.OUTPUT_ROOT_DIR)

    @computed_field
    @property
    def database_path(self) -> Path:
        """Full path to SQLite database."""
        return Path(self.OUTPUT_ROOT_DIR) / self.DATABASE_PATH

    @computed_field
    @property
    def log_path(self) -> Path:
        """Full path to log directory."""
        return Path(self.OUTPUT_ROOT_DIR) / self.LOG_DIR

    @computed_field
    @property
    def inspection_path(self) -> Path:
        """Full path to inspection directory."""
        return Path(self.OUTPUT_ROOT_DIR) / self.INSPECTION_DIR

    @computed_field
    @property
    def feedback_output_path(self) -> Path:
        """Full path to feedback output directory."""
        return Path(self.OUTPUT_ROOT_DIR) / self.FEEDBACK_OUTPUT_DIR

    @computed_field
    @property
    def checkpoint_path(self) -> Path:
        """Full path to scrape checkpoint file."""
        return Path(self.OUTPUT_ROOT_DIR) / self.SCRAPE_CHECKPOINT_FILE

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
            "anthropic": bool(self.ANTHROPIC_API_KEY),
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
