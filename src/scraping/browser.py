"""Playwright browser manager for web scraping.

Provides async context manager for browser lifecycle management,
with built-in rate limiting and retry logic.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.core.config import get_settings
from src.core.errors import PageNotFoundError, PageTimeoutError, ScrapingError

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages Playwright browser for web scraping.

    Provides rate limiting, retry logic, and clean resource management.

    Usage:
        async with BrowserManager() as browser:
            page = await browser.new_page()
            content = await browser.goto_and_get_content(page, url)
    """

    def __init__(
        self,
        headless: Optional[bool] = None,
        timeout: Optional[int] = None,
        delay_seconds: Optional[float] = None,
        retry_count: Optional[int] = None,
    ):
        """Initialize browser manager.

        Args:
            headless: Run browser in headless mode (default from settings)
            timeout: Page load timeout in ms (default from settings)
            delay_seconds: Delay between requests (default from settings)
            retry_count: Number of retry attempts (default from settings)
        """
        settings = get_settings()

        self.headless = headless if headless is not None else settings.BROWSER_HEADLESS
        self.timeout = timeout if timeout is not None else settings.BROWSER_TIMEOUT
        self.delay_seconds = (
            delay_seconds if delay_seconds is not None else settings.SCRAPE_DELAY_SECONDS
        )
        self.retry_count = retry_count if retry_count is not None else settings.SCRAPE_RETRY_COUNT

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._last_request_time: float = 0

    async def __aenter__(self) -> "BrowserManager":
        """Enter async context - launch browser."""
        logger.debug("Launching browser")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        logger.info("Browser launched successfully")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context - close browser."""
        logger.debug("Closing browser")
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser closed")

    async def new_page(self) -> Page:
        """Create a new browser page.

        Returns:
            Playwright Page instance
        """
        if not self._context:
            raise ScrapingError("Browser not initialized - use async with")

        page = await self._context.new_page()
        page.set_default_timeout(self.timeout)
        return page

    async def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        import time

        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.delay_seconds:
            wait_time = self.delay_seconds - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        self._last_request_time = time.time()

    async def goto(
        self,
        page: Page,
        url: str,
        wait_until: str = "networkidle",
    ) -> None:
        """Navigate to URL with rate limiting and retry.

        Args:
            page: Playwright page instance
            url: URL to navigate to
            wait_until: Wait condition (load, domcontentloaded, networkidle)

        Raises:
            PageNotFoundError: If page returns 404
            PageTimeoutError: If page load times out after retries
            ScrapingError: For other navigation errors
        """
        last_error = None

        for attempt in range(self.retry_count + 1):
            try:
                await self._rate_limit()

                logger.debug(f"Navigating to {url} (attempt {attempt + 1}/{self.retry_count + 1})")
                response = await page.goto(url, wait_until=wait_until)

                if response is None:
                    raise ScrapingError(f"No response from {url}")

                if response.status == 404:
                    raise PageNotFoundError(f"Page not found: {url}")

                if not response.ok:
                    raise ScrapingError(
                        f"HTTP {response.status} for {url}: {response.status_text}"
                    )

                logger.debug(f"Successfully loaded {url}")
                return

            except PageNotFoundError:
                raise  # Don't retry 404s

            except Exception as e:
                last_error = e
                if "timeout" in str(e).lower():
                    logger.warning(f"Timeout loading {url} (attempt {attempt + 1})")
                    if attempt == self.retry_count:
                        raise PageTimeoutError(f"Timeout loading {url} after {self.retry_count + 1} attempts") from e
                else:
                    logger.warning(f"Error loading {url}: {e} (attempt {attempt + 1})")

                if attempt < self.retry_count:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        raise ScrapingError(f"Failed to load {url} after {self.retry_count + 1} attempts") from last_error

    async def get_content(self, page: Page) -> str:
        """Get page HTML content.

        Args:
            page: Playwright page instance

        Returns:
            Page HTML content
        """
        return await page.content()

    async def goto_and_get_content(
        self,
        page: Page,
        url: str,
        wait_until: str = "networkidle",
    ) -> str:
        """Navigate to URL and return HTML content.

        Args:
            page: Playwright page instance
            url: URL to navigate to
            wait_until: Wait condition

        Returns:
            Page HTML content
        """
        await self.goto(page, url, wait_until)
        return await self.get_content(page)

    async def wait_for_selector(
        self,
        page: Page,
        selector: str,
        timeout: Optional[int] = None,
    ) -> None:
        """Wait for element to appear on page.

        Args:
            page: Playwright page instance
            selector: CSS selector to wait for
            timeout: Timeout in ms (default from settings)
        """
        timeout = timeout or self.timeout
        await page.wait_for_selector(selector, timeout=timeout)

    async def extract_text(self, page: Page, selector: str) -> Optional[str]:
        """Extract text content from element.

        Args:
            page: Playwright page instance
            selector: CSS selector

        Returns:
            Text content or None if not found
        """
        element = await page.query_selector(selector)
        if element:
            return await element.text_content()
        return None

    async def extract_attribute(
        self,
        page: Page,
        selector: str,
        attribute: str,
    ) -> Optional[str]:
        """Extract attribute value from element.

        Args:
            page: Playwright page instance
            selector: CSS selector
            attribute: Attribute name to extract

        Returns:
            Attribute value or None if not found
        """
        element = await page.query_selector(selector)
        if element:
            return await element.get_attribute(attribute)
        return None

    async def extract_all_links(
        self,
        page: Page,
        selector: str = "a",
    ) -> list[str]:
        """Extract all href values from matching elements.

        Args:
            page: Playwright page instance
            selector: CSS selector for link elements

        Returns:
            List of href values
        """
        elements = await page.query_selector_all(selector)
        hrefs = []
        for element in elements:
            href = await element.get_attribute("href")
            if href:
                hrefs.append(href)
        return hrefs


@asynccontextmanager
async def create_browser(**kwargs) -> AsyncIterator[BrowserManager]:
    """Convenience function to create browser manager as context manager.

    Args:
        **kwargs: Arguments passed to BrowserManager

    Yields:
        BrowserManager instance
    """
    async with BrowserManager(**kwargs) as browser:
        yield browser
