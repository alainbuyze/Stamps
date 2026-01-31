"""CoderDojo Guide Generator - Markdown generation for printable guides.

This module provides comprehensive functionality for converting extracted web content
into well-structured Markdown documents suitable for printing and PDF generation.
It handles HTML-to-Markdown conversion, image processing, content organization,
and post-processing optimizations.

## Core Features

- **HTML to Markdown Conversion**: Custom converter that preserves image URLs and
  applies section-based CSS classes for targeted styling
- **Image Processing**: Maps remote URLs to local paths, applies scaling, and
  handles image organization by content sections
- **Content Structuring**: Organizes content into hierarchical sections with
  proper heading levels and metadata handling
- **Post-Processing**: Applies content cleanup, header normalization, chapter
  removal, and table of contents generation
- **QR Code Integration**: Optionally generates QR codes for hyperlinks
- **Error Handling**: Comprehensive error handling with detailed context logging

## Function Tree

```
generator.py
├── heading_to_class(heading: str) -> str
│   └── Converts section headings to valid CSS class names
├── GuideMarkdownConverter(MarkdownConverter)
│   ├── __init__(image_map, section_class, **kwargs)
│   └── convert_img(el, text, convert_as_inline, **kwargs) -> str
│       └── Converts img tags to HTML with section classes and scaling
├── html_to_markdown(html, image_map, section_class) -> str
│   └── Converts HTML to Markdown using custom converter
├── build_image_map(content: ExtractedContent) -> dict[str, str]
│   └── Builds mapping from remote URLs to local image paths
├── generate_table_of_contents(markdown: str) -> str
│   └── Generates table of contents from header 2 entries
├── post_process_markdown(markdown: str) -> str
│   └── Applies comprehensive content cleanup and optimization
├── generate_guide(content, output_dir, add_qrcodes) -> str
│   └── Main function: generates complete Markdown guide from content
└── save_guide(guide: str, output_path: Path) -> Path
    └── Saves guide to file with proper error handling
```

## Usage Examples

### Basic Guide Generation

```python
from pathlib import Path
from src.generator import generate_guide, save_guide
from src.sources.base import ExtractedContent

# Create or load extracted content
content = ExtractedContent(
    title="My CoderDojo Project",
    sections=[...],  # List of section dictionaries
    images=[...],    # List of image dictionaries
    metadata={...}   # Optional metadata
)

# Generate guide without QR codes
guide = generate_guide(content, add_qrcodes=False)

# Save to file
output_path = Path("output/my_guide.md")
save_guide(guide, output_path)
```

### Advanced Guide Generation with QR Codes

```python
from pathlib import Path
from src.generator import generate_guide, save_guide

# Generate guide with QR codes for all hyperlinks
output_dir = Path("output")
guide = generate_guide(
    content=content,
    output_dir=output_dir,  # Required for QR codes
    add_qrcodes=True
)

# Save and get QR code files
output_path = output_dir / "complete_guide.md"
saved_path = save_guide(guide, output_path)
print(f"Guide saved to: {saved_path}")
```

### Custom HTML to Markdown Conversion

```python
from bs4 import BeautifulSoup
from src.generator import html_to_markdown

# Convert HTML content with custom image mapping
html_content = "<h2>Section</h2><img src='remote.jpg'>"
image_map = {"remote.jpg": "local/path/image.jpg"}

markdown = html_to_markdown(
    html=html_content,
    image_map=image_map,
    section_class="section-my-section"
)
```

## Configuration

The module uses settings from `src.core.config.get_settings()`:
- `IMAGE_SCALE`: Scaling factor for image dimensions (default: 1.0)

## Dependencies

- `markdownify`: Base Markdown conversion
- `beautifulsoup4`: HTML parsing and manipulation
- `pathlib`: Path handling for file operations
- `re`: Regular expressions for content processing

## Error Handling

All functions include comprehensive error handling with:
- Detailed error messages with context
- Logging at appropriate levels (debug, error)
- Custom `GenerationError` exceptions for recoverable failures

## Integration

This module integrates with:
- `src.core.config`: Configuration management
- `src.core.errors`: Custom error types
- `src.qrcode_processor`: QR code generation for links
- `src.sources.base`: Content extraction interfaces
"""

import inspect
import logging
import re
from pathlib import Path

from bs4 import Tag
from markdownify import MarkdownConverter

from src.core.config import get_settings
from src.core.errors import GenerationError
from src.qrcode_processor import process_markdown_links
from src.sources.base import ExtractedContent

settings = get_settings()
logger = logging.getLogger(__name__)


def heading_to_class(heading: str) -> str:
    """Convert a section heading to a valid CSS class name.

    This function transforms section headings into CSS-compatible class names
    that can be used for targeted styling in HTML/CSS output. It handles special
    characters, normalization, and ensures valid CSS identifier format.

    The conversion process:
    1. Convert to lowercase
    2. Remove non-alphanumeric characters (except spaces and hyphens)
    3. Replace spaces with hyphens
    4. Normalize multiple consecutive hyphens
    5. Remove leading/trailing hyphens
    6. Prefix with 'section-' for namespacing

    Args:
        heading: The section heading text to convert. Can be empty string.

    Returns:
        A valid CSS class name prefixed with 'section-'. For empty input,
        returns 'section-content'.

    Examples:
        >>> heading_to_class("Programming Steps")
        'section-programming-steps'
        >>> heading_to_class("Hardware & Software!")
        'section-hardware-software'
        >>> heading_to_class("")
        'section-content'
        >>> heading_to_class("  Multiple   Spaces  ")
        'section-multiple-spaces'
    """
    if not heading:
        return "section-content"
    # Lowercase, replace spaces with hyphens, remove special chars
    class_name = heading.lower()
    class_name = re.sub(r"[^a-z0-9\s-]", "", class_name)
    class_name = re.sub(r"\s+", "-", class_name)
    class_name = re.sub(r"-+", "-", class_name)
    return f"section-{class_name.strip('-')}"

class GuideMarkdownConverter(MarkdownConverter):
    """Custom Markdown converter that preserves image URLs and adds section classes.

    This converter extends the base MarkdownConverter to provide specialized
    functionality for CoderDojo guide generation:

    - **Image URL Preservation**: Maintains original image URLs while optionally
      substituting local paths from an image map
    - **Section-Based CSS Classes**: Adds CSS classes to images based on their
      content section for targeted styling in PDF generation
    - **Image Scaling**: Applies configurable scaling to image dimensions
    - **HTML Output**: Outputs HTML img tags instead of Markdown image syntax
      to preserve CSS classes and attributes

    The converter is designed to work with the guide generation pipeline where
    images need to be styled differently based on their section context
    (e.g., header images vs. content images vs. programming examples).

    Attributes:
        image_map: Dictionary mapping remote URLs to local file paths
        section_class: CSS class name applied to images in the current section

    Example:
        >>> image_map = {"https://example.com/img.jpg": "local/img.jpg"}
        >>> converter = GuideMarkdownConverter(
        ...     image_map=image_map,
        ...     section_class="section-programming"
        ... )
        >>> html = '<img src="https://example.com/img.jpg" alt="Example">'
        >>> result = converter.convert(html)
        # Returns HTML with local path and CSS class
    """

    def __init__(
        self,
        image_map: dict[str, str] | None = None,
        section_class: str | None = None,
        **kwargs,
        ):
        """Initialize converter with optional image mapping and section class.

        Sets up the converter with configuration for image processing and
        section-based styling. The image map allows substitution of remote URLs
        with local paths for offline access or optimized loading.

        Args:
            image_map: Optional dictionary mapping remote URLs to local file paths.
                      Keys are original URLs, values are local file paths.
                      If None, empty dict is used.
            section_class: CSS class name for images in the current section.
                          Used for targeted styling in CSS/PDF generation.
                          Defaults to 'section-content' if None.
            **kwargs: Additional arguments passed to parent MarkdownConverter.
                     Common options include heading_style, bullets, etc.

        Example:
            >>> image_map = {
            ...     "https://remote.com/img1.jpg": "local/img1.jpg",
            ...     "https://remote.com/img2.png": "local/img2.png"
            ... }
            >>> converter = GuideMarkdownConverter(
            ...     image_map=image_map,
            ...     section_class="section-hardware",
            ...     heading_style="ATX"
            ... )
        """
        super().__init__(**kwargs)
        self.image_map = image_map or {}
        self.section_class = section_class or "section-content"

    def convert_img(
        self, el: Tag, text: str = "", convert_as_inline: bool = False, **kwargs
        ) -> str:
        """Convert img tag to HTML img element with section class and scaling.

        This method overrides the default image conversion to:
        1. Substitute remote URLs with local paths from image_map
        2. Apply configurable scaling to width/height attributes
        3. Add section-based CSS class for targeted styling
        4. Output HTML img tags instead of Markdown image syntax

        The scaling uses the global IMAGE_SCALE setting from configuration,
        allowing consistent image sizing across the generated guide.

        Args:
            el: BeautifulSoup Tag representing the img element.
            text: Text content (usually empty for img tags).
            convert_as_inline: Whether to convert as inline element
                               (not typically used for images).
            **kwargs: Additional arguments passed by markdownify framework.

        Returns:
            HTML img tag string with src, alt, title, dimensions, and CSS class.
            The tag preserves all original attributes while adding the section
            class and applying scaling.

        Example:
            >>> # Given el is <img src="remote.jpg" width="100" alt="Test">
            >>> converter = GuideMarkdownConverter(
            ...     image_map={"remote.jpg": "local.jpg"},
            ...     section_class="section-demo"
            ... )
            >>> result = converter.convert_img(el)
            # Returns: '<img src="local.jpg" alt="Test" width="100" class="section-demo">'
        """
        src = el.get("src", "")
        alt = el.get("alt", "")
        title = el.get("title", "")

        # Check for local path in image map
        local_path = self.image_map.get(src)
        if local_path:
            src = local_path

        # Calculate dimensions with scaling
        width_attr = ""
        height_attr = ""
        scale = settings.IMAGE_SCALE

        width = el.get("width")
        height = el.get("height")

        if width:
            try:
                new_width = int(float(width) * scale) if scale != 1.0 else int(float(width))
                width_attr = f' width="{new_width}"'
            except (ValueError, TypeError):
                pass

        if height:
            try:
                new_height = int(float(height) * scale) if scale != 1.0 else int(float(height))
                height_attr = f' height="{new_height}"'
            except (ValueError, TypeError):
                pass

        # Build HTML img tag with section class
        alt_attr = f' alt="{alt}"' if alt else ' alt=""'
        title_attr = f' title="{title}"' if title else ""
        class_attr = f' class="{self.section_class}"'

        return f"<img src=\"{src}\"{alt_attr}{title_attr}{width_attr}{height_attr}{class_attr}>"

def html_to_markdown(
    html: str | Tag,
    image_map: dict[str, str] | None = None,
    section_class: str | None = None,
    ) -> str:
    """Convert HTML content to Markdown using custom converter with image processing.

    This function provides a high-level interface for HTML-to-Markdown conversion
    with specialized handling for images and content sections. It uses the
    GuideMarkdownConverter to ensure consistent formatting across the guide.

    The conversion process:
    1. Initialize custom converter with image mapping and section class
    2. Convert HTML to Markdown with ATX headings and dash bullets
    3. Clean up excessive whitespace (3+ newlines to 2 newlines)
    4. Fix spacing around Markdown links for proper rendering
    5. Return cleaned, properly formatted Markdown

    Args:
        html: HTML content to convert. Can be either a string containing HTML
              or a BeautifulSoup Tag object.
        image_map: Optional dictionary mapping remote URLs to local image paths.
                  Used for offline access and optimized loading.
        section_class: Optional CSS class name for images in this section.
                      Used for targeted styling in PDF generation.

    Returns:
        Cleaned Markdown string with HTML img tags (not Markdown image syntax)
        and proper spacing around links.

    Example:
        >>> html = '<h2>Section</h2><p>Text with <img src="img.jpg"> image</p>'
        >>> image_map = {"img.jpg": "local/img.jpg"}
        >>> markdown = html_to_markdown(html, image_map, "section-demo")
        >>> print(markdown)
        ## Section
        Text with <img src="local/img.jpg" class="section-demo"> image
    """
    if isinstance(html, Tag):
        html = str(html)

    converter = GuideMarkdownConverter(
        image_map=image_map,
        section_class=section_class,
        heading_style="ATX",
        bullets="-",
        code_language="",
        escape_underscores=False,
    )

    md = converter.convert(html)

    # Clean up excessive whitespace
    md = re.sub(r"\n{3,}", "\n\n", md)

    # Ensure space before markdown links when preceded by a word character
    # e.g., "de[link]" -> "de [link]"
    md = re.sub(r"(\w)\[([^\]]+)\]\(", r"\1 [\2](", md)

    # Ensure space after markdown links when followed by a word character
    # e.g., "[link](url)word" -> "[link](url) word"
    md = re.sub(r"\]\(([^)]+)\)(\w)", r"](\1) \2", md)

    return md.strip()

def build_image_map(content: ExtractedContent) -> dict[str, str]:
    """Build a mapping from remote image URLs to local file paths.

    This function creates a dictionary that maps original remote image URLs
    to their local file paths for offline access and optimized loading. It
    prioritizes enhanced paths over regular local paths when available.

    The mapping process:
    1. Iterate through all images in the extracted content
    2. Extract the src URL from each image
    3. Prefer enhanced_path if available, otherwise use local_path
    4. Convert Windows backslashes to forward slashes for Markdown compatibility
    5. Build dictionary mapping src -> local_path

    Args:
        content: ExtractedContent object containing images list with metadata.
                Each image should have 'src' and either 'enhanced_path' or
                'local_path' keys.

    Returns:
        Dictionary mapping remote src URLs to local file paths. Empty dict
        if no images with valid paths are found.

    Example:
        >>> content = ExtractedContent(
        ...     images=[
        ...         {"src": "https://example.com/img1.jpg", "local_path": "img1.jpg"},
        ...         {"src": "https://example.com/img2.png", "enhanced_path": "enhanced/img2.png"}
        ...     ]
        ... )
        >>> image_map = build_image_map(content)
        >>> image_map
        {'https://example.com/img1.jpg': 'img1.jpg',
         'https://example.com/img2.png': 'enhanced/img2.png'}
    """
    image_map = {}
    for image in content.images:
        src = image.get("src", "")
        if not src:
            continue

        # Prefer enhanced path, fall back to local path
        local_path = image.get("enhanced_path") or image.get("local_path")
        if local_path:
            # Use forward slashes for markdown compatibility
            # Backslashes cause escape sequence issues in markdown
            image_map[src] = local_path.replace("\\", "/")

    return image_map

def generate_table_of_contents(markdown: str) -> str:
    """Generate and insert a table of contents from header 2 entries.

    This function scans the markdown content for all level 2 headers (##)
    and creates a clickable table of contents that gets inserted after the
    main title (first level 1 header). The TOC provides navigation for
    longer guides and improves document structure.

    The generation process:
    1. Clean markdown from invisible characters for consistency
    2. Find all ## headers using regex
    3. Generate anchor links by converting headers to lowercase hyphenated format
    4. Create TOC in Markdown list format
    5. Insert TOC after the first # header

    Args:
        markdown: The markdown content to process. Should contain at least one
                  level 1 header for proper insertion.

    Returns:
        Markdown content with table of contents added. If no ## headers are
        found, returns the original markdown unchanged.

    Example:
        >>> markdown = "# Main Title\n\n## Section 1\n\nContent\n\n## Section 2\nContent"
        >>> result = generate_table_of_contents(markdown)
        >>> print(result)
        # Main Title

        ## Inhoudsopgave
        - [Section 1](#section-1)
        - [Section 2](#section-2)

        ## Section 1
        Content

        ## Section 2
        Content
    """
    # Clean markdown from invisible characters first to ensure consistency
    cleaned_markdown = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', markdown)
    cleaned_markdown = re.sub(r'[\u200B-\u200D\uFEFF]', '', cleaned_markdown)

    # Find all header 2 entries from cleaned markdown
    headers = re.findall(r'^## (.+)$', cleaned_markdown, flags=re.MULTILINE)

    if not headers:
        return markdown

    # Generate table of contents
    toc_lines = ["## Inhoudsopgave\n"]
    for header in headers:
        # Create anchor link by converting to lowercase and replacing spaces with hyphens
        anchor = header.lower().replace(' ', '-').replace('/', '').replace('(', '').replace(')', '')
        toc_lines.append(f"- [{header}](#{anchor})")

    toc = "\n".join(toc_lines) + "\n\n"

    # Insert table of contents after the main title (first # header)
    title_pattern = r'^(# .+)$'
    if re.search(title_pattern, markdown, flags=re.MULTILINE):
        markdown = re.sub(title_pattern, r'\1\n\n' + toc, markdown, count=1, flags=re.MULTILINE)

    return markdown

def post_process_markdown(markdown: str) -> str:
    """Apply comprehensive post-processing fixes and optimizations to markdown.

    This function performs extensive cleanup and normalization of the generated
    markdown to ensure consistent formatting, proper structure, and optimal
    rendering. It handles content filtering, header normalization, image scaling,
    and table of contents generation.

    Processing stages:
    1. **Character Cleanup**: Remove invisible Unicode characters and control chars
    2. **Content Filtering**: Remove unwanted sections like "Invoering" paragraphs
    3. **Header Normalization**: Convert specific headers to level 2 for consistency
    4. **Chapter Removal**: Remove entire sections (Lesvoorbereiding, Demonstratie, etc.)
    5. **Image Scaling**: Scale first non-QR image in Programmering section to 50%
    6. **TOC Generation**: Add table of contents with all header 2 entries
    7. **URL Updates**: Fix specific URLs (e.g., elecfreaks.com domain changes)

    Args:
        markdown: The raw markdown content to process, typically from
                 html_to_markdown conversion.

    Returns:
        Processed markdown content with:
        - Clean, readable formatting
        - Consistent header structure
        - Removed unwanted content
        - Properly scaled images
        - Generated table of contents
        - Fixed hyperlinks

    Note:
        Some title word fixes (Geval->Project, etc.) are handled in translator.py
        via TITLE_WORD_FIXES and _apply_title_fixes() to maintain separation of concerns.

    Example:
        >>> raw_md = "# Title\n\n> Invoering\n\n### Stap 1\nContent"
        >>> processed = post_process_markdown(raw_md)
        >>> print(processed)
        # Title

        ## Inhoudsopgave

        ## Programmering
        Content
    """
    # Remove all invisible characters comprehensively
    # Control characters (0x00-0x1F, 0x7F-0x9F) except common whitespace (\t, \n, \r)
    markdown = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', markdown)
    # Zero-width characters and other invisible Unicode characters
    markdown = re.sub(r'[\u200B-\u200D\uFEFF\u2060\u180E\u00AD]', '', markdown)
    # Various spaces and separators that should be normalized
    markdown = re.sub(r'[\u2000-\u200A\u202F\u205F\u3000]', ' ', markdown)  # Convert to regular space
    # Line and paragraph separators
    markdown = re.sub(r'[\u2028\u2029]', '\n', markdown)  # Convert to regular newline

    # Remove paragraph containing "Invoering" just after header 1
    # Pattern: # Header\n\n> Invoering\n\n or # Header\n\nInvoering\n\n
    markdown = re.sub(r'(^# .+\n\n)>? ?Invoering\n\n', r'\1', markdown, flags=re.MULTILINE)

    # Change title "Stap 1" to "Programmering"
    markdown = re.sub(r'^#+ Stap 1', '## Programmering', markdown, flags=re.MULTILINE)

    # Change specific hyperlink from elecfreaks.com to shop.elecfreaks.com
    old_url = "https://www.elecfreaks.com/nezha-inventor-s-kit-for-micro-bit-without-micro-bit-board.html"
    new_url = "https://shop.elecfreaks.com/products/elecfreaks-micro-bit-nezha-48-in-1-inventors-kit-without-micro-bit-board"
    markdown = markdown.replace(old_url, new_url)

    # Clean all headers by removing inline markdown and anchor links
    # This handles patterns like " [#](#purpose "Permalink to this headline")" and similar
    lines = markdown.split('\n')
    for i, line in enumerate(lines):
        # Match any header line (# to ######)
        header_match = re.match(r'^(#{1,6})\s+(.+)$', line.rstrip())
        if header_match:
            header_level = header_match.group(1)
            header_text = header_match.group(2)

            # Remove anchor links and other inline markdown from headers
            # Pattern 1: [#](#id "title") - common permalink format
            header_text = re.sub(r'\s*\[\s*#\s*\]\(\s*#[^)]*\s+"[^"]*"\s*\)\s*', '', header_text)
            # Pattern 2: [#](#id) - simple anchor links
            header_text = re.sub(r'\s*\[\s*#\s*\]\(\s*#[^)]*\s*\)\s*', '', header_text)
            # Pattern 3: [text](#id) - any anchor link
            header_text = re.sub(r'\s*\[[^\]]*\]\(\s*#[^)]*\s*\)\s*', '', header_text)
            # Pattern 4: Remove any remaining brackets that might be empty
            header_text = re.sub(r'\s*\[\s*\]\s*', '', header_text)
            # Pattern 5: Remove numbering like "3." or "3.1." from headers
            header_text = re.sub(r'^\d+(?:\.\d+)*\.?\s*', '', header_text)
            # Pattern 6: Remove trailing whitespace
            header_text = header_text.strip()

            # Reconstruct the clean header
            lines[i] = f'{header_level} {header_text}'

    markdown = '\n'.join(lines)

    # Headers to normalize to level 2, removing any trailing content
    headers_to_convert = {
        'Programmering',
        'Benodigde materialen',
        'Montage stappen',
        'Montagestappen',
        'Montage',
        'Montagevideo',
        'Aansluitschema',
        'Resultaat',
        'Referentie',
        'Hardware',
        'Hardwareverbinding',
        'Softwareprogrammering',
        'Demonstratie',
    }

    # Single pass: find all headers and convert matching ones to level 2
    lines = markdown.split('\n')
    for i, line in enumerate(lines):
        # Match any header line (## to ######)
        header_match = re.match(r'^(#{2,6})\s+(.+)$', line.rstrip())
        if header_match:
            header_text = header_match.group(2)

            # Clean header text: remove anchor links like [](#id "title") and strip
            header_text_clean = re.sub(r'\s*\[]\(#[^)]*\)\s*$', '', header_text).strip()

            # Check if this header starts with any of our target headers
            for target in headers_to_convert:
                if header_text_clean == target or header_text_clean.startswith(target + ' '):
                    replacement = f'## {target}'
                    if lines[i] != replacement:
                        logger.debug(f"Converting header: {repr(line)} -> {repr(replacement)}")
                        lines[i] = replacement
                    break

    markdown = '\n'.join(lines)

    # Note: Title word fixes (Geval->Project, etc.) are now handled in translator.py
    # via TITLE_WORD_FIXES and _apply_title_fixes()

    # Remove entire chapters (header + content) for specified section names
    chapters_to_remove = [
        'Lesvoorbereiding',
        'Demonstratie',
        "Reflectie"
    ]

    lines = markdown.split('\n')
    filtered_lines = []
    skip_until_next_header = False
    skip_header_level = 0

    for line in lines:
        # Check if this line is a header
        header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if header_match:
            header_level = len(header_match.group(1))
            header_text = header_match.group(2).strip()

            if skip_until_next_header:
                # Check if we've reached a header of same or higher level (fewer #'s)
                if header_level <= skip_header_level:
                    skip_until_next_header = False
                else:
                    # Still in the section to remove, skip this line
                    continue

            # Check if this header should be removed
            if any(header_text == chapter or header_text.startswith(chapter + ' ')
                   for chapter in chapters_to_remove):
                skip_until_next_header = True
                skip_header_level = header_level
                continue

        elif skip_until_next_header:
            # Skip content lines while in a chapter to remove
            continue

        filtered_lines.append(line)

    markdown = '\n'.join(filtered_lines)

    # Scale down the first non-QR code image after "## Programmering" header
    lines = markdown.split('\n')
    in_programming_section = False
    for i, line in enumerate(lines):
        # Look for the Programmering section header
        if line.strip() == '## Programmering':
            in_programming_section = True
            continue

        # Once in programming section, find the first image (not QR code) and scale it
        if in_programming_section:
            # Check if this line contains an HTML img tag (not QR code)
            img_match = re.match(r'^(\s*)<img\s+src="([^"]+)"([^>]*)>(\s*)$', line)
            if img_match and 'qrcode' not in line.lower():
                # Add scaling style to make image 50% smaller
                indent = img_match.group(1)
                img_path = img_match.group(2)
                other_attrs = img_match.group(3)
                trailing = img_match.group(4)
                # Insert style before the closing >
                scaled_img = f'{indent}<img src="{img_path}" class="img-half"{other_attrs}>{trailing}'
                lines[i] = scaled_img
                # Only scale the first image after the header
                break
            # Stop if we hit another section header
            elif line.startswith('## '):
                break
    markdown = '\n'.join(lines)

    # Add table of contents with all header 2 entries
    markdown = generate_table_of_contents(markdown)

    return markdown

def generate_guide(
    content: ExtractedContent, output_dir: Path | None = None, add_qrcodes: bool = True
    ) -> str:
    """Generate a complete Markdown guide from extracted content.

    This is the main function that orchestrates the entire guide generation
    process. It converts structured extracted content into a well-formatted
    Markdown document with proper organization, image handling, and optional
    QR code generation for hyperlinks.

    The generation process:
    1. Build image mapping for local path substitution
    2. Create document structure with title and metadata
    3. Process each section with appropriate CSS classes
    4. Convert HTML content to Markdown with image processing
    5. Apply comprehensive post-processing and cleanup
    6. Optionally generate QR codes for all hyperlinks
    7. Return final formatted guide

    Args:
        content: ExtractedContent object containing the structured content
                with title, sections, images, and metadata.
        output_dir: Output directory for QR code generation. Required if
                   add_qrcodes is True, otherwise optional.
        add_qrcodes: Whether to generate QR codes for hyperlinks in the guide.
                    Defaults to True for enhanced accessibility.

    Returns:
        Complete Markdown guide string ready for saving or further processing.
        The guide includes proper formatting, table of contents, processed
        images, and optionally QR codes.

    Raises:
        GenerationError: If guide generation fails due to content processing
                        errors, missing output directory for QR codes, or
                        other processing issues.

    Example:
        >>> from pathlib import Path
        >>> from src.sources.base import ExtractedContent
        >>>
        >>> content = ExtractedContent(
        ...     title="My Arduino Project",
        ...     sections=[
        ...         {
        ...             "heading": "Hardware Setup",
        ...             "level": 2,
        ...             "content": [BeautifulSoup("<p>Connect the LED</p>", "html.parser")]
        ...         }
        ...     ],
        ...     images=[],
        ...     metadata={"description": "A beginner Arduino project"}
        ... )
        >>>
        >>> guide = generate_guide(
        ...     content=content,
        ...     output_dir=Path("output"),
        ...     add_qrcodes=True
        ... )
        >>> print(guide[:100])  # First 100 characters
        # My Arduino Project

        > A beginner Arduino project

        ## Inhoudsopgave
        - [Hardware Setup](#hardware-setup)

        ## Hardware Setup
        Connect the LED
    """
    logger.debug(f" * {inspect.currentframe().f_code.co_name} > Generating guide: {content.title}")

    try:
        parts = []

        # Build image map for local path substitution
        image_map = build_image_map(content)
        if image_map:
            logger.debug(f"    -> Using {len(image_map)} local image paths")

        # Title
        parts.append(f"# {content.title}\n")

        # Metadata section (optional)
        if content.metadata.get("description"):
            parts.append(f"> {content.metadata['description']}\n")

        # Language indicator if translated
        if content.metadata.get("language") and content.metadata.get("language") != "en":
            lang = content.metadata["language"]
            logger.debug(f"    -> Content language: {lang}")

        # Sections - track current section for image classification
        current_section_class = "section-header"

        for section in content.sections:
            heading = section.get("heading", "")
            level = section.get("level", 2)
            section_content = section.get("content", [])

            # Skip section if heading duplicates the title
            if heading and heading == content.title:
                continue

            # Update current section class for image classification
            if heading:
                current_section_class = heading_to_class(heading)
                prefix = "#" * level
                parts.append(f"\n{prefix} {heading}\n")

            # Convert each content element with section context
            for element in section_content:
                if isinstance(element, Tag):
                    md = html_to_markdown(
                        element, image_map=image_map, section_class=current_section_class
                    )
                    if md:
                        parts.append(md + "\n")

        # Combine all parts
        guide = "\n".join(parts)

        # Final cleanup
        guide = re.sub(r"\n{3,}", "\n\n", guide)

        logger.debug(f"    -> Generated {len(guide)} bytes of Markdown")

        # Apply post-processing fixes
        guide = post_process_markdown(guide)

        # Add QR codes for hyperlinks if requested
        if add_qrcodes and output_dir:
            logger.debug("    -> Processing hyperlinks for QR codes")
            guide, qr_codes = process_markdown_links(guide, output_dir)
            if qr_codes:
                logger.debug(f"    -> Added {len(qr_codes)} QR codes")

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
    """Save a generated guide to file with proper error handling.

    This function handles the file I/O operations for saving generated guides,
    ensuring that directories are created as needed and providing detailed
    error context if saving fails. It uses UTF-8 encoding to support
    international characters and special symbols.

    The saving process:
    1. Ensure parent directory exists (create if needed)
    2. Write guide content to file using UTF-8 encoding
    3. Log successful save operation
    4. Return the final output path for confirmation

    Args:
        guide: The complete Markdown guide content to save.
                Should be a string generated by generate_guide().
        output_path: Path where the guide should be saved. Can include
                    subdirectories which will be created automatically.

    Returns:
        Path object where the guide was actually saved. This matches the
        input output_path but ensures the operation completed successfully.

    Raises:
        GenerationError: If saving fails due to permission issues, disk space,
                        invalid path, or other I/O errors.

    Example:
        >>> from pathlib import Path
        >>> guide_content = "# My Guide\n\nThis is my guide content."
        >>> output_path = Path("output/guides/my_guide.md")
        >>>
        >>> try:
        ...     saved_path = save_guide(guide_content, output_path)
        ...     print(f"Guide saved to: {saved_path}")
        ... except GenerationError as e:
        ...     print(f"Failed to save guide: {e}")
        Guide saved to: output/guides/my_guide.md
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


def _create_sample_content() -> ExtractedContent:
    """Create sample ExtractedContent for demonstration purposes.

    Returns:
        ExtractedContent with sample sections, images, and metadata.
    """
    from bs4 import BeautifulSoup

    # Create sample HTML content
    sample_html = """
    <p>This is a sample CoderDojo project guide.</p>
    <img src="https://example.com/circuit.jpg" alt="Circuit diagram" width="400">
    <h3>Components Needed</h3>
    <ul>
        <li>Arduino Uno</li>
        <li>LED</li>
        <li>220Ω resistor</li>
        <li>Breadboard</li>
    </ul>
    <p>Visit <a href="https://www.arduino.cc">Arduino website</a> for more info.</p>
    """

    # Parse HTML into BeautifulSoup objects
    soup = BeautifulSoup(sample_html, 'html.parser')
    content_elements = list(soup.children)

    return ExtractedContent(
        title="Sample Arduino LED Project",
        sections=[
            {
                "heading": "Hardware Setup",
                "level": 2,
                "content": content_elements
            },
            {
                "heading": "Programming",
                "level": 2,
                "content": [BeautifulSoup("<p>Upload the following code to your Arduino:</p>", "html.parser")]
            }
        ],
        images=[
            {
                "src": "https://example.com/circuit.jpg",
                "local_path": "images/circuit.jpg",
                "alt": "Circuit diagram",
                "width": "400"
            }
        ],
        metadata={
            "description": "A beginner-friendly Arduino project with LED",
            "language": "en",
            "difficulty": "beginner"
        }
    )


def main():
    """Main function for running the generator with sample data.

    This function demonstrates the usage of the generator module with
    hardcoded sample parameters. It creates a sample guide, processes it,
    and saves it to the output directory.

    Usage:
        python -m src.generator

    The function will:
    1. Create sample ExtractedContent
    2. Generate a Markdown guide with QR codes
    3. Save the guide to output/sample_guide.md
    4. Print success message with file location
    """
    import logging
    from pathlib import Path

    # Configure logging for demo
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)s: %(message)s'
    )

    print("🚀 Starting CoderDojo Guide Generator Demo")
    print("=" * 50)

    try:
        # Create sample content
        print("📝 Creating sample content...")
        content = _create_sample_content()
        print(f"   ✓ Title: {content.title}")
        print(f"   ✓ Sections: {len(content.sections)}")
        print(f"   ✓ Images: {len(content.images)}")

        # Set up output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        # Generate guide with QR codes
        print("\n🔄 Generating Markdown guide...")
        guide = generate_guide(
            content=content,
            output_dir=output_dir,
            add_qrcodes=True
        )
        print(f"   ✓ Generated {len(guide)} characters")

        # Save guide
        output_path = output_dir / "sample_guide.md"
        print(f"\n💾 Saving guide to {output_path}...")
        saved_path = save_guide(guide, output_path)
        print(f"   ✓ Saved to: {saved_path}")

        # Show preview
        print("\n📋 Guide Preview:")
        print("-" * 30)
        lines = guide.split('\n')
        for i, line in enumerate(lines[:10]):  # Show first 10 lines
            print(f"{i+1:2d}: {line}")
        if len(lines) > 10:
            print(f"... ({len(lines) - 10} more lines)")

        print("\n✅ Demo completed successfully!")
        print(f"📁 Check the output directory: {output_dir.absolute()}")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return 1

    return 0


if __name__ == "__main__":
    """Entry point when running the module directly.

    Allows the generator to be run as:
        python -m src.generator
    """
    exit(main())
