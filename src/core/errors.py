"""Custom exceptions for the Stamp Collection Toolset.

Exception Hierarchy:
    StampToolsError (base)
    ├── ConfigurationError
    ├── DatabaseError
    │   ├── RecordNotFoundError
    │   └── DuplicateRecordError
    ├── ScrapingError
    │   ├── PageNotFoundError
    │   ├── PageTimeoutError
    │   └── ExtractionError
    ├── RAGError
    │   ├── EmbeddingError
    │   ├── SupabaseError
    │   └── SearchError
    ├── VisionError
    │   ├── GroqAPIError
    │   └── DescriptionError
    ├── IdentificationError
    │   ├── CameraError
    │   └── DetectionError
    ├── MigrationError
    │   ├── MatchingError
    │   └── ImportError
    └── BrowserAutomationError
        ├── CDPConnectionError
        └── ColnectActionError
"""


class StampToolsError(Exception):
    """Base exception for all Stamp Collection Toolset errors."""

    pass


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(StampToolsError):
    """Invalid or missing configuration."""

    pass


# =============================================================================
# Database Errors
# =============================================================================


class DatabaseError(StampToolsError):
    """Base exception for database operations."""

    pass


class RecordNotFoundError(DatabaseError):
    """Requested record does not exist."""

    pass


class DuplicateRecordError(DatabaseError):
    """Record with same key already exists."""

    pass


# =============================================================================
# Scraping Errors
# =============================================================================


class ScrapingError(StampToolsError):
    """Base exception for web scraping errors."""

    pass


class PageNotFoundError(ScrapingError):
    """Page URL returned 404."""

    pass


class PageTimeoutError(ScrapingError):
    """Page loading timed out."""

    pass


class ExtractionError(ScrapingError):
    """Failed to extract content from page."""

    pass


# =============================================================================
# RAG Errors
# =============================================================================


class RAGError(StampToolsError):
    """Base exception for RAG operations."""

    pass


class EmbeddingError(RAGError):
    """Failed to generate embedding."""

    pass


class SupabaseError(RAGError):
    """Supabase operation failed."""

    pass


class SearchError(RAGError):
    """Similarity search failed."""

    pass


# =============================================================================
# Vision Errors
# =============================================================================


class VisionError(StampToolsError):
    """Base exception for vision/description operations."""

    pass


class GroqAPIError(VisionError):
    """Groq API call failed."""

    pass


class DescriptionError(VisionError):
    """Failed to generate stamp description."""

    pass


# =============================================================================
# Identification Errors
# =============================================================================


class IdentificationError(StampToolsError):
    """Base exception for stamp identification."""

    pass


class CameraError(IdentificationError):
    """Camera capture failed."""

    pass


class DetectionError(IdentificationError):
    """YOLO stamp detection failed."""

    pass


# =============================================================================
# Migration Errors
# =============================================================================


class MigrationError(StampToolsError):
    """Base exception for LASTDODO migration."""

    pass


class MatchingError(MigrationError):
    """Failed to match stamp to catalog."""

    pass


class ImportTaskError(MigrationError):
    """Failed to import stamp to Colnect."""

    pass


# =============================================================================
# Browser Automation Errors
# =============================================================================


class BrowserAutomationError(StampToolsError):
    """Base exception for browser automation."""

    pass


class CDPConnectionError(BrowserAutomationError):
    """Failed to connect to Chrome via CDP."""

    pass


class ColnectActionError(BrowserAutomationError):
    """Colnect browser action failed."""

    pass
