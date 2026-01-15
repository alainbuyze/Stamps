"""Markdown generator for creating printable guides."""

import inspect
import logging
import re
from pathlib import Path

from bs4 import Tag
from markdownify import MarkdownConverter

from src.core.config import get_settings
from src.core.errors import GenerationError
from src.sources.base import ExtractedContent

settings = get_settings()
logger = logging.getLogger(__name__)


class GuideMarkdownConverter(MarkdownConverter):
    """Custom Markdown converter that preserves image URLs."""

    def convert_img(
        self, el: Tag, text: str = "", convert_as_inline: bool = False, **kwargs
    ) -> str:
        """Convert img tag to markdown, preserving the full URL.

        Args:
            el: The img element.
            text: Text content (usually empty for images).
            convert_as_inline: Whether to convert as inline element.
            **kwargs: Additional arguments passed by markdownify.
        """
        src = el.get("src", "")
        alt = el.get("alt", "")
        title = el.get("title", "")

        if title:
            return f'![{alt}]({src} "{title}")'
        return f"![{alt}]({src})"


def html_to_markdown(html: str | Tag) -> str:
    """Convert HTML to Markdown using custom converter.

    Args:
        html: HTML string or BeautifulSoup Tag.

    Returns:
        Markdown formatted string.
    """
    if isinstance(html, Tag):
        html = str(html)

    converter = GuideMarkdownConverter(
        heading_style="ATX",
        bullets="-",
        code_language="",
        escape_underscores=False,
    )

    md = converter.convert(html)

    # Clean up excessive whitespace
    md = re.sub(r"\n{3,}", "\n\n", md)

    return md.strip()


def generate_guide(content: ExtractedContent) -> str:
    """Generate a Markdown guide from extracted content.

    Args:
        content: Structured content from extraction.

    Returns:
        Markdown formatted guide string.

    Raises:
        GenerationError: If guide generation fails.
    """
    logger.debug(f" * {inspect.currentframe().f_code.co_name} > Generating guide: {content.title}")

    try:
        parts = []

        # Title
        parts.append(f"# {content.title}\n")

        # Metadata section (optional)
        if content.metadata.get("description"):
            parts.append(f"> {content.metadata['description']}\n")

        # Sections
        for section in content.sections:
            heading = section.get("heading", "")
            level = section.get("level", 2)
            section_content = section.get("content", [])

            if heading:
                prefix = "#" * level
                parts.append(f"\n{prefix} {heading}\n")

            # Convert each content element
            for element in section_content:
                if isinstance(element, Tag):
                    md = html_to_markdown(element)
                    if md:
                        parts.append(md + "\n")

        # Combine all parts
        guide = "\n".join(parts)

        # Final cleanup
        guide = re.sub(r"\n{3,}", "\n\n", guide)

        logger.debug(f"    -> Generated {len(guide)} bytes of Markdown")
        return guide

    except Exception as e:
        error_context = {
            "title": content.title,
            "sections": len(content.sections),
            "error_type": type(e).__name__,
        }
        logger.error(f"Generation failed: {e} | Context: {error_context}")
        raise GenerationError(f"Failed to generate guide: {e}") from e


def save_guide(guide: str, output_path: Path) -> Path:
    """Save a guide to a file.

    Args:
        guide: Markdown content to save.
        output_path: Path to save the guide to.

    Returns:
        The path where the guide was saved.

    Raises:
        GenerationError: If saving fails.
    """
    logger.debug(f" * {inspect.currentframe().f_code.co_name} > Saving to: {output_path}")

    try:
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        output_path.write_text(guide, encoding="utf-8")
        logger.debug(f"    -> Saved {len(guide)} bytes")

        return output_path

    except Exception as e:
        error_context = {
            "path": str(output_path),
            "error_type": type(e).__name__,
        }
        logger.error(f"Save failed: {e} | Context: {error_context}")
        raise GenerationError(f"Failed to save guide: {e}") from e
