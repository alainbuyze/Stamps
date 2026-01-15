"""Tests for markdown generator."""

import pytest

from src.generator import generate_guide, html_to_markdown
from src.sources.base import ExtractedContent


def test_html_to_markdown_basic():
    """Test basic HTML to Markdown conversion."""
    html = "<p>Hello <strong>world</strong></p>"
    md = html_to_markdown(html)

    assert "Hello" in md
    assert "**world**" in md


def test_html_to_markdown_images():
    """Test image conversion preserves URLs."""
    html = '<img src="https://example.com/img.png" alt="Test image" />'
    md = html_to_markdown(html)

    assert "![Test image](https://example.com/img.png)" in md


def test_generate_guide_basic():
    """Test basic guide generation."""
    content = ExtractedContent(
        title="Test Guide",
        sections=[
            {
                "heading": "Introduction",
                "level": 2,
                "content": [],
            }
        ],
        images=[],
        metadata={},
    )

    guide = generate_guide(content)

    assert "# Test Guide" in guide
    assert "## Introduction" in guide


def test_generate_guide_with_metadata():
    """Test guide generation with description."""
    content = ExtractedContent(
        title="Test Guide",
        sections=[],
        images=[],
        metadata={"description": "A test description"},
    )

    guide = generate_guide(content)

    assert "# Test Guide" in guide
    assert "> A test description" in guide
