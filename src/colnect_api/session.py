"""Chrome DevTools Protocol session manager for Colnect automation.

Goal
----
Connect to an existing Chrome browser session via CDP (Chrome DevTools Protocol)
to automate Colnect collection operations. This allows the user to stay logged
in via their normal Chrome session while the tool performs automated actions.

How to Use
----------
Start Chrome with remote debugging enabled:

    & "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222

Then connect via CDPSession:

    from src.colnect_api.session import create_colnect_session

    async with create_colnect_session() as session:
        if await session.verify_colnect_login():
            page = await session.get_colnect_page()
            # Perform operations...

Function Tree
-------------
### Classes
- CDPSession
  - __init__(cdp_url)
  - connect() -> Browser
  - disconnect() -> None
  - verify_colnect_login() -> bool
  - get_colnect_page() -> Page
  - navigate_to_stamp(stamp_url) -> Page

### Factory Functions
- create_colnect_session() -> CDPSession

Configuration Parameters
------------------------
These settings are loaded from `get_settings()`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| CHROME_CDP_URL | str | http://localhost:9222 | Chrome DevTools Protocol URL |
| COLNECT_BASE_URL | str | https://colnect.com | Colnect base URL |
| BROWSER_TIMEOUT | int | 60000 | Page timeout in milliseconds |

Usage Examples
--------------
### Basic Usage
```python
from src.colnect_api.session import create_colnect_session

async def check_login():
    async with create_colnect_session() as session:
        is_logged_in = await session.verify_colnect_login()
        print(f"Logged in: {is_logged_in}")
```

### Navigate to Stamp Page
```python
async with create_colnect_session() as session:
    if await session.verify_colnect_login():
        page = await session.navigate_to_stamp(
            "https://colnect.com/en/stamps/stamp/12345-Name"
        )
        # Page is ready for actions
```

See Also
--------
- actions.py: Colnect collection actions (add stamp, check owned)
- src/scraping/browser.py: Playwright browser manager for scraping
"""

import asyncio
import logging
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.core.config import get_settings
from src.core.errors import CDPConnectionError, ColnectActionError

logger = logging.getLogger(__name__)


class CDPSession:
    """Chrome DevTools Protocol session for Colnect automation.

    Connects to an existing Chrome browser via CDP and provides methods
    for Colnect-specific page navigation and login verification.

    Attributes
    ----------
    cdp_url : str
        Chrome DevTools Protocol URL (e.g., http://localhost:9222)
    colnect_base_url : str
        Colnect base URL for navigation
    timeout : int
        Page timeout in milliseconds

    Examples
    --------
    >>> async with create_colnect_session() as session:
    ...     if await session.verify_colnect_login():
    ...         page = await session.get_colnect_page()
    ...         print(f"Connected to: {page.url}")
    """

    def __init__(
        self,
        cdp_url: Optional[str] = None,
        colnect_base_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """Initialize CDP session.

        Parameters
        ----------
        cdp_url : str, optional
            Chrome DevTools Protocol URL. Default from settings.
        colnect_base_url : str, optional
            Colnect base URL. Default from settings.
        timeout : int, optional
            Page timeout in milliseconds. Default from settings.
        """
        settings = get_settings()

        self.cdp_url = cdp_url or settings.CHROME_CDP_URL
        self.colnect_base_url = colnect_base_url or settings.COLNECT_BASE_URL
        self.timeout = timeout or settings.BROWSER_TIMEOUT

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    async def __aenter__(self) -> "CDPSession":
        """Enter async context - connect to Chrome via CDP."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context - disconnect from Chrome."""
        await self.disconnect()

    async def connect(self) -> Browser:
        """Connect to Chrome browser via CDP.

        Returns
        -------
        Browser
            Playwright Browser instance connected via CDP.

        Raises
        ------
        CDPConnectionError
            If connection to Chrome fails (e.g., Chrome not running with CDP enabled).
        """
        logger.info(f"Connecting to Chrome via CDP at {self.cdp_url}")

        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.connect_over_cdp(
                self.cdp_url
            )

            # Get existing context or create new one
            contexts = self._browser.contexts
            if contexts:
                self._context = contexts[0]
                logger.debug(f"Using existing browser context with {len(self._context.pages)} pages")
            else:
                self._context = await self._browser.new_context()
                logger.debug("Created new browser context")

            logger.info("Successfully connected to Chrome via CDP")
            return self._browser

        except Exception as e:
            # Clean up playwright if connection failed
            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception:
                    pass  # Ignore cleanup errors
                self._playwright = None

            error_msg = str(e)
            if "Connection refused" in error_msg or "connect" in error_msg.lower():
                raise CDPConnectionError(
                    f"Cannot connect to Chrome at {self.cdp_url}. "
                    "Ensure Chrome is running with --remote-debugging-port=9222"
                ) from e
            raise CDPConnectionError(f"CDP connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from Chrome (does not close Chrome itself)."""
        logger.debug("Disconnecting from Chrome")

        # Note: We don't close pages/context since we're using an existing Chrome
        # Just cleanup our Playwright connection
        if self._browser:
            # Don't close - just disconnect
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        self._context = None
        self._page = None
        logger.info("Disconnected from Chrome")

    async def verify_colnect_login(self) -> bool:
        """Check if user is logged into Colnect.

        Navigates to Colnect and checks for login indicators.

        Returns
        -------
        bool
            True if user is logged in, False otherwise.

        Raises
        ------
        CDPConnectionError
            If not connected to Chrome.
        """
        if not self._context:
            raise CDPConnectionError("Not connected - call connect() first")

        logger.info("Verifying Colnect login status...")

        page = await self._get_or_create_page()

        # Navigate to Colnect if not already there
        if not page.url.startswith(self.colnect_base_url):
            logger.debug(f"Navigating to {self.colnect_base_url}")
            await page.goto(self.colnect_base_url, wait_until="domcontentloaded")
            await asyncio.sleep(1)  # Allow page to settle

        # Check for login indicators
        # Logged in users see their username in the header
        # Logged out users see "Log in" link
        try:
            # Look for user menu (indicates logged in)
            user_menu = await page.query_selector("a[href*='/profile/'], .user-menu, #user-menu")
            if user_menu:
                logger.info("User is logged into Colnect")
                return True

            # Check for login link (indicates logged out)
            login_link = await page.query_selector("a[href*='/login'], a[href*='/signin']")
            if login_link:
                logger.warning("User is NOT logged into Colnect")
                return False

            # Alternative check: look for "My Items" or collection links
            my_items = await page.query_selector("a[href*='/my_items/'], a[href*='/collection/']")
            if my_items:
                logger.info("User is logged into Colnect (found My Items)")
                return True

            logger.warning("Could not determine login status - assuming logged out")
            return False

        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False

    async def _get_or_create_page(self) -> Page:
        """Get existing page or create new one.

        Returns
        -------
        Page
            Playwright Page instance.
        """
        if self._page and not self._page.is_closed():
            return self._page

        if not self._context:
            raise CDPConnectionError("Not connected - call connect() first")

        # Try to use existing Colnect page
        for page in self._context.pages:
            if self.colnect_base_url in page.url:
                self._page = page
                logger.debug(f"Using existing Colnect page: {page.url}")
                return page

        # Use first page or create new one
        pages = self._context.pages
        if pages:
            self._page = pages[0]
            logger.debug(f"Using existing page: {self._page.url}")
        else:
            self._page = await self._context.new_page()
            logger.debug("Created new page")

        self._page.set_default_timeout(self.timeout)
        return self._page

    async def get_colnect_page(self) -> Page:
        """Get a page ready for Colnect operations.

        Returns
        -------
        Page
            Playwright Page instance on Colnect.

        Raises
        ------
        CDPConnectionError
            If not connected to Chrome.
        """
        if not self._context:
            raise CDPConnectionError("Not connected - call connect() first")

        page = await self._get_or_create_page()

        # Navigate to Colnect if not already there
        if not page.url.startswith(self.colnect_base_url):
            await page.goto(self.colnect_base_url, wait_until="domcontentloaded")

        return page

    async def navigate_to_stamp(self, stamp_url: str) -> Page:
        """Navigate to a specific stamp page on Colnect.

        Parameters
        ----------
        stamp_url : str
            Full Colnect stamp URL (e.g., https://colnect.com/en/stamps/stamp/12345-Name)

        Returns
        -------
        Page
            Playwright Page instance on the stamp page.

        Raises
        ------
        ColnectActionError
            If navigation fails.
        """
        if not stamp_url.startswith(self.colnect_base_url):
            # Handle relative URLs
            if stamp_url.startswith("/"):
                stamp_url = f"{self.colnect_base_url}{stamp_url}"
            else:
                raise ColnectActionError(f"Invalid stamp URL: {stamp_url}")

        logger.info(f"Navigating to stamp: {stamp_url}")

        page = await self._get_or_create_page()

        try:
            response = await page.goto(stamp_url, wait_until="domcontentloaded")

            if response is None:
                raise ColnectActionError(f"No response from {stamp_url}")

            if response.status == 404:
                raise ColnectActionError(f"Stamp page not found: {stamp_url}")

            if not response.ok:
                raise ColnectActionError(
                    f"HTTP {response.status} for {stamp_url}: {response.status_text}"
                )

            # Wait for page content to stabilize
            await asyncio.sleep(0.5)

            logger.debug(f"Successfully navigated to stamp page")
            return page

        except ColnectActionError:
            raise
        except Exception as e:
            raise ColnectActionError(f"Failed to navigate to stamp: {e}") from e


def create_colnect_session(
    cdp_url: Optional[str] = None,
    colnect_base_url: Optional[str] = None,
    timeout: Optional[int] = None,
) -> CDPSession:
    """Factory function to create CDPSession with settings.

    Parameters
    ----------
    cdp_url : str, optional
        Chrome DevTools Protocol URL. Default from settings.
    colnect_base_url : str, optional
        Colnect base URL. Default from settings.
    timeout : int, optional
        Page timeout in milliseconds. Default from settings.

    Returns
    -------
    CDPSession
        Configured CDP session (use as async context manager).

    Examples
    --------
    >>> session = create_colnect_session()
    >>> async with session:
    ...     is_logged_in = await session.verify_colnect_login()
    """
    return CDPSession(
        cdp_url=cdp_url,
        colnect_base_url=colnect_base_url,
        timeout=timeout,
    )


if __name__ == "__main__":
    """Test CDP session with Chrome."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("=== CDP Session Test ===")
    print("Prerequisites:")
    print("1. Start Chrome with: chrome.exe --remote-debugging-port=9222")
    print("2. Log into Colnect in that Chrome window")
    print()

    async def test_session():
        try:
            print("Connecting to Chrome via CDP...")
            async with create_colnect_session() as session:
                print("[OK] Connected to Chrome")

                print("Verifying Colnect login...")
                is_logged_in = await session.verify_colnect_login()

                if is_logged_in:
                    print("[OK] User is logged into Colnect")
                else:
                    print("[WARN] User is NOT logged into Colnect")
                    print("       Please log in manually and retry")

                # Get page info
                page = await session.get_colnect_page()
                print(f"Current page: {page.url}")

            print("\n[PASS] CDP session test completed!")
            return True

        except CDPConnectionError as e:
            print(f"\n[FAIL] CDP Connection Error: {e}")
            print("\nTroubleshooting:")
            print("1. Make sure Chrome is running with:")
            print('   & "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222')
            print("2. Check that CHROME_CDP_URL in .env.app matches the port")
            return False

        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False

    success = asyncio.run(test_session())
    sys.exit(0 if success else 1)
