"""Base source adapter interface for content extraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from bs4 import BeautifulSoup


@dataclass
class ExtractedContent:
    """Container for extracted tutorial content."""

    title: str
    sections: list[dict[str, Any]] = field(default_factory=list)
    images: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseSourceAdapter(ABC):
    """Abstract base class for source-specific content extraction."""

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if this adapter can handle the given URL.

        Args:
            url: The URL to check.

        Returns:
            True if this adapter can extract content from the URL.
        """
        pass

    @abstractmethod
    def extract(self, soup: BeautifulSoup, url: str) -> ExtractedContent:
        """Extract content from parsed HTML.

        Args:
            soup: Parsed HTML as BeautifulSoup object.
            url: The source URL for context.

        Returns:
            ExtractedContent with title, sections, images, and metadata.
        """
        pass
