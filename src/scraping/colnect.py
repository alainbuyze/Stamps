"""Colnect stamp catalog scraper.

Scrapes stamp data from Colnect website including:
- Theme-based stamp discovery
- Individual stamp page extraction
- Catalog codes (Michel, Scott, Yvert, SG, Fisher)
- Checkpoint/resume support for long scraping sessions
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.async_api import Page

from src.core.config import get_settings
from src.core.database import CatalogStamp, upsert_catalog_stamp
from src.core.errors import ExtractionError, ScrapingError
from src.scraping.browser import BrowserManager

logger = logging.getLogger(__name__)


# =============================================================================
# Colnect URL Patterns
# =============================================================================

COLNECT_BASE_URL = "https://colnect.com"
COLNECT_STAMPS_URL = f"{COLNECT_BASE_URL}/en/stamps"

# Theme name to ID mapping (will be populated dynamically or use known IDs)
# These are the space-related theme IDs on Colnect
SPACE_THEMES = {
    "Space": "space",
    "Space Traveling": "space_traveling",
    "Astronomy": "astronomy",
    "Rockets": "rockets",
    "Satellites": "satellites",
    "Scientists": "scientists",
}


@dataclass
class ScrapeCheckpoint:
    """Checkpoint for resuming interrupted scrapes."""

    theme: str
    page_number: int
    processed_urls: list[str] = field(default_factory=list)
    total_scraped: int = 0
    last_updated: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "theme": self.theme,
            "page_number": self.page_number,
            "processed_urls": self.processed_urls,
            "total_scraped": self.total_scraped,
            "last_updated": self.last_updated or datetime.now().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScrapeCheckpoint":
        """Create from dictionary."""
        return cls(
            theme=data.get("theme", ""),
            page_number=data.get("page_number", 1),
            processed_urls=data.get("processed_urls", []),
            total_scraped=data.get("total_scraped", 0),
            last_updated=data.get("last_updated", ""),
        )


class ColnectScraper:
    """Scrapes stamp data from Colnect catalog.

    Features:
    - Theme-based discovery of stamps
    - Individual stamp page extraction
    - Checkpoint/resume for long sessions
    - Rate limiting and retry logic (via BrowserManager)

    Usage:
        async with ColnectScraper() as scraper:
            count = await scraper.scrape_themes(["Space", "Astronomy"])
    """

    def __init__(
        self,
        browser: Optional[BrowserManager] = None,
        checkpoint_file: Optional[Path] = None,
    ):
        """Initialize scraper.

        Args:
            browser: Browser manager instance (created if not provided)
            checkpoint_file: Path to checkpoint file for resume support
        """
        settings = get_settings()
        self._browser = browser
        self._owns_browser = browser is None
        self.checkpoint_file = checkpoint_file or Path(settings.SCRAPE_CHECKPOINT_FILE)
        self.checkpoint: Optional[ScrapeCheckpoint] = None

    async def __aenter__(self) -> "ColnectScraper":
        """Enter async context."""
        if self._owns_browser:
            self._browser = BrowserManager()
            await self._browser.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        if self._owns_browser and self._browser:
            await self._browser.__aexit__(exc_type, exc_val, exc_tb)

    # =========================================================================
    # Checkpoint Management
    # =========================================================================

    def load_checkpoint(self) -> Optional[ScrapeCheckpoint]:
        """Load checkpoint from file if exists."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, "r") as f:
                    data = json.load(f)
                self.checkpoint = ScrapeCheckpoint.from_dict(data)
                logger.info(f"Loaded checkpoint: theme={self.checkpoint.theme}, page={self.checkpoint.page_number}")
                return self.checkpoint
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
        return None

    def save_checkpoint(self, checkpoint: ScrapeCheckpoint) -> None:
        """Save checkpoint to file."""
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.last_updated = datetime.now().isoformat()
        with open(self.checkpoint_file, "w") as f:
            json.dump(checkpoint.to_dict(), f, indent=2)
        logger.debug(f"Saved checkpoint: {checkpoint.theme} page {checkpoint.page_number}")

    def clear_checkpoint(self) -> None:
        """Clear checkpoint file."""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
            logger.info("Cleared checkpoint file")

    # =========================================================================
    # Theme Discovery
    # =========================================================================

    def get_theme_url(self, theme_slug: str, page: int = 1) -> str:
        """Get URL for theme listing page.

        Args:
            theme_slug: Theme identifier (e.g., 'space', 'astronomy')
            page: Page number (1-indexed)

        Returns:
            Full URL for theme listing
        """
        # Colnect uses different URL patterns for themes
        # Example: /en/stamps/list/theme/space/page/2
        base = f"{COLNECT_STAMPS_URL}/list/theme/{theme_slug}"
        if page > 1:
            return f"{base}/page/{page}"
        return base

    async def get_theme_stamp_urls(
        self,
        page: Page,
        theme_slug: str,
        page_number: int = 1,
    ) -> tuple[list[str], bool]:
        """Get stamp URLs from a theme listing page.

        Args:
            page: Playwright page instance
            theme_slug: Theme identifier
            page_number: Page number

        Returns:
            Tuple of (list of stamp URLs, has_next_page)
        """
        url = self.get_theme_url(theme_slug, page_number)
        content = await self._browser.goto_and_get_content(page, url)
        soup = BeautifulSoup(content, "html.parser")

        # Extract stamp links - they typically follow pattern /en/stamps/stamp/ID-Slug
        stamp_links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "/stamps/stamp/" in href:
                full_url = urljoin(COLNECT_BASE_URL, href)
                if full_url not in stamp_links:
                    stamp_links.append(full_url)

        # Check for next page
        has_next = False
        pagination = soup.find("div", class_="pagination") or soup.find("nav", class_="pagination")
        if pagination:
            next_link = pagination.find("a", text=re.compile(r"Next|>|»"))
            has_next = next_link is not None

        logger.debug(f"Found {len(stamp_links)} stamps on {theme_slug} page {page_number}")
        return stamp_links, has_next

    # =========================================================================
    # Stamp Page Extraction
    # =========================================================================

    async def scrape_stamp_page(self, page: Page, url: str) -> CatalogStamp:
        """Scrape individual stamp page.

        Args:
            page: Playwright page instance
            url: Stamp page URL

        Returns:
            CatalogStamp with extracted data

        Raises:
            ExtractionError: If required data cannot be extracted
        """
        content = await self._browser.goto_and_get_content(page, url)
        soup = BeautifulSoup(content, "html.parser")

        try:
            # Extract Colnect ID from URL
            # Format: /en/stamps/stamp/123456-Stamp_Title
            match = re.search(r"/stamp/(\d+)", url)
            if not match:
                raise ExtractionError(f"Cannot extract stamp ID from URL: {url}")
            colnect_id = match.group(1)

            # Extract title - usually in h1 or specific element
            title = self._extract_title(soup)

            # Extract country
            country = self._extract_country(soup)

            # Extract year
            year = self._extract_year(soup)

            # Extract image URL
            image_url = self._extract_image_url(soup)

            # Extract themes
            themes = self._extract_themes(soup)

            # Extract catalog codes
            catalog_codes = self._extract_catalog_codes(soup)

            stamp = CatalogStamp(
                colnect_id=colnect_id,
                colnect_url=url,
                title=title,
                country=country,
                year=year,
                image_url=image_url,
                themes=themes,
                catalog_codes=catalog_codes,
                scraped_at=datetime.now(),
            )

            logger.debug(f"Scraped stamp: {colnect_id} - {title}")
            return stamp

        except ExtractionError:
            raise
        except Exception as e:
            raise ExtractionError(f"Failed to extract stamp data from {url}: {e}") from e

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract stamp title from page."""
        # Try common title patterns
        title_elem = (
            soup.find("h1", class_="item_name")
            or soup.find("h1")
            or soup.find("span", class_="item_name")
        )
        if title_elem:
            return title_elem.get_text(strip=True)

        # Fallback to page title
        if soup.title:
            return soup.title.get_text(strip=True).split("|")[0].strip()

        raise ExtractionError("Cannot extract title")

    def _extract_country(self, soup: BeautifulSoup) -> str:
        """Extract issuing country from page."""
        # Look for country in metadata or breadcrumb
        country_elem = soup.find("a", href=re.compile(r"/stamps/country/"))
        if country_elem:
            return country_elem.get_text(strip=True)

        # Try metadata table
        for row in soup.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                label = th.get_text(strip=True).lower()
                if "country" in label or "issuer" in label:
                    return td.get_text(strip=True)

        raise ExtractionError("Cannot extract country")

    def _extract_year(self, soup: BeautifulSoup) -> int:
        """Extract year of issue from page."""
        # Look for year in metadata
        for row in soup.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                label = th.get_text(strip=True).lower()
                if "year" in label or "issued" in label:
                    text = td.get_text(strip=True)
                    match = re.search(r"\b(19|20)\d{2}\b", text)
                    if match:
                        return int(match.group())

        # Try to find year in page content
        text = soup.get_text()
        # Look for "Issue Year: YYYY" or similar patterns
        match = re.search(r"(?:year|issued)[:\s]+(\d{4})", text, re.IGNORECASE)
        if match:
            return int(match.group(1))

        raise ExtractionError("Cannot extract year")

    def _extract_image_url(self, soup: BeautifulSoup) -> str:
        """Extract main stamp image URL from page."""
        # Look for main stamp image
        img = soup.find("img", class_="item_image") or soup.find("img", id="item_image")
        if img and img.get("src"):
            return urljoin(COLNECT_BASE_URL, img["src"])

        # Try data-src for lazy loaded images
        if img and img.get("data-src"):
            return urljoin(COLNECT_BASE_URL, img["data-src"])

        # Look in figure or main image container
        figure = soup.find("figure", class_="item_photo") or soup.find("div", class_="item_photo")
        if figure:
            img = figure.find("img")
            if img:
                src = img.get("src") or img.get("data-src")
                if src:
                    return urljoin(COLNECT_BASE_URL, src)

        raise ExtractionError("Cannot extract image URL")

    def _extract_themes(self, soup: BeautifulSoup) -> list[str]:
        """Extract themes/topics from page."""
        themes = []

        # Look for theme links
        for link in soup.find_all("a", href=re.compile(r"/stamps/.*theme")):
            theme = link.get_text(strip=True)
            if theme and theme not in themes:
                themes.append(theme)

        # Try metadata table
        for row in soup.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                label = th.get_text(strip=True).lower()
                if "theme" in label or "topic" in label:
                    for link in td.find_all("a"):
                        theme = link.get_text(strip=True)
                        if theme and theme not in themes:
                            themes.append(theme)

        return themes

    def _extract_catalog_codes(self, soup: BeautifulSoup) -> dict[str, str]:
        """Extract catalog codes (Michel, Scott, Yvert, etc.) from page."""
        codes = {}
        catalog_names = {
            "michel": "michel",
            "scott": "scott",
            "yvert": "yvert",
            "gibbons": "sg",
            "sg": "sg",
            "stanley gibbons": "sg",
            "fisher": "fisher",
        }

        # Look in metadata table
        for row in soup.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                label = th.get_text(strip=True).lower()
                for catalog_key, code_key in catalog_names.items():
                    if catalog_key in label:
                        value = td.get_text(strip=True)
                        if value and value != "-" and value.lower() != "n/a":
                            codes[code_key] = value
                        break

        return codes

    # =========================================================================
    # Main Scraping Methods
    # =========================================================================

    async def scrape_themes(
        self,
        themes: Optional[list[str]] = None,
        resume: bool = False,
        country_filter: Optional[str] = None,
        year_filter: Optional[int] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> int:
        """Scrape stamps from specified themes.

        Args:
            themes: List of theme names (default from settings)
            resume: Resume from checkpoint if available
            country_filter: Only scrape stamps from this country
            year_filter: Only scrape stamps from this year
            progress_callback: Called with (count, message) for progress updates

        Returns:
            Number of stamps scraped
        """
        settings = get_settings()
        if themes is None:
            themes = settings.themes_list

        total_scraped = 0
        start_theme_idx = 0
        start_page = 1
        processed_urls: set[str] = set()

        # Load checkpoint if resuming
        if resume:
            checkpoint = self.load_checkpoint()
            if checkpoint:
                try:
                    start_theme_idx = themes.index(checkpoint.theme)
                    start_page = checkpoint.page_number
                    processed_urls = set(checkpoint.processed_urls)
                    total_scraped = checkpoint.total_scraped
                    logger.info(f"Resuming from {checkpoint.theme} page {start_page}")
                except ValueError:
                    logger.warning(f"Checkpoint theme '{checkpoint.theme}' not in theme list")

        page = await self._browser.new_page()

        try:
            for theme_idx, theme in enumerate(themes[start_theme_idx:], start_theme_idx):
                theme_slug = SPACE_THEMES.get(theme, theme.lower().replace(" ", "_"))
                page_number = start_page if theme_idx == start_theme_idx else 1

                logger.info(f"Scraping theme: {theme}")

                while True:
                    # Get stamp URLs from listing page
                    try:
                        stamp_urls, has_next = await self.get_theme_stamp_urls(
                            page, theme_slug, page_number
                        )
                    except Exception as e:
                        logger.error(f"Failed to get theme page {theme} #{page_number}: {e}")
                        break

                    # Scrape each stamp
                    for url in stamp_urls:
                        if url in processed_urls:
                            continue

                        try:
                            stamp = await self.scrape_stamp_page(page, url)

                            # Apply filters
                            if country_filter and stamp.country != country_filter:
                                continue
                            if year_filter and stamp.year != year_filter:
                                continue

                            # Save to database
                            upsert_catalog_stamp(stamp)
                            total_scraped += 1
                            processed_urls.add(url)

                            if progress_callback:
                                progress_callback(total_scraped, f"Scraped: {stamp.title[:50]}")

                        except ExtractionError as e:
                            logger.warning(f"Extraction failed for {url}: {e}")
                            settings = get_settings()
                            if settings.SCRAPE_ERROR_BEHAVIOR == "abort":
                                raise
                        except Exception as e:
                            logger.error(f"Error scraping {url}: {e}")
                            settings = get_settings()
                            if settings.SCRAPE_ERROR_BEHAVIOR == "abort":
                                raise

                    # Save checkpoint after each page
                    self.save_checkpoint(ScrapeCheckpoint(
                        theme=theme,
                        page_number=page_number + 1,
                        processed_urls=list(processed_urls),
                        total_scraped=total_scraped,
                    ))

                    if not has_next:
                        break

                    page_number += 1

                # Reset start page for subsequent themes
                start_page = 1

        finally:
            await page.close()

        # Clear checkpoint on successful completion
        self.clear_checkpoint()

        logger.info(f"Scraping complete: {total_scraped} stamps")
        return total_scraped

    async def scrape_single(self, url: str) -> CatalogStamp:
        """Scrape a single stamp page.

        Args:
            url: Stamp page URL

        Returns:
            CatalogStamp with extracted data
        """
        page = await self._browser.new_page()
        try:
            return await self.scrape_stamp_page(page, url)
        finally:
            await page.close()
