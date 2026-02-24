"""Core module - configuration, logging, database, and error handling."""

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
