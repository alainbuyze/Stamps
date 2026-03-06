"""Core infrastructure module for the Stamp Collection Toolset.

This module provides the foundational components used across all other packages:

Modules
-------
config.py
    Pydantic Settings-based configuration management. Loads settings from
    .env.app (defaults), .env.keys (secrets), and .env.local (overrides).
    Provides computed paths relative to OUTPUT_ROOT_DIR.

database.py
    SQLite database operations with dataclass models. Defines CatalogStamp
    (Colnect scraped data), LastdodoItem (LASTDODO collection), and ImportTask
    (migration tracking). Provides CRUD operations and statistics queries.

errors.py
    Custom exception hierarchy rooted at StampToolsError. Organized by domain:
    scraping (ScrapingError, PageNotFoundError), RAG (EmbeddingError, SearchError),
    vision (VisionError, DetectionError), and migration (MigrationError).

logging.py
    Rich-based logging setup for formatted console output with colors and
    structured log files.

Key Exports
-----------
- Settings, get_settings(): Configuration access
- CatalogStamp, LastdodoItem, ImportTask: Data models
- Database CRUD functions: upsert_*, get_*, count_*
- Exception classes: StampToolsError and subclasses
"""

from src.core.config import Settings, get_settings, reset_settings
from src.core.database import (
    CatalogStamp,
    ImportTask,
    LastdodoItem,
    count_catalog_stamps,
    count_import_tasks,
    count_lastdodo_items,
    create_import_task,
    find_catalog_stamp_by_catalog_code,
    get_catalog_stamp,
    get_catalog_stamps,
    get_connection,
    get_database_stats,
    get_import_task,
    get_import_task_stats,
    get_import_tasks,
    get_lastdodo_item,
    get_lastdodo_items,
    init_database,
    update_import_task,
    upsert_catalog_stamp,
    upsert_lastdodo_item,
)
from src.core.errors import (
    BrowserAutomationError,
    CameraError,
    CDPConnectionError,
    ColnectActionError,
    ConfigurationError,
    DatabaseError,
    DescriptionError,
    DetectionError,
    DuplicateRecordError,
    EmbeddingError,
    ExtractionError,
    GroqAPIError,
    IdentificationError,
    ImportTaskError,
    MatchingError,
    MigrationError,
    PageNotFoundError,
    PageTimeoutError,
    RAGError,
    RecordNotFoundError,
    ScrapingError,
    SearchError,
    StampToolsError,
    SupabaseError,
    VisionError,
)

__all__ = [
    # Config
    "Settings",
    "get_settings",
    "reset_settings",
    # Database - Data classes
    "CatalogStamp",
    "LastdodoItem",
    "ImportTask",
    # Database - Connection
    "get_connection",
    "init_database",
    # Database - Catalog stamps
    "upsert_catalog_stamp",
    "get_catalog_stamp",
    "get_catalog_stamps",
    "count_catalog_stamps",
    "find_catalog_stamp_by_catalog_code",
    # Database - LASTDODO items
    "upsert_lastdodo_item",
    "get_lastdodo_item",
    "get_lastdodo_items",
    "count_lastdodo_items",
    # Database - Import tasks
    "create_import_task",
    "update_import_task",
    "get_import_task",
    "get_import_tasks",
    "count_import_tasks",
    "get_import_task_stats",
    "get_database_stats",
    # Errors - Base
    "StampToolsError",
    "ConfigurationError",
    # Errors - Database
    "DatabaseError",
    "RecordNotFoundError",
    "DuplicateRecordError",
    # Errors - Scraping
    "ScrapingError",
    "PageNotFoundError",
    "PageTimeoutError",
    "ExtractionError",
    # Errors - RAG
    "RAGError",
    "EmbeddingError",
    "SupabaseError",
    "SearchError",
    # Errors - Vision
    "VisionError",
    "GroqAPIError",
    "DescriptionError",
    # Errors - Identification
    "IdentificationError",
    "CameraError",
    "DetectionError",
    # Errors - Migration
    "MigrationError",
    "MatchingError",
    "ImportTaskError",
    # Errors - Browser automation
    "BrowserAutomationError",
    "CDPConnectionError",
    "ColnectActionError",
]
