"""Tests for browser manager."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.scraping.browser import BrowserManager
from src.core.errors import PageNotFoundError, PageTimeoutError, ScrapingError


class TestBrowserManagerInit:
    """Tests for BrowserManager initialization."""

    def test_default_settings(self):
        """Test that default settings are loaded from config."""
        browser = BrowserManager()
        assert browser.headless is True
        assert browser.timeout > 0
        assert browser.delay_seconds > 0
        assert browser.retry_count > 0

    def test_custom_settings(self):
        """Test that custom settings override defaults."""
        browser = BrowserManager(
            headless=False,
            timeout=5000,
            delay_seconds=2.0,
            retry_count=5,
        )
        assert browser.headless is False
        assert browser.timeout == 5000
        assert browser.delay_seconds == 2.0
        assert browser.retry_count == 5

    def test_initial_state(self):
        """Test initial state before context entry."""
        browser = BrowserManager()
        assert browser._playwright is None
        assert browser._browser is None
        assert browser._context is None


class TestBrowserManagerRateLimiting:
    """Tests for rate limiting logic."""

    @pytest.mark.asyncio
    async def test_rate_limit_applies_delay(self):
        """Test that rate limiting waits between requests."""
        import time

        browser = BrowserManager(delay_seconds=0.5)
        browser._last_request_time = time.time()

        start = time.time()
        await browser._rate_limit()
        elapsed = time.time() - start

        # Should have waited close to 0.5 seconds
        assert elapsed >= 0.4

    @pytest.mark.asyncio
    async def test_rate_limit_no_delay_first_request(self):
        """Test that first request has no delay."""
        import time

        browser = BrowserManager(delay_seconds=1.0)
        browser._last_request_time = 0  # Long ago

        start = time.time()
        await browser._rate_limit()
        elapsed = time.time() - start

        # Should not have waited
        assert elapsed < 0.1


class TestBrowserManagerNewPage:
    """Tests for new_page method."""

    @pytest.mark.asyncio
    async def test_new_page_requires_context(self):
        """Test that new_page fails without context."""
        browser = BrowserManager()

        with pytest.raises(ScrapingError, match="not initialized"):
            await browser.new_page()


class TestBrowserManagerGoto:
    """Tests for goto method with mocked playwright."""

    @pytest.mark.asyncio
    async def test_goto_success(self):
        """Test successful page navigation."""
        browser = BrowserManager(retry_count=0)
        browser._last_request_time = 0

        # Mock page and response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.ok = True

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(return_value=mock_response)

        await browser.goto(mock_page, "https://example.com")
        mock_page.goto.assert_called_once()

    @pytest.mark.asyncio
    async def test_goto_404_raises_page_not_found(self):
        """Test that 404 response raises PageNotFoundError."""
        browser = BrowserManager(retry_count=0)
        browser._last_request_time = 0

        mock_response = MagicMock()
        mock_response.status = 404

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(return_value=mock_response)

        with pytest.raises(PageNotFoundError):
            await browser.goto(mock_page, "https://example.com/notfound")

    @pytest.mark.asyncio
    async def test_goto_retries_on_error(self):
        """Test that goto retries on transient errors."""
        browser = BrowserManager(retry_count=2, delay_seconds=0)
        browser._last_request_time = 0

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.ok = True

        mock_page = AsyncMock()
        # Fail twice, then succeed
        mock_page.goto = AsyncMock(
            side_effect=[Exception("Network error"), Exception("Network error"), mock_response]
        )

        await browser.goto(mock_page, "https://example.com")
        assert mock_page.goto.call_count == 3


class TestBrowserManagerExtraction:
    """Tests for extraction helper methods."""

    @pytest.mark.asyncio
    async def test_extract_text_found(self):
        """Test extracting text from existing element."""
        browser = BrowserManager()

        mock_element = AsyncMock()
        mock_element.text_content = AsyncMock(return_value="Hello World")

        mock_page = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        result = await browser.extract_text(mock_page, "h1")
        assert result == "Hello World"

    @pytest.mark.asyncio
    async def test_extract_text_not_found(self):
        """Test extracting text from non-existent element."""
        browser = BrowserManager()

        mock_page = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=None)

        result = await browser.extract_text(mock_page, "h1")
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_attribute(self):
        """Test extracting attribute from element."""
        browser = BrowserManager()

        mock_element = AsyncMock()
        mock_element.get_attribute = AsyncMock(return_value="https://example.com/img.jpg")

        mock_page = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        result = await browser.extract_attribute(mock_page, "img", "src")
        assert result == "https://example.com/img.jpg"

    @pytest.mark.asyncio
    async def test_extract_all_links(self):
        """Test extracting multiple links."""
        browser = BrowserManager()

        mock_elements = [
            AsyncMock(get_attribute=AsyncMock(return_value="/page1")),
            AsyncMock(get_attribute=AsyncMock(return_value="/page2")),
            AsyncMock(get_attribute=AsyncMock(return_value=None)),  # No href
        ]

        mock_page = AsyncMock()
        mock_page.query_selector_all = AsyncMock(return_value=mock_elements)

        result = await browser.extract_all_links(mock_page, "a")
        assert result == ["/page1", "/page2"]
