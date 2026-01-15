"""Playwright-based page scraper for fetching web content."""

import asyncio
import inspect
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from playwright.async_api import Browser, async_playwright

from src.core.config import get_settings
from src.core.errors import PageNotFoundError, PageTimeoutError, ScrapingError

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_browser() -> AsyncGenerator[Browser, None]:
    """Context manager for Playwright browser.

    Yields:
        Browser instance configured per settings.
    """
    logger.debug(f" * {inspect.currentframe().f_code.co_name} > Starting browser")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=settings.BROWSER_HEADLESS)
        logger.debug("    -> Browser launched successfully")
        try:
            yield browser
        finally:
            await browser.close()
            logger.debug("    -> Browser closed")


async def fetch_page(url: str) -> str:
    """Fetch and render a web page using Playwright.

    Args:
        url: The URL to fetch.

    Returns:
        The fully rendered HTML content of the page.

    Raises:
        PageNotFoundError: If the page returns a 404 status.
        PageTimeoutError: If the page load times out.
        ScrapingError: For other scraping errors.
    """
    logger.debug(f" * {inspect.currentframe().f_code.co_name} > Fetching: {url}")

    async with get_browser() as browser:
        page = await browser.new_page()
        logger.debug("    -> Created new page")

        try:
            response = await page.goto(url, timeout=settings.BROWSER_TIMEOUT)

            if response is None:
                raise ScrapingError(f"No response received for URL: {url}")

            if response.status == 404:
                raise PageNotFoundError(f"Page not found: {url}")

            if response.status >= 400:
                raise ScrapingError(f"HTTP {response.status} for URL: {url}")

            # Wait for content to load
            await page.wait_for_load_state("networkidle")
            logger.debug("    -> Page loaded, network idle")

            content = await page.content()
            logger.debug(f"    -> Retrieved {len(content)} bytes of HTML")

            return content

        except TimeoutError as e:
            error_context = {"url": url, "timeout": settings.BROWSER_TIMEOUT}
            logger.error(f"Page load timeout: {e} | Context: {error_context}")
            raise PageTimeoutError(f"Timeout loading page: {url}") from e

        except Exception as e:
            if isinstance(e, (PageNotFoundError, PageTimeoutError, ScrapingError)):
                raise
            error_context = {"url": url, "error_type": type(e).__name__}
            logger.error(f"Scraping failed: {e} | Context: {error_context}")
            raise ScrapingError(f"Failed to scrape {url}: {e}") from e


async def rate_limited_fetch(url: str) -> str:
    """Fetch a page with rate limiting.

    Adds a delay after fetching to respect rate limits.

    Args:
        url: The URL to fetch.

    Returns:
        The fully rendered HTML content of the page.
    """
    content = await fetch_page(url)

    # Apply rate limiting
    if settings.RATE_LIMIT_SECONDS > 0:
        logger.debug(f"    -> Rate limiting: waiting {settings.RATE_LIMIT_SECONDS}s")
        await asyncio.sleep(settings.RATE_LIMIT_SECONDS)

    return content
