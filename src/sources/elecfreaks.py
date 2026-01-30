"""Elecfreaks Wiki source adapter for content extraction.

This adapter handles multiple Elecfreaks website variants:
- Sphinx-based documentation (elecfreaks.com/learn-en/)
- Docusaurus-based wiki (wiki.elecfreaks.com)

Each site type has specific container selectors and extraction logic
configured via the SITE_CONFIGS mapping.
"""

import inspect
import logging
import re
from dataclasses import dataclass
from enum import Enum, auto
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from src.core.config import get_settings
from src.sources.base import BaseSourceAdapter, ExtractedContent, TutorialLink

settings = get_settings()
logger = logging.getLogger(__name__)


class SiteType(Enum):
    """Enumeration of supported site types with different extraction strategies."""

    SPHINX_TOCTREE = auto()  # Sphinx-style with toctree structure
    DOCUSAURUS_CARD_MARGIN = auto()  # Docusaurus with article.margin--md cards
    DOCUSAURUS_CARD_COL = auto()  # Docusaurus with article.col cards


@dataclass
class SiteConfig:
    """Configuration for a specific site type's extraction strategy.

    Attributes:
        site_type: The type of site (determines extraction method).
        container_selector: CSS selector for the main container to search within.
        url_patterns: List of URL patterns (substrings) that match this config.
        description: Human-readable description of this site type.
        skip_patterns: Optional list of href patterns to skip (e.g., safety_instructions).
    """

    site_type: SiteType
    container_selector: str
    url_patterns: list[str]
    description: str
    skip_patterns: list[str] | None = None


# Site configurations ordered by specificity (most specific first)
# The first matching config will be used for extraction
SITE_CONFIGS: list[SiteConfig] = [
    # Sphinx-based documentation (elecfreaks.com/learn-en/)
    # Example: https://www.elecfreaks.com/learn-en/microbitKit/Wonder_Building_Kit/index.html
    SiteConfig(
        site_type=SiteType.SPHINX_TOCTREE,
        container_selector="body > div.container-xl > div > div.col.py-0.content-container > div.article.row",
        url_patterns=["elecfreaks.com/learn-en/"],
        description="Sphinx toctree-based documentation (Wonder Building Kit)",
        skip_patterns=["safety_instructions", "introduction", "packing_list", "components"],
    ),
    # Docusaurus wiki with article.margin--md cards
    # Example: https://wiki.elecfreaks.com/en/microbit/building-blocks/nezha-inventors-kit-v2/
    SiteConfig(
        site_type=SiteType.DOCUSAURUS_CARD_MARGIN,
        container_selector="article div.theme-doc-markdown.markdown",
        url_patterns=["nezha-inventors-kit-v2"],
        description="Docusaurus cards with margin--md articles (Nezha Kit V2)",
        skip_patterns=None,
    ),
    # Docusaurus wiki with article.col cards (nezha-inventors-kit original)
    # Example: https://wiki.elecfreaks.com/en/microbit/building-blocks/nezha-inventors-kit/
    SiteConfig(
        site_type=SiteType.DOCUSAURUS_CARD_COL,
        container_selector="article div.theme-doc-markdown.markdown",
        url_patterns=["nezha-inventors-kit/"],
        description="Docusaurus cards with col articles (Nezha Kit V1)",
        skip_patterns=None,
    ),
    # Docusaurus wiki with article.col cards (microbit-starter-kit)
    # Example: https://wiki.elecfreaks.com/en/microbit/interesting-case/microbit-starter-kit/
    SiteConfig(
        site_type=SiteType.DOCUSAURUS_CARD_COL,
        container_selector="article div.theme-doc-markdown.markdown",
        url_patterns=["microbit-starter-kit"],
        description="Docusaurus cards with col articles (Starter Kit)",
        skip_patterns=None,
    ),
    # Default Docusaurus wiki fallback (for other wiki.elecfreaks.com pages)
    SiteConfig(
        site_type=SiteType.DOCUSAURUS_CARD_COL,
        container_selector="article div.theme-doc-markdown.markdown",
        url_patterns=["wiki.elecfreaks.com"],
        description="Docusaurus wiki fallback",
        skip_patterns=None,
    ),
]


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

    def _get_site_config(self, url: str) -> SiteConfig | None:
        """Find the matching site configuration for a URL.

        Iterates through SITE_CONFIGS in order (most specific first) and
        returns the first configuration whose URL patterns match the input URL.

        Args:
            url: The URL to match against site configurations.

        Returns:
            SiteConfig if a match is found, None otherwise.
        """
        url_lower = url.lower()
        for config in SITE_CONFIGS:
            for pattern in config.url_patterns:
                if pattern.lower() in url_lower:
                    logger.debug(
                        f"    -> URL matched config: {config.description} "
                        f"(pattern: '{pattern}')"
                    )
                    return config
        return None

    def _find_container(self, soup: BeautifulSoup, selector: str) -> Tag | None:
        """Find the container element using the given CSS selector.

        Args:
            soup: Parsed HTML as BeautifulSoup object.
            selector: CSS selector string to locate the container.

        Returns:
            The matched Tag element, or None if not found.
        """
        container = soup.select_one(selector)
        if container:
            logger.debug(f"    -> Found container using selector: {selector}")
        else:
            logger.warning(f"    -> Container not found for selector: {selector}")
        return container

    def _should_skip_href(self, href: str, skip_patterns: list[str] | None) -> bool:
        """Check if a href should be skipped based on skip patterns.

        Args:
            href: The href value to check.
            skip_patterns: List of patterns to match against href.

        Returns:
            True if the href matches any skip pattern.
        """
        if not skip_patterns:
            return False
        href_lower = href.lower()
        for pattern in skip_patterns:
            if pattern.lower() in href_lower:
                logger.debug(f"    -> Skipping href matching pattern '{pattern}': {href}")
                return True
        return False

    def extract_tutorial_links(self, soup: BeautifulSoup, url: str) -> list[TutorialLink]:
        """Extract tutorial links from an Elecfreaks index page.

        Uses URL-specific extraction strategies defined in SITE_CONFIGS.
        The extraction method is selected based on the URL pattern:

        - SPHINX_TOCTREE: For elecfreaks.com/learn-en/ pages with toctree structure
        - DOCUSAURUS_CARD_MARGIN: For wiki pages with article.margin--md cards
        - DOCUSAURUS_CARD_COL: For wiki pages with article.col cards

        Args:
            soup: Parsed HTML as BeautifulSoup object.
            url: The source URL for context and pattern matching.

        Returns:
            List of TutorialLink objects with url and title.
        """
        func_name = inspect.currentframe().f_code.co_name
        logger.debug(f" * {func_name} > Extracting tutorial links from: {url}")

        # Get the site configuration for this URL
        config = self._get_site_config(url)
        if not config:
            logger.warning(f"    -> No site config found for URL: {url}")
            logger.warning("    -> Falling back to generic extraction")
            return self._extract_tutorials_generic(soup, url)

        logger.info(f"    -> Using extraction strategy: {config.description}")
        logger.debug(f"    -> Container selector: {config.container_selector}")

        # Find the container element
        container = self._find_container(soup, config.container_selector)
        if not container:
            logger.warning("    -> Container not found, trying full document")
            container = soup

        # Dispatch to the appropriate extraction method based on site type
        if config.site_type == SiteType.SPHINX_TOCTREE:
            tutorials = self._extract_sphinx_toctree(container, url, config.skip_patterns)
        elif config.site_type == SiteType.DOCUSAURUS_CARD_MARGIN:
            tutorials = self._extract_docusaurus_card_margin(container, url)
        elif config.site_type == SiteType.DOCUSAURUS_CARD_COL:
            tutorials = self._extract_docusaurus_card_col(container, url)
        else:
            logger.warning(f"    -> Unknown site type: {config.site_type}")
            tutorials = []

        logger.info(f"    -> Extracted {len(tutorials)} tutorials")
        return tutorials

    def _extract_sphinx_toctree(
        self, container: Tag, base_url: str, skip_patterns: list[str] | None
    ) -> list[TutorialLink]:
        """Extract tutorials from Sphinx toctree structure.

        Parses the Sphinx documentation toctree format:
        <div class="toctree-wrapper compound">
            <ul>
                <li class="toctree-l1">
                    <a class="reference internal" href="Case_01.html">Title</a>
                </li>
            </ul>
        </div>

        Args:
            container: The container element to search within.
            base_url: Base URL for resolving relative links.
            skip_patterns: List of href patterns to skip (e.g., safety_instructions).

        Returns:
            List of TutorialLink objects.
        """
        func_name = inspect.currentframe().f_code.co_name
        logger.debug(f"    * {func_name} > Searching for toctree structure")

        tutorials: list[TutorialLink] = []
        seen_urls: set[str] = set()

        # Find toctree-wrapper divs
        toctree_wrappers = container.find_all("div", class_="toctree-wrapper")
        logger.debug(f"    -> Found {len(toctree_wrappers)} toctree-wrapper elements")

        for toctree in toctree_wrappers:
            # Find top-level list items (toctree-l1)
            list_items = toctree.find_all("li", class_="toctree-l1")
            logger.debug(f"    -> Found {len(list_items)} toctree-l1 items in wrapper")

            for li in list_items:
                # Find the reference link
                link = li.find("a", class_="reference")
                if not link:
                    continue

                # Verify it's an internal reference
                classes = link.get("class", [])
                if "internal" not in classes:
                    logger.debug(f"    -> Skipping non-internal link: {link}")
                    continue

                href = link.get("href", "")
                text = link.get_text(strip=True)

                if not href or not text:
                    logger.debug(f"    -> Skipping empty link: href='{href}', text='{text}'")
                    continue

                # Check skip patterns
                if self._should_skip_href(href, skip_patterns):
                    continue

                # Make URL absolute
                abs_href = self._make_absolute_url(href, base_url)

                # Skip duplicates
                if abs_href in seen_urls:
                    logger.debug(f"    -> Skipping duplicate URL: {abs_href}")
                    continue
                seen_urls.add(abs_href)

                # Clean up title - remove leading number prefix (e.g., "3. Case 01:" -> "Case 01:")
                clean_title = re.sub(r"^\d+\.\s*", "", text).strip()

                tutorials.append(TutorialLink(url=abs_href, title=clean_title))
                logger.debug(f"    -> Found toctree tutorial: {clean_title} -> {abs_href}")

        logger.debug(f"    * {func_name} > Extracted {len(tutorials)} tutorials")
        return tutorials

    def _extract_docusaurus_card_margin(
        self, container: Tag, base_url: str
    ) -> list[TutorialLink]:
        """Extract tutorials from Docusaurus article.margin--md cards.

        Parses the Docusaurus card format with margin--md class:
        <article class="margin--md">
            <a class="card padding--md cardContainer__xxx" href="...">
                <div class="imgWrapper_xxx">
                    <img src="..." alt="" class="img_xxx">
                </div>
                <h2 class="text--truncate cardTitle_xxx" title="Full Title">
                    Display Title
                </h2>
            </a>
        </article>

        Args:
            container: The container element to search within.
            base_url: Base URL for resolving relative links.

        Returns:
            List of TutorialLink objects.
        """
        func_name = inspect.currentframe().f_code.co_name
        logger.debug(f"    * {func_name} > Searching for article.margin--md cards")

        tutorials: list[TutorialLink] = []
        seen_urls: set[str] = set()

        # Find all article elements with margin--md class
        articles = container.find_all("article", class_="margin--md")
        logger.debug(f"    -> Found {len(articles)} article.margin--md elements")

        for article in articles:
            # Find the card link inside the article
            # Match any class containing "card" or "cardContainer"
            card_link = article.find(
                "a", class_=lambda c: c and any("card" in cls.lower() for cls in (c if isinstance(c, list) else [c]))
            )
            if not card_link:
                logger.debug("    -> No card link found in article")
                continue

            href = card_link.get("href", "")
            if not href:
                logger.debug("    -> Card link has no href")
                continue

            # Extract title from h2 with cardTitle class or text--truncate
            title_elem = article.find(
                "h2", class_=lambda c: c and any(
                    "cardTitle" in cls or "text--truncate" in cls
                    for cls in (c if isinstance(c, list) else [c])
                )
            )
            if title_elem:
                # Prefer the title attribute if available (full text without truncation)
                title = title_elem.get("title") or title_elem.get_text(strip=True)
            else:
                title = card_link.get_text(strip=True)

            if not title:
                logger.debug(f"    -> No title found for card link: {href}")
                continue

            # Make URL absolute
            abs_href = self._make_absolute_url(href, base_url)

            # Skip duplicates and current page
            if abs_href in seen_urls or abs_href.rstrip("/") == base_url.rstrip("/"):
                logger.debug(f"    -> Skipping duplicate or current page: {abs_href}")
                continue
            seen_urls.add(abs_href)

            tutorials.append(TutorialLink(url=abs_href, title=title))
            logger.debug(f"    -> Found card tutorial: {title} -> {abs_href}")

        logger.debug(f"    * {func_name} > Extracted {len(tutorials)} tutorials")
        return tutorials

    def _extract_docusaurus_card_col(
        self, container: Tag, base_url: str
    ) -> list[TutorialLink]:
        """Extract tutorials from Docusaurus article.col cards.

        Parses the Docusaurus card format with col classes:
        <article class="col col--6 margin-bottom--lg">
            <a class="card padding--lg cardContainer_xxx" href="...">
                <h2 class="text--truncate cardTitle_xxx" title="Case 01: Title">
                    📄️ Case 01: Title
                </h2>
                <p class="text--truncate cardDescription_xxx" title="Description">
                    Description
                </p>
            </a>
        </article>

        Also handles section wrappers:
        <section>
            <article class="col col--6 ...">...</article>
        </section>

        Args:
            container: The container element to search within.
            base_url: Base URL for resolving relative links.

        Returns:
            List of TutorialLink objects.
        """
        func_name = inspect.currentframe().f_code.co_name
        logger.debug(f"    * {func_name} > Searching for article.col cards")

        tutorials: list[TutorialLink] = []
        seen_urls: set[str] = set()

        # Find all article elements with col class
        # This matches "col", "col--6", etc.
        articles = container.find_all(
            "article", class_=lambda c: c and any(
                cls == "col" or cls.startswith("col--")
                for cls in (c if isinstance(c, list) else [c])
            )
        )
        logger.debug(f"    -> Found {len(articles)} article.col elements")

        for article in articles:
            # Find the card link inside the article
            card_link = article.find(
                "a", class_=lambda c: c and any(
                    "card" in cls.lower()
                    for cls in (c if isinstance(c, list) else [c])
                )
            )
            if not card_link:
                logger.debug("    -> No card link found in article")
                continue

            href = card_link.get("href", "")
            if not href:
                logger.debug("    -> Card link has no href")
                continue

            # Extract title from h2 with cardTitle class
            title_elem = article.find(
                "h2", class_=lambda c: c and any(
                    "cardTitle" in cls or "text--truncate" in cls
                    for cls in (c if isinstance(c, list) else [c])
                )
            )
            if title_elem:
                # Prefer the title attribute if available (full text)
                title = title_elem.get("title") or title_elem.get_text(strip=True)
                # Clean up emojis and extra whitespace from display text
                title = re.sub(r"^[📄️📁🔗\s]+", "", title).strip()
            else:
                title = card_link.get_text(strip=True)
                title = re.sub(r"^[📄️📁🔗\s]+", "", title).strip()

            if not title:
                logger.debug(f"    -> No title found for card link: {href}")
                continue

            # Make URL absolute
            abs_href = self._make_absolute_url(href, base_url)

            # Skip duplicates and current page
            if abs_href in seen_urls or abs_href.rstrip("/") == base_url.rstrip("/"):
                logger.debug(f"    -> Skipping duplicate or current page: {abs_href}")
                continue
            seen_urls.add(abs_href)

            tutorials.append(TutorialLink(url=abs_href, title=title))
            logger.debug(f"    -> Found card tutorial: {title} -> {abs_href}")

        logger.debug(f"    * {func_name} > Extracted {len(tutorials)} tutorials")
        return tutorials

    def _extract_tutorials_generic(
        self, soup: BeautifulSoup, base_url: str
    ) -> list[TutorialLink]:
        """Fallback generic extraction for unknown site types.

        Attempts to find tutorial links using common patterns:
        - Card links with href attributes
        - Links containing "case" or "lesson" in the URL

        Args:
            soup: Parsed HTML as BeautifulSoup object.
            base_url: Base URL for resolving relative links.

        Returns:
            List of TutorialLink objects.
        """
        func_name = inspect.currentframe().f_code.co_name
        logger.debug(f"    * {func_name} > Using generic extraction")

        tutorials: list[TutorialLink] = []
        seen_urls: set[str] = set()

        # Try to find card-style links
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            if not href or not text:
                continue

            # Look for case/lesson patterns
            if not re.search(r"(case|lesson)[_\-\s]?\d+", href, re.IGNORECASE):
                continue

            abs_href = self._make_absolute_url(href, base_url)

            if abs_href in seen_urls:
                continue
            seen_urls.add(abs_href)

            tutorials.append(TutorialLink(url=abs_href, title=text))
            logger.debug(f"    -> Found generic tutorial: {text} -> {abs_href}")

        logger.debug(f"    * {func_name} > Extracted {len(tutorials)} tutorials")
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
