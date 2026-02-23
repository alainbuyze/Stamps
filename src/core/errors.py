"""Custom exceptions for the Stamp Guide Generator."""


class ScrapingError(Exception):
    """Base exception for scraping errors."""

    pass


class PageNotFoundError(ScrapingError):
    """Page URL returned 404."""

    pass


class PageTimeoutError(ScrapingError):
    """Page loading timed out."""

    pass


class ExtractionError(Exception):
    """Failed to extract content from page."""

    pass


class GenerationError(Exception):
    """Failed to generate markdown output."""

    pass


class DownloadError(Exception):
    """Failed to download image."""

    pass


class EnhancementError(Exception):
    """Failed to enhance image with Upscayl."""

    pass


class TranslationError(Exception):
    """Failed to translate content."""

    pass
