"""Elecfreaks Wiki source adapter for content extraction."""

import inspect
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from src.core.config import get_settings
from src.sources.base import BaseSourceAdapter, ExtractedContent, TutorialLink

settings = get_settings()
logger = logging.getLogger(__name__)


class ElecfreaksAdapter(BaseSourceAdapter):
    """Adapter for extracting content from Elecfreaks Wiki pages.

    The Elecfreaks Wiki uses Docusaurus, so we look for specific
    CSS classes and structure typical of that platform.
    """

    DOMAIN_PATTERNS = [
        "wiki.elecfreaks.com",
        "elecfreaks.com/wiki",
        "elecfreaks.com/learn-en",
        "www.elecfreaks.com/learn-en",
    ]

    # CSS selectors for content removal (navigation, sidebars, etc.)
    REMOVE_SELECTORS = [
        ".navbar",
        ".sidebar",
        ".footer",
        ".breadcrumbs",
        ".toc",
        ".pagination-nav",
        ".theme-doc-sidebar-container",
        ".theme-doc-footer",
        ".theme-doc-toc-mobile",
        "nav",
        "footer",
        "[class*='breadcrumb']",
        "[class*='sidebar']",
        "[class*='pagination']",
    ]

    # CSS selectors for main content (in priority order)
    CONTENT_SELECTORS = [
        ".theme-doc-markdown.markdown",  # Most specific for Docusaurus
        ".theme-doc-markdown",
        "article .markdown",
        ".markdown",
        "article",
        "div.body",  # Sphinx documentation
        ".documentwrapper",  # Sphinx documentation
        "[role='main']",  # Accessibility role
        "main",
        ".docMainContainer",
    ]

    def can_handle(self, url: str) -> bool:
        """Check if this adapter can handle the given URL.

        Args:
            url: The URL to check.

        Returns:
            True if URL is from Elecfreaks Wiki.
        """
        return any(pattern in url.lower() for pattern in self.DOMAIN_PATTERNS)

    def extract(self, soup: BeautifulSoup, url: str) -> ExtractedContent:
        """Extract content from an Elecfreaks Wiki page.

        Args:
            soup: Parsed HTML as BeautifulSoup object.
            url: The source URL for context.

        Returns:
            ExtractedContent with title, sections, images, and metadata.
        """
        logger.debug(f" * {inspect.currentframe().f_code.co_name} > Extracting from: {url}")

        # Remove unwanted elements
        self._remove_navigation(soup)

        # Find main content
        main_content = self._find_main_content(soup)
        if main_content is None:
            logger.warning("    -> Could not find main content, using body")
            main_content = soup.body or soup

        # Extract title
        title = self._extract_title(main_content, soup)
        logger.debug(f"    -> Title: {title}")

        # Extract sections
        sections = self._extract_sections(main_content)
        logger.debug(f"    -> Found {len(sections)} sections")

        # Extract images
        images = self._extract_images(main_content, url)
        logger.debug(f"    -> Found {len(images)} images")

        # Extract metadata
        metadata = self._extract_metadata(soup, url)

        return ExtractedContent(
            title=title,
            sections=sections,
            images=images,
            metadata=metadata,
        )

    def _remove_navigation(self, soup: BeautifulSoup) -> None:
        """Remove navigation and sidebar elements from the soup."""
        for selector in self.REMOVE_SELECTORS:
            for element in soup.select(selector):
                element.decompose()

    def _find_main_content(self, soup: BeautifulSoup) -> Tag | None:
        """Find the main content container."""
        for selector in self.CONTENT_SELECTORS:
            content = soup.select_one(selector)
            if content:
                logger.debug(f"    -> Found content using selector: {selector}")
                return content
        return None

    def _extract_title(self, content: Tag, soup: BeautifulSoup) -> str:
        """Extract the page title."""
        # Try h1 in content first
        h1 = content.find("h1")
        if h1 and h1.get_text(strip=True):
            return h1.get_text(strip=True)

        # Fall back to page title
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Remove site suffix
            title = re.sub(r"\s*\|\s*.*$", "", title)
            title = re.sub(r"\s*-\s*.*$", "", title)
            return title

        return "Untitled"

    def _extract_sections(self, content: Tag) -> list[dict]:
        """Extract content sections split by h2 headers."""
        sections = []
        current_section: dict = {"heading": "", "content": [], "level": 0}

        # Remove h1 from content to avoid duplication (title already extracted)
        h1 = content.find("h1")
        if h1:
            h1.decompose()

        for element in content.children:
            if not isinstance(element, Tag):
                continue

            if element.name in ("h2", "h3", "h4"):
                # Save previous section if it has content
                if current_section["content"]:
                    sections.append(current_section)

                # Start new section
                level = int(element.name[1])
                current_section = {
                    "heading": element.get_text(strip=True),
                    "content": [],
                    "level": level,
                }
            else:
                # Add to current section
                current_section["content"].append(element)

        # Don't forget the last section
        if current_section["content"]:
            sections.append(current_section)

        return sections

    def _extract_images(self, content: Tag, base_url: str) -> list[dict]:
        """Extract images from the content.

        Also updates img tags in place with absolute URLs so that
        sections (which reference the same Tag objects) will have
        matching src attributes for the image map lookup.
        """
        images = []

        for img in content.find_all("img"):
            src = img.get("src", "")
            if not src:
                continue

            # Make URL absolute
            if src.startswith("//"):
                src = "https:" + src
            elif not src.startswith(("http://", "https://")):
                src = urljoin(base_url, src)

            # Update the img tag with absolute URL so sections have matching src
            img["src"] = src

            alt = img.get("alt", "")
            title = img.get("title", "")

            images.append(
                {
                    "src": src,
                    "alt": alt,
                    "title": title,
                }
            )

        return images

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> dict:
        """Extract page metadata."""
        metadata = {"url": url, "source": "elecfreaks"}

        # Try to extract description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            metadata["description"] = meta_desc["content"]

        return metadata

    def extract_tutorial_links(self, soup: BeautifulSoup, url: str) -> list[TutorialLink]:
        """Extract tutorial links from an Elecfreaks index page.

        Extracts tutorial links from multiple sources:
        1. Card-based tutorial listings (article.margin--md with card links) - Docusaurus
        2. Sphinx-style reference links (a.reference.internal with Case_ in href)
        3. Sphinx toctree structure (div.toctree-wrapper with li.toctree-l1 links)
        4. Navigation sidebar links containing "case" in the URL path

        Args:
            soup: Parsed HTML as BeautifulSoup object.
            url: The source URL for context.

        Returns:
            List of TutorialLink objects with url and title.
        """
        logger.debug(f" * {inspect.currentframe().f_code.co_name} > Extracting tutorial links from: {url}")

        tutorials: list[TutorialLink] = []
        seen_urls: set[str] = set()

        # Track counts for each extraction method
        method_counts = {
            "card": 0,
            "sphinx": 0,
            "toctree": 0,
            "sidebar": 0
        }

        # Method 1: Find card-based tutorials (article elements with card links)
        for article in soup.find_all("article", class_="margin--md"):
            # Find the card link inside the article
            card_link = article.find("a", class_=lambda c: c and ("card" in c or "cardContainer" in c))
            if not card_link:
                continue

            href = card_link.get("href", "")
            if not href:
                continue

            # Extract title from h2 with cardTitle class or text--truncate
            title_elem = article.find("h2", class_=lambda c: c and ("cardTitle" in c or "text--truncate" in c))
            if title_elem:
                # Prefer the title attribute if available (full text)
                title = title_elem.get("title") or title_elem.get_text(strip=True)
            else:
                title = card_link.get_text(strip=True)

            if not title:
                continue

            # Make URL absolute
            href = self._make_absolute_url(href, url)

            # Skip duplicates and current page
            if href in seen_urls or href.rstrip("/") == url.rstrip("/"):
                continue
            seen_urls.add(href)

            tutorials.append(TutorialLink(url=href, title=title))
            method_counts["card"] += 1
            logger.debug(f"    -> Found card tutorial: {title}")

        # Method 2: Find Sphinx-style reference links (a.reference.internal)
        # Pattern: <a class="reference internal" href="Case_01.html#section">Title</a>
        for link in soup.find_all("a", class_="reference"):
            classes = link.get("class", [])
            if "internal" not in classes:
                continue

            href = link.get("href", "")
            text = link.get_text(strip=True)

            if not href or not text:
                continue

            # Look for Case_ pattern in href (e.g., Case_01.html)
            if not re.search(r"case[_\-]?\d+", href, re.IGNORECASE):
                continue

            # Remove anchor fragment for deduplication (Case_01.html#link -> Case_01.html)
            base_href = href.split("#")[0] if "#" in href else href

            # Make URL absolute
            abs_href = self._make_absolute_url(base_href, url)

            # Skip duplicates
            if abs_href in seen_urls:
                continue
            seen_urls.add(abs_href)

            # Clean up title - remove leading number prefix (e.g., "3.2. Link" -> "Link")
            clean_title = re.sub(r"^\d+\.\d+\.\s*", "", text).strip()
            if not clean_title:
                clean_title = text.strip()

            tutorials.append(TutorialLink(url=abs_href, title=clean_title))
            method_counts["sphinx"] += 1
            logger.debug(f"    -> Found Sphinx tutorial: {clean_title}")

        # Method 3: Find Sphinx toctree links (top-level only)
        # Pattern: <div class="toctree-wrapper compound"><ul><li class="toctree-l1"><a>...</a></li>
        for toctree in soup.find_all("div", class_="toctree-wrapper"):
            for li in toctree.find_all("li", class_="toctree-l1"):
                link = li.find("a", class_="reference")
                if not link:
                    continue

                classes = link.get("class", [])
                if "internal" not in classes:
                    continue

                href = link.get("href", "")
                text = link.get_text(strip=True)

                if not href or not text:
                    continue

                # Skip non-tutorial pages (like safety instructions)
                # Look for Case/case pattern in href or text
                is_case_href = re.search(r"case[_\-]?\d+", href, re.IGNORECASE)
                is_case_text = re.search(r"case\s*\d+", text, re.IGNORECASE)

                if not is_case_href and not is_case_text:
                    continue

                # Make URL absolute
                abs_href = self._make_absolute_url(href, url)

                # Skip duplicates
                if abs_href in seen_urls:
                    continue
                seen_urls.add(abs_href)
                # Clean up title - remove leading number prefix (e.g., "3. Case 01:" -> "Case 01:")
                clean_title = re.sub(r"^\d+\.\s*", "", text).strip()

                tutorials.append(TutorialLink(url=abs_href, title=clean_title))
                method_counts["toctree"] += 1
                logger.debug(f"    -> Found toctree tutorial: {clean_title}")

        # Method 4: Find sidebar links containing "case" in the path
        '''
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            # Skip empty links
            if not href or not text:
                continue

            # Look for case tutorial links
            # Pattern: URLs containing "case" in the path
            if "case" not in href.lower():
                continue

            # Make URL absolute
            href = self._make_absolute_url(href, url)

            # Skip if we've already seen this URL
            if href in seen_urls:
                continue
            seen_urls.add(href)

            # Skip the current page
            if href.rstrip("/") == url.rstrip("/"):
                continue

            # Extract and clean up the title
            title = text.strip()

            tutorials.append(TutorialLink(url=href, title=title))
            method_counts["sidebar"] += 1
            logger.debug(f"    -> Found case tutorial: {title}")
'''
        # Log method breakdown
        method_summary = ", ".join([f"{method}: {count}" for method, count in method_counts.items() if count > 0])
        if method_summary:
            logger.info(f"    -> Found {len(tutorials)} tutorials ({method_summary})")
        else:
            logger.info(f"    -> Found {len(tutorials)} tutorials")
        
        return tutorials

    def _make_absolute_url(self, href: str, base_url: str) -> str:
        """Convert a relative URL to absolute.

        Args:
            href: The URL to convert (may be relative or absolute).
            base_url: The base URL for resolving relative paths.

        Returns:
            Absolute URL string.
        """
        if href.startswith(("http://", "https://")):
            return href
        return urljoin(base_url, href)
