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


async def _fetch_page_once(url: str, timeout: int | None = None) -> str:
    """Single attempt to fetch a page.

    Args:
        url: The URL to fetch.
        timeout: Optional timeout override in milliseconds.

    Returns:
        The fully rendered HTML content of the page.

    Raises:
        PageNotFoundError: If the page returns a 404 status.
        PageTimeoutError: If the page load times out.
        ScrapingError: For other scraping errors.
    """
    effective_timeout = timeout or settings.BROWSER_TIMEOUT

    async with get_browser() as browser:
        page = await browser.new_page()
        logger.debug("    -> Created new page")

        try:
            response = await page.goto(url, timeout=effective_timeout)

            if response is None:
                raise ScrapingError(f"No response received for URL: {url}")

            if response.status == 404:
                raise PageNotFoundError(f"Page not found: {url}")

            if response.status >= 400:
                raise ScrapingError(f"HTTP {response.status} for URL: {url}")

            # Wait for page to fully load (including network idle)
            try:
                await page.wait_for_load_state("networkidle", timeout=effective_timeout)
                logger.debug("    -> Network idle reached")
            except TimeoutError:
                # Fallback to domcontentloaded if networkidle times out
                logger.debug("    -> Network idle timeout, checking DOM")
                await page.wait_for_load_state("domcontentloaded", timeout=effective_timeout)

            # Simple check: ensure body has content
            body_has_content = await page.evaluate("document.body && document.body.innerHTML.length > 100")
            if body_has_content:
                logger.debug("    -> Page has content")
            else:
                logger.warning("    -> Page body appears empty")

            # Small delay for any remaining rendering
            await asyncio.sleep(0.5)
            logger.debug("    -> Page ready")

            content = await page.content()
            logger.debug(f"    -> Retrieved {len(content)} bytes of HTML")

            return content

        except TimeoutError as e:
            error_context = {"url": url, "timeout": effective_timeout}
            logger.debug(f"Page load timeout: {e} | Context: {error_context}")
            raise PageTimeoutError(f"Timeout loading page: {url}") from e

        except Exception as e:
            if isinstance(e, (PageNotFoundError, PageTimeoutError, ScrapingError)):
                raise
            error_context = {"url": url, "error_type": type(e).__name__}
            logger.debug(f"Scraping attempt failed: {e} | Context: {error_context}")
            raise ScrapingError(f"Failed to scrape {url}: {e}") from e


async def fetch_page(url: str) -> str:
    """Fetch and render a web page using Playwright with retry logic.

    Implements exponential backoff retry mechanism for transient failures.
    Non-retryable errors (404, permanent failures) are raised immediately.

    Args:
        url: The URL to fetch.

    Returns:
        The fully rendered HTML content of the page.

    Raises:
        PageNotFoundError: If the page returns a 404 status.
        PageTimeoutError: If all retry attempts fail due to timeout.
        ScrapingError: For other scraping errors after all retries.
    """
    logger.debug(f" * {inspect.currentframe().f_code.co_name} > Fetching: {url}")

    max_retries = settings.SCRAPE_MAX_RETRIES
    retry_delay = settings.SCRAPE_RETRY_DELAY
    backoff = settings.SCRAPE_RETRY_BACKOFF

    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            # Increase timeout for retries
            timeout = settings.BROWSER_TIMEOUT
            if attempt > 0:
                timeout = int(timeout * (1 + attempt * 0.5))  # 50% increase per retry
                logger.info(
                    f"    -> Retry {attempt}/{max_retries} for {url} (timeout: {timeout}ms)"
                )

            return await _fetch_page_once(url, timeout=timeout)

        except PageNotFoundError:
            # Don't retry 404 errors
            raise

        except (PageTimeoutError, ScrapingError) as e:
            last_exception = e

            if attempt < max_retries:
                delay = retry_delay * (backoff**attempt)
                logger.warning(
                    f"    -> Attempt {attempt + 1} failed, retrying in {delay:.1f}s: {e}"
                )
                await asyncio.sleep(delay)
            else:
                error_context = {
                    "url": url,
                    "attempts": attempt + 1,
                    "error_type": type(e).__name__,
                }
                logger.error(
                    f"Scraping failed after {attempt + 1} attempts: {e} | Context: {error_context}"
                )

    # Re-raise the last exception
    if last_exception:
        raise last_exception
    raise ScrapingError(f"Failed to scrape {url} after {max_retries + 1} attempts")


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
