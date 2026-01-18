"""PDF printer for converting markdown guides to printable PDFs.

Uses xhtml2pdf for HTML to PDF conversion - a pure Python solution
that works reliably on Windows without external dependencies.
"""

import inspect
import logging
import re
from io import BytesIO
from pathlib import Path

from markdown import markdown
from xhtml2pdf import pisa

from src.core.config import get_settings
from src.core.errors import GenerationError

settings = get_settings()
logger = logging.getLogger(__name__)


def detect_image_sections(md_content: str) -> dict[str, list[str]]:
    """Detect different types of image sections in markdown content.

    Analyzes headings and image patterns to categorize images for optimal layout.

    Args:
        md_content: Markdown content to analyze.

    Returns:
        Dict mapping section types to lists of image references.
        Section types: 'construction', 'connection', 'code', 'other'
    """
    sections = {
        "construction": [],
        "connection": [],
        "code": [],
        "other": [],
    }

    # Split by headings
    heading_pattern = r"^(#{2,3})\s+(.+)$"
    current_section = None
    current_type = "other"

    for line in md_content.split("\n"):
        # Check for heading
        heading_match = re.match(heading_pattern, line)
        if heading_match:
            heading_text = heading_match.group(2).lower()
            current_section = heading_text

            # Categorize section
            if any(
                keyword in heading_text
                for keyword in ["assembly", "bouw", "construction", "stap", "step"]
            ):
                current_type = "construction"
            elif any(
                keyword in heading_text
                for keyword in ["connection", "wiring", "aansluiting", "bedrading"]
            ):
                current_type = "connection"
            elif any(keyword in heading_text for keyword in ["code", "program", "software"]):
                current_type = "code"
            else:
                current_type = "other"

        # Check for image
        img_match = re.search(r"!\[([^\]]*)\]\(([^)]+)\)", line)
        if img_match and current_section:
            img_path = img_match.group(2)
            sections[current_type].append(img_path)

    return sections


def enhance_markdown_for_print(md_content: str) -> str:
    """Enhance markdown with CSS classes for print layout optimization.

    Args:
        md_content: Original markdown content.

    Returns:
        Enhanced markdown with HTML classes for layout control.
    """
    lines = []
    current_section = None
    section_type = "other"
    in_construction = False
    step_counter = 0

    heading_pattern = r"^(#{2,3})\s+(.+)$"
    img_pattern = r"(!\[([^\]]*)\]\(([^)]+)\))"

    for line in md_content.split("\n"):
        # Check for heading
        heading_match = re.match(heading_pattern, line)
        if heading_match:
            heading_text = heading_match.group(2).lower()
            current_section = heading_text

            # Reset step counter for new sections
            step_counter = 0

            # Categorize section
            if any(
                keyword in heading_text
                for keyword in ["assembly", "bouw", "construction", "stap", "step"]
            ):
                section_type = "construction"
                in_construction = True
            elif any(
                keyword in heading_text
                for keyword in ["connection", "wiring", "aansluiting", "bedrading"]
            ):
                section_type = "connection"
                in_construction = False
            elif any(keyword in heading_text for keyword in ["code", "program", "software"]):
                section_type = "code"
                in_construction = False
            else:
                section_type = "other"
                in_construction = False

            lines.append(line)
            continue

        # Check for image
        img_match = re.search(img_pattern, line)
        if img_match:
            # Wrap images with appropriate div classes
            if section_type == "construction":
                step_counter += 1
                # Wrap in construction-step div
                lines.append(f'<div class="construction-step" data-step="{step_counter}">')
                lines.append(line)
                lines.append("</div>")
            elif section_type == "connection":
                # Full-page connection diagrams
                lines.append('<div class="connection-diagram">')
                lines.append(line)
                lines.append("</div>")
            elif section_type == "code":
                # Code screenshots
                lines.append('<div class="code-image">')
                lines.append(line)
                lines.append("</div>")
            else:
                lines.append(line)
        else:
            lines.append(line)

    return "\n".join(lines)


def markdown_to_html(md_content: str, css_path: Path | None = None) -> str:
    """Convert markdown to HTML with print-optimized structure.

    Args:
        md_content: Markdown content to convert.
        css_path: Optional path to custom CSS file.

    Returns:
        Complete HTML document ready for PDF conversion.
    """
    # Enhance markdown with print classes
    enhanced_md = enhance_markdown_for_print(md_content)

    # Convert to HTML
    html_body = markdown(
        enhanced_md,
        extensions=[
            "tables",
            "fenced_code",
            "codehilite",
            "nl2br",  # Preserve line breaks
        ],
    )

    # Load CSS
    css_content = ""
    if css_path and css_path.exists():
        css_content = css_path.read_text(encoding="utf-8")
    else:
        # Use default embedded CSS
        css_content = get_default_css()

    # Build complete HTML document
    html_doc = f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CoderDojo Guide</title>
    <style>
{css_content}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

    return html_doc


def get_default_css() -> str:
    """Get default CSS for print layout.

    Returns:
        CSS string with A4 portrait layout rules.
        Note: xhtml2pdf supports a subset of CSS 2.1
    """
    return """
/* A4 Portrait page setup - xhtml2pdf syntax */
@page {
    size: A4 portrait;
    margin: 15mm 20mm;
}

/* General typography */
body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.4;
    color: #333333;
}

/* Title page */
h1 {
    font-size: 28pt;
    font-weight: bold;
    text-align: center;
    page-break-after: always;
    margin-top: 50mm;
    color: #2c3e50;
}

/* Section headers */
h2 {
    font-size: 18pt;
    font-weight: bold;
    page-break-before: always;
    page-break-after: avoid;
    margin-top: 0;
    margin-bottom: 8mm;
    color: #2c3e50;
    border-bottom: 2pt solid #3498db;
    padding-bottom: 2mm;
}

h3 {
    font-size: 14pt;
    font-weight: bold;
    page-break-after: avoid;
    margin-top: 5mm;
    margin-bottom: 3mm;
    color: #34495e;
}

/* Paragraphs */
p {
    margin-bottom: 3mm;
    text-align: justify;
}

/* Lists */
ul, ol {
    margin-bottom: 3mm;
    padding-left: 8mm;
}

li {
    margin-bottom: 2mm;
}

/* Code blocks */
pre {
    background-color: #f5f5f5;
    border: 1pt solid #dddddd;
    border-left: 3pt solid #3498db;
    padding: 3mm;
    font-family: Courier, monospace;
    font-size: 9pt;
    page-break-inside: avoid;
    margin: 3mm 0;
}

code {
    font-family: Courier, monospace;
    font-size: 10pt;
    background-color: #f5f5f5;
    padding: 1mm 2mm;
}

pre code {
    background-color: transparent;
    padding: 0;
}

/* Images - default */
img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 3mm auto;
}

/* Construction diagrams */
.construction-step {
    width: 100%;
    page-break-inside: avoid;
    margin-bottom: 8mm;
    border: 1pt solid #ecf0f1;
    padding: 3mm;
    background-color: #fafafa;
}

.construction-step img {
    max-width: 100%;
    max-height: 110mm;
    display: block;
    margin: 0 auto;
}

/* Connection diagrams: full page */
.connection-diagram {
    page-break-before: always;
    page-break-after: always;
    page-break-inside: avoid;
    text-align: center;
}

.connection-diagram img {
    max-width: 100%;
    max-height: 250mm;
    display: block;
    margin: 0 auto;
}

/* Code screenshots */
.code-image {
    page-break-inside: avoid;
    margin: 5mm 0;
    text-align: center;
}

.code-image img {
    max-width: 100%;
    max-height: 180mm;
    display: block;
    margin: 0 auto;
    border: 1pt solid #dddddd;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 3mm 0;
    page-break-inside: avoid;
    font-size: 10pt;
}

th, td {
    border: 1pt solid #dddddd;
    padding: 2mm;
    text-align: left;
}

th {
    background-color: #3498db;
    color: white;
    font-weight: bold;
}

/* Blockquotes */
blockquote {
    border-left: 3pt solid #3498db;
    padding-left: 5mm;
    margin: 3mm 0;
    color: #555555;
    font-style: italic;
}

/* Links */
a {
    color: #3498db;
    text-decoration: none;
}

/* Prevent page breaks in bad places */
h1, h2, h3, h4, h5, h6 {
    page-break-after: avoid;
}
"""


def link_callback(uri: str, rel: str) -> str:
    """Callback for xhtml2pdf to resolve resource URIs.

    Args:
        uri: The URI to resolve (image path, etc.)
        rel: Relative path (unused)

    Returns:
        Resolved path to the resource.
    """
    # Handle file:// URIs
    if uri.startswith("file://"):
        # Convert file:// URI to local path
        if uri.startswith("file:///"):
            # Windows absolute path: file:///C:/path
            return uri[8:]  # Remove 'file:///'
        return uri[7:]  # Remove 'file://'

    # Handle absolute paths
    if Path(uri).is_absolute():
        return uri

    # Return as-is for relative paths (xhtml2pdf will resolve)
    return uri


def markdown_to_pdf(
    md_content: str,
    output_path: Path,
    css_path: Path | None = None,
    base_url: str | None = None,
) -> Path:
    """Convert markdown content to PDF with print-optimized layout.

    Args:
        md_content: Markdown content to convert.
        output_path: Path where PDF should be saved.
        css_path: Optional path to custom CSS file.
        base_url: Optional base URL for resolving relative image paths.

    Returns:
        Path to the generated PDF file.

    Raises:
        GenerationError: If PDF generation fails.
    """
    logger.debug(
        f" * {inspect.currentframe().f_code.co_name} > Converting markdown to PDF: {output_path}"
    )

    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert markdown to HTML
        html_content = markdown_to_html(md_content, css_path)
        logger.debug(f"    -> Generated {len(html_content)} bytes of HTML")

        # Generate PDF using xhtml2pdf
        with open(output_path, "wb") as pdf_file:
            # Create PDF
            pisa_status = pisa.CreatePDF(
                src=html_content,
                dest=pdf_file,
                encoding="utf-8",
                link_callback=link_callback,
            )

            if pisa_status.err:
                raise GenerationError(f"xhtml2pdf reported {pisa_status.err} errors")

        logger.debug(f"    -> PDF saved: {output_path}")
        return output_path

    except Exception as e:
        error_context = {
            "output_path": str(output_path),
            "error_type": type(e).__name__,
        }
        logger.error(f"PDF generation failed: {e} | Context: {error_context}")
        raise GenerationError(f"Failed to generate PDF: {e}") from e


def markdown_file_to_pdf(
    md_path: Path,
    output_path: Path | None = None,
    css_path: Path | None = None,
) -> Path:
    """Convert a markdown file to PDF.

    Args:
        md_path: Path to markdown file.
        output_path: Optional output PDF path (defaults to same name with .pdf extension).
        css_path: Optional path to custom CSS file.

    Returns:
        Path to the generated PDF file.

    Raises:
        GenerationError: If file reading or PDF generation fails.
    """
    logger.debug(f" * {inspect.currentframe().f_code.co_name} > Processing file: {md_path}")

    try:
        # Read markdown file
        if not md_path.exists():
            raise GenerationError(f"Markdown file not found: {md_path}")

        md_content = md_path.read_text(encoding="utf-8")
        logger.debug(f"    -> Read {len(md_content)} bytes")

        # Determine output path
        if output_path is None:
            output_path = md_path.with_suffix(".pdf")

        # Get base URL for resolving relative image paths
        # Use the markdown file's directory as base
        base_url = md_path.parent.as_uri()

        # Convert to PDF
        return markdown_to_pdf(md_content, output_path, css_path, base_url)

    except Exception as e:
        error_context = {
            "md_path": str(md_path),
            "error_type": type(e).__name__,
        }
        logger.error(f"Markdown file conversion failed: {e} | Context: {error_context}")
        raise GenerationError(f"Failed to convert markdown file: {e}") from e
