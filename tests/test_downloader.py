"""Tests for image downloader."""

import pytest

from src.downloader import generate_filename, slugify
from src.sources.base import ExtractedContent


def test_slugify_basic():
    """Test basic text slugification."""
    assert slugify("Hello World") == "hello_world"
    assert slugify("Test-String") == "test_string"
    assert slugify("  spaces  ") == "spaces"


def test_slugify_special_chars():
    """Test slugification removes special characters."""
    assert slugify("Hello! World?") == "hello_world"
    assert slugify("test@example.com") == "testexamplecom"
    assert slugify("file (1).png") == "file_1png"


def test_slugify_unicode():
    """Test slugification handles unicode."""
    # Unicode characters should be removed
    assert slugify("café") == "caf"
    assert slugify("日本語") == ""


def test_generate_filename_with_alt():
    """Test filename generation with alt text."""
    filename = generate_filename(
        "https://example.com/image.png",
        "Test Image Alt Text",
        0,
    )
    assert filename == "test_image_alt_text.png"


def test_generate_filename_fallback_to_index():
    """Test filename generation falls back to index."""
    # Empty alt text
    filename = generate_filename(
        "https://example.com/image.jpg",
        "",
        5,
    )
    assert filename == "image_005.jpg"

    # Short alt text
    filename = generate_filename(
        "https://example.com/image.png",
        "ab",
        3,
    )
    assert filename == "image_003.png"


def test_generate_filename_preserves_extension():
    """Test filename generation preserves original extension."""
    filename = generate_filename(
        "https://example.com/path/to/image.gif",
        "test",
        0,
    )
    assert filename.endswith(".gif")


def test_generate_filename_default_extension():
    """Test filename generation uses .png as default."""
    filename = generate_filename(
        "https://example.com/image",  # No extension
        "test",
        0,
    )
    assert filename.endswith(".png")


def test_generate_filename_long_alt_truncated():
    """Test filename generation truncates long alt text."""
    long_alt = "A" * 100
    filename = generate_filename(
        "https://example.com/image.png",
        long_alt,
        0,
    )
    # Should be truncated to 50 chars max plus extension
    assert len(filename) <= 54  # 50 + ".png"


def test_extracted_content_image_dict():
    """Test ExtractedContent handles image dicts correctly."""
    content = ExtractedContent(
        title="Test",
        sections=[],
        images=[
            {"src": "https://example.com/img1.png", "alt": "Image 1"},
            {"src": "https://example.com/img2.png", "alt": "Image 2"},
        ],
        metadata={},
    )

    assert len(content.images) == 2
    assert content.images[0]["src"] == "https://example.com/img1.png"


def test_extracted_content_with_local_path():
    """Test ExtractedContent can store local_path."""
    content = ExtractedContent(
        title="Test",
        sections=[],
        images=[
            {
                "src": "https://example.com/img1.png",
                "alt": "Image 1",
                "local_path": "images/image_1.png",
            },
        ],
        metadata={},
    )

    assert content.images[0].get("local_path") == "images/image_1.png"


def test_extracted_content_with_enhanced_path():
    """Test ExtractedContent can store enhanced_path."""
    content = ExtractedContent(
        title="Test",
        sections=[],
        images=[
            {
                "src": "https://example.com/img1.png",
                "alt": "Image 1",
                "local_path": "images/image_1.png",
                "enhanced_path": "images/image_1_enhanced.png",
            },
        ],
        metadata={},
    )

    assert content.images[0].get("enhanced_path") == "images/image_1_enhanced.png"
