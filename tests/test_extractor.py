"""Tests for content extractor."""

import pytest

from src.core.errors import ExtractionError
from src.extractor import ContentExtractor


def test_can_extract_elecfreaks():
    """Test that extractor can handle Elecfreaks URLs."""
    extractor = ContentExtractor()

    assert extractor.can_extract("https://wiki.elecfreaks.com/en/page")
    assert not extractor.can_extract("https://example.com/page")


def test_extract_raises_for_unknown_url():
    """Test that extraction fails for unsupported URLs."""
    extractor = ContentExtractor()

    with pytest.raises(ExtractionError) as exc_info:
        extractor.extract("<html></html>", "https://unknown-site.com/page")

    assert "No adapter" in str(exc_info.value)


def test_extract_basic_content():
    """Test basic content extraction."""
    extractor = ContentExtractor()

    html = """
    <html>
    <body>
    <article>
        <h1>Test Title</h1>
        <p>Test paragraph content.</p>
    </article>
    </body>
    </html>
    """

    content = extractor.extract(html, "https://wiki.elecfreaks.com/test")

    assert content.title == "Test Title"
