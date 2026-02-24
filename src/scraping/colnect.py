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

# Theme name to ID mapping - Colnect uses numeric IDs
# URL pattern: /en/stamps/list/theme/ID-Theme_Name
SPACE_THEMES = {
    "Space": "2938-Outer_Space",          # Outer Space theme
    "Space Traveling": "144-Space_Traveling",
    "Astronomy": "330-Astronomy",
    "Rockets": "1627-Rockets",
    "Satellites": "1640-Satellites",
    "Scientists": "175-Scientists",
}

# Country name to ID mapping for common countries
# URL pattern: /en/stamps/list/country/ID-Country_Name/theme/ID-Theme_Name
COUNTRY_IDS = {
    "Ascension Island": "253-Ascension_Island",
    "Australia": "12-Australia",
    "Austria": "13-Austria",
    "Belgium": "17-Belgium",
    "Canada": "38-Canada",
    "China": "43-China",
    "France": "73-France",
    "Germany": "79-Germany",
    "India": "97-India",
    "Italy": "102-Italy",
    "Japan": "105-Japan",
    "Netherlands": "147-Netherlands",
    "New Zealand": "149-New_Zealand",
    "Russia": "175-Russia",
    "South Africa": "197-South_Africa",
    "Spain": "199-Spain",
    "Switzerland": "207-Switzerland",
    "United Kingdom": "75-Great_Britain",
    "United States": "225-United_States",
    "USSR": "223-USSR",
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

    def get_theme_url(
        self,
        theme_slug: str,
        page: int = 1,
        country_slug: Optional[str] = None,
        year: Optional[int] = None,
    ) -> str:
        """Get URL for theme listing page, optionally filtered by country and year.

        Args:
            theme_slug: Theme identifier (e.g., '1627-Rockets', '330-Astronomy')
            page: Page number (1-indexed)
            country_slug: Optional country identifier (e.g., '253-Ascension_Island')
            year: Optional year filter (e.g., 1971)

        Returns:
            Full URL for theme listing
        """
        # Build URL with filters
        # Pattern: /en/stamps/list/country/ID-Country/theme/ID-Theme/year/YYYY
        parts = [COLNECT_STAMPS_URL, "list"]

        if country_slug:
            parts.extend(["country", country_slug])

        parts.extend(["theme", theme_slug])

        if year:
            parts.extend(["year", str(year)])

        base = "/".join(parts)

        if page > 1:
            return f"{base}/page/{page}"
        return base

    async def get_theme_stamp_urls(
        self,
        page: Page,
        theme_slug: str,
        page_number: int = 1,
        country_slug: Optional[str] = None,
        year: Optional[int] = None,
    ) -> tuple[list[str], bool]:
        """Get stamp URLs from a theme listing page.

        Args:
            page: Playwright page instance
            theme_slug: Theme identifier
            page_number: Page number
            country_slug: Optional country identifier for filtering
            year: Optional year for filtering

        Returns:
            Tuple of (list of stamp URLs, has_next_page)
        """
        url = self.get_theme_url(theme_slug, page_number, country_slug, year)
        logger.debug(f"Fetching stamp list from: {url}")
        content = await self._browser.goto_and_get_content(page, url)
        soup = BeautifulSoup(content, "html.parser")

        # Extract stamp links - pattern: /en/stamps/stamp/ID-Slug
        # Skip fragment links (e.g., #minorvariants) as they're not separate pages
        stamp_links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "/stamps/stamp/" in href and "#" not in href:
                full_url = urljoin(COLNECT_BASE_URL, href)
                if full_url not in stamp_links:
                    stamp_links.append(full_url)

        # Check for next page - Colnect uses various pagination patterns
        has_next = False

        # Method 1: Look for "page/N" links where N > current page
        next_page_pattern = f"/page/{page_number + 1}"
        for link in soup.find_all("a", href=True):
            if next_page_pattern in link["href"]:
                has_next = True
                break

        # Method 2: Look for pagination container with next link
        if not has_next:
            pagination = soup.find("ul", class_="pagination") or soup.find("div", class_="pagination")
            if pagination:
                for link in pagination.find_all("a", href=True):
                    href = link["href"]
                    if f"/page/{page_number + 1}" in href or ">>" in link.get_text():
                        has_next = True
                        break

        logger.info(f"Found {len(stamp_links)} stamps on {theme_slug} page {page_number} (has_next={has_next})")
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
        # Navigate and wait for dynamic content to load
        await self._browser.goto(page, url)

        # Wait for JavaScript to populate the obfuscated content
        # Colnect uses placeholders like "ColnectIsBest" that get replaced by JS
        try:
            await page.wait_for_function(
                "!document.body.innerText.includes('ColnectIsBest')",
                timeout=5000
            )
        except Exception:
            # Timeout is OK - some pages might not have this placeholder
            pass

        content = await self._browser.get_content(page)
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

            # Extract country (pass URL for fallback extraction)
            country = self._extract_country(soup, url)

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

    def _extract_country(self, soup: BeautifulSoup, url: str = "") -> str:
        """Extract issuing country from page."""
        # Method 1: Extract from URL - MOST reliable for Colnect URLs
        # URL format: /stamp/ID-Title-Series-Country (with underscores)
        # Example: /stamp/324257-First_Manned_Flight-Man_In_Space_Issue-Ascension_Island
        if url and "/stamp/" in url:
            parts = url.rstrip("/").split("-")
            if len(parts) >= 2:
                # Last part is always country with underscores
                country = parts[-1].replace("_", " ")
                if country and len(country) > 2:
                    logger.debug(f"Extracted country from URL: {country}")
                    return country

        # Method 2: Look for country link with /list/country/ pattern
        # This is specific to the country field in Colnect
        country_link = soup.find("a", href=re.compile(r"/list/country/\d+"))
        if country_link:
            country = country_link.get_text(strip=True)
            logger.debug(f"Extracted country from link: {country}")
            return country

        # Method 3: Look for "Country:" row in metadata table
        for row in soup.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                label = th.get_text(strip=True).lower().strip()
                if label in ["country:", "country"]:
                    link = td.find("a")
                    if link:
                        return link.get_text(strip=True)
                    return td.get_text(strip=True)

        raise ExtractionError("Cannot extract country")

    def _extract_year(self, soup: BeautifulSoup) -> int:
        """Extract year of issue from page."""
        # Method 1: Look for "Issued on:" row specifically (most reliable for Colnect)
        # The date is often a link like <a href="...">1971-02-15</a>
        for row in soup.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                label = th.get_text(strip=True).lower()
                if "issued" in label:
                    # Try link text first (Colnect puts date in a link)
                    link = td.find("a")
                    if link:
                        text = link.get_text(strip=True)
                        match = re.search(r"(19|20)\d{2}", text)
                        if match:
                            return int(match.group())
                    # Fall back to full td text
                    text = td.get_text(strip=True)
                    match = re.search(r"(19|20)\d{2}", text)
                    if match:
                        return int(match.group())

        # Method 2: Look for other date-related rows
        for row in soup.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                label = th.get_text(strip=True).lower()
                if any(x in label for x in ["year", "date", "release"]):
                    text = td.get_text(strip=True)
                    match = re.search(r"(19|20)\d{2}", text)
                    if match:
                        return int(match.group())

        # Method 3: Look for date links anywhere on the page
        # Colnect links dates to list pages: /list/year/1971
        for link in soup.find_all("a", href=re.compile(r"/list/year/")):
            text = link.get_text(strip=True)
            match = re.search(r"(19|20)\d{2}", text)
            if match:
                return int(match.group())

        # Method 4: Search entire page for date patterns
        text = soup.get_text()
        patterns = [
            r"issued\s+on[:\s]+(\d{4})",
            r"issue\s+date[:\s]+(\d{4})",
            r"year\s+of\s+issue[:\s]+(\d{4})",
            r"(\d{4})-\d{2}-\d{2}",  # ISO date format
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year_str = match.group(1) if match.lastindex else match.group()
                year = int(year_str[:4])
                if 1840 <= year <= 2030:
                    return year

        raise ExtractionError("Cannot extract year")

    def _extract_image_url(self, soup: BeautifulSoup) -> str:
        """Extract main stamp image URL from page."""
        # Method 1: Look for main stamp image by class/id
        for selector in ["item_image", "item_photo", "stamp_image", "main_image"]:
            img = soup.find("img", class_=selector) or soup.find("img", id=selector)
            if img:
                # Try various attributes for the actual URL
                for attr in ["src", "data-src", "data-lazy-src", "data-original"]:
                    url = img.get(attr)
                    if url and not url.startswith("data:"):  # Skip data URIs
                        return urljoin(COLNECT_BASE_URL, url)

        # Method 2: Look in figure or image container
        for container_class in ["item_photo", "photo", "stamp_photo", "main_photo"]:
            container = soup.find("figure", class_=container_class) or soup.find("div", class_=container_class)
            if container:
                img = container.find("img")
                if img:
                    for attr in ["src", "data-src", "data-lazy-src", "data-original"]:
                        url = img.get(attr)
                        if url and not url.startswith("data:"):
                            return urljoin(COLNECT_BASE_URL, url)

        # Method 3: Find any large image (likely the main stamp image)
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src and not src.startswith("data:"):
                # Look for image URLs that seem like stamp images
                if any(x in src.lower() for x in ["stamp", "image", "photo", "/i/"]):
                    return urljoin(COLNECT_BASE_URL, src)

        # Method 4: Look for og:image meta tag
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"]

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
        dry_run: bool = False,
        limit: Optional[int] = None,
    ) -> int:
        """Scrape stamps from specified themes.

        Args:
            themes: List of theme names (default from settings)
            resume: Resume from checkpoint if available
            country_filter: Only scrape stamps from this country
            year_filter: Only scrape stamps from this year
            progress_callback: Called with (count, message) for progress updates
            dry_run: If True, display data but don't save to database
            limit: Maximum number of stamps to scrape

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

        # Resolve country filter to Colnect country slug
        country_slug = None
        if country_filter:
            country_slug = COUNTRY_IDS.get(country_filter)
            if not country_slug:
                # Try to construct slug from country name
                country_slug = country_filter.replace(" ", "_")
                # If it looks like it already has an ID (e.g., "253-Ascension_Island"), use as-is
                if not country_slug[0].isdigit():
                    logger.warning(
                        f"Country '{country_filter}' not in COUNTRY_IDS mapping. "
                        f"Using '{country_slug}' - this may not work. "
                        f"Consider adding the country ID to COUNTRY_IDS."
                    )

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
                    # Get stamp URLs from listing page (with country/year filters in URL if specified)
                    try:
                        stamp_urls, has_next = await self.get_theme_stamp_urls(
                            page, theme_slug, page_number, country_slug, year_filter
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

                            # Verify year matches (fallback check - URL filtering may not be exact)
                            if year_filter and stamp.year != year_filter:
                                processed_urls.add(url)  # Mark as processed to avoid re-scraping
                                continue

                            if dry_run:
                                # Display stamp data without saving
                                logger.info(
                                    f"[DRY RUN] Stamp: {stamp.colnect_id}\n"
                                    f"  Title: {stamp.title}\n"
                                    f"  Country: {stamp.country}\n"
                                    f"  Year: {stamp.year}\n"
                                    f"  Image: {stamp.image_url}\n"
                                    f"  Themes: {', '.join(stamp.themes)}\n"
                                    f"  Catalog: {stamp.catalog_codes}"
                                )
                            else:
                                # Save to database
                                upsert_catalog_stamp(stamp)

                            total_scraped += 1
                            processed_urls.add(url)

                            if progress_callback:
                                progress_callback(total_scraped, f"Scraped: {stamp.title[:50]}")

                            # Check limit
                            if limit and total_scraped >= limit:
                                logger.info(f"Reached limit of {limit} stamps")
                                return total_scraped

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
