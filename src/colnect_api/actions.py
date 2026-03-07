"""Colnect collection actions for browser automation.

Goal
----
Automate Colnect collection operations via CDP browser automation. Supports adding
stamps to collection with condition, quantity, and comments. Handles duplicate
detection and ownership verification.

How to Use
----------
Use ColnectActions with an active CDPSession:

    from src.colnect_api import create_colnect_session, create_colnect_actions

    async with create_colnect_session() as session:
        if await session.verify_colnect_login():
            actions = create_colnect_actions(session)
            success = await actions.add_to_collection(
                colnect_url="https://colnect.com/en/stamps/stamp/12345-Name",
                condition="MNH",
                quantity=1,
                comment="From album page 5"
            )

Function Tree
-------------
### Classes
- ColnectActions
  - __init__(session)
  - add_to_collection(colnect_url, condition, quantity, comment) -> bool
  - check_owned(colnect_url) -> OwnershipInfo
  - _click_add_button(page) -> bool
  - _fill_add_form(page, condition, quantity, comment) -> bool
  - _submit_and_verify(page) -> bool

### Data Classes
- OwnershipInfo: Contains owned status, quantity, and condition

### Factory Functions
- create_colnect_actions(session) -> ColnectActions

Configuration Parameters
------------------------
These settings are loaded from `get_settings()`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| BROWSER_TIMEOUT | int | 60000 | Page timeout in milliseconds |

Usage Examples
--------------
### Add Single Stamp
```python
from src.colnect_api import create_colnect_session, create_colnect_actions

async with create_colnect_session() as session:
    if await session.verify_colnect_login():
        actions = create_colnect_actions(session)
        success = await actions.add_to_collection(
            colnect_url="https://colnect.com/en/stamps/stamp/12345-Apollo_11",
            condition="MNH",
            quantity=1,
        )
        print(f"Added: {success}")
```

### Check Ownership First
```python
async with create_colnect_session() as session:
    actions = create_colnect_actions(session)

    # Check if already owned
    ownership = await actions.check_owned(stamp_url)
    if ownership.owned:
        print(f"Already own {ownership.quantity}x ({ownership.condition})")
    else:
        # Add to collection
        await actions.add_to_collection(stamp_url, "MNH", 1)
```

See Also
--------
- session.py: CDP session management
- src/identification/results.py: Identification results that trigger add actions
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from playwright.async_api import Page

from src.colnect_api.session import CDPSession
from src.core.config import get_settings
from src.core.errors import ColnectActionError

logger = logging.getLogger(__name__)


class StampCondition(Enum):
    """Stamp condition values supported by Colnect."""

    MNH = "MNH"  # Mint Never Hinged
    MH = "MH"  # Mint Hinged
    USED = "Used"
    CTO = "CTO"  # Cancelled To Order
    FDC = "FDC"  # First Day Cover


@dataclass
class OwnershipInfo:
    """Information about stamp ownership status.

    Attributes
    ----------
    owned : bool
        Whether the stamp is in the user's collection.
    quantity : int
        Number of copies owned (0 if not owned).
    condition : str | None
        Condition of owned stamp(s), if available.
    in_wishlist : bool
        Whether the stamp is in the user's wishlist.
    """

    owned: bool
    quantity: int = 0
    condition: Optional[str] = None
    in_wishlist: bool = False


class ColnectActions:
    """Browser automation for Colnect collection operations.

    Provides methods to add stamps to collection, check ownership status,
    and manage collection entries via CDP browser automation.

    Attributes
    ----------
    session : CDPSession
        Active CDP session connected to Chrome.
    timeout : int
        Operation timeout in milliseconds.

    Examples
    --------
    >>> async with create_colnect_session() as session:
    ...     actions = ColnectActions(session)
    ...     success = await actions.add_to_collection(stamp_url, "MNH", 1)
    """

    # CSS selectors for Colnect page elements
    # These may need adjustment if Colnect updates their site
    SELECTORS = {
        # Add to collection button
        "add_button": [
            "button[data-action='add-to-collection']",
            ".add-collection-btn",
            "a[href*='add_item']",
            "#add-to-collection",
            ".item-actions button:has-text('Add')",
            "button:has-text('Add to collection')",
        ],
        # Ownership indicators
        "owned_indicator": [
            ".owned-badge",
            ".in-collection",
            "[data-owned='true']",
            ".item-status.owned",
        ],
        "wishlist_indicator": [
            ".wishlist-badge",
            ".in-wishlist",
            "[data-wishlist='true']",
        ],
        # Add form elements
        "condition_select": [
            "select[name='condition']",
            "#condition",
            "select.condition-select",
        ],
        "quantity_input": [
            "input[name='quantity']",
            "#quantity",
            "input.quantity-input",
            "input[type='number']",
        ],
        "comment_input": [
            "textarea[name='comment']",
            "textarea[name='note']",
            "#comment",
            "#note",
            "textarea.comment-input",
        ],
        "submit_button": [
            "button[type='submit']",
            "input[type='submit']",
            ".submit-btn",
            "button:has-text('Save')",
            "button:has-text('Add')",
        ],
        # Success/error indicators
        "success_message": [
            ".success-message",
            ".alert-success",
            "[data-status='success']",
        ],
        "error_message": [
            ".error-message",
            ".alert-danger",
            ".alert-error",
            "[data-status='error']",
        ],
    }

    def __init__(self, session: CDPSession):
        """Initialize Colnect actions.

        Parameters
        ----------
        session : CDPSession
            Active CDP session connected to Chrome.
        """
        self.session = session
        settings = get_settings()
        self.timeout = settings.BROWSER_TIMEOUT

    async def _find_element(self, page: Page, selector_key: str) -> Optional[object]:
        """Try multiple selectors to find an element.

        Parameters
        ----------
        page : Page
            Playwright page instance.
        selector_key : str
            Key in SELECTORS dict.

        Returns
        -------
        ElementHandle | None
            Element if found, None otherwise.
        """
        selectors = self.SELECTORS.get(selector_key, [])
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    logger.debug(f"Found element with selector: {selector}")
                    return element
            except Exception:
                continue
        return None

    async def check_owned(self, colnect_url: str) -> OwnershipInfo:
        """Check if stamp is already in user's collection.

        Parameters
        ----------
        colnect_url : str
            Colnect stamp page URL.

        Returns
        -------
        OwnershipInfo
            Ownership status with quantity and condition.

        Raises
        ------
        ColnectActionError
            If unable to check ownership status.
        """
        logger.info(f"Checking ownership for: {colnect_url}")

        try:
            page = await self.session.navigate_to_stamp(colnect_url)
            await asyncio.sleep(0.5)  # Allow page to settle

            # Check for owned indicator
            owned = False
            for selector in self.SELECTORS["owned_indicator"]:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        owned = True
                        logger.debug(f"Found owned indicator: {selector}")
                        break
                except Exception:
                    continue

            # Check for wishlist indicator
            in_wishlist = False
            for selector in self.SELECTORS["wishlist_indicator"]:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        in_wishlist = True
                        break
                except Exception:
                    continue

            # Try to extract quantity if owned
            quantity = 1 if owned else 0
            condition = None

            if owned:
                # Look for quantity display
                try:
                    qty_elem = await page.query_selector(".owned-quantity, .collection-qty")
                    if qty_elem:
                        qty_text = await qty_elem.text_content()
                        if qty_text:
                            import re
                            match = re.search(r"(\d+)", qty_text)
                            if match:
                                quantity = int(match.group(1))
                except Exception as e:
                    logger.debug(f"Could not extract quantity: {e}")

            logger.info(
                f"Ownership check: owned={owned}, quantity={quantity}, wishlist={in_wishlist}"
            )
            return OwnershipInfo(
                owned=owned,
                quantity=quantity,
                condition=condition,
                in_wishlist=in_wishlist,
            )

        except ColnectActionError:
            raise
        except Exception as e:
            raise ColnectActionError(f"Failed to check ownership: {e}") from e

    async def add_to_collection(
        self,
        colnect_url: str,
        condition: str = "MNH",
        quantity: int = 1,
        comment: Optional[str] = None,
        skip_if_owned: bool = True,
    ) -> bool:
        """Add stamp to Colnect collection.

        Parameters
        ----------
        colnect_url : str
            Colnect stamp page URL.
        condition : str, optional
            Stamp condition (MNH, MH, Used, CTO, FDC). Default: "MNH".
        quantity : int, optional
            Number of copies to add. Default: 1.
        comment : str, optional
            Optional comment/note for the collection entry.
        skip_if_owned : bool, optional
            Skip if already owned. Default: True.

        Returns
        -------
        bool
            True if stamp was added successfully.

        Raises
        ------
        ColnectActionError
            If add operation fails.
        """
        logger.info(f"Adding to collection: {colnect_url} ({condition}, qty={quantity})")

        try:
            # Check if already owned
            if skip_if_owned:
                ownership = await self.check_owned(colnect_url)
                if ownership.owned:
                    logger.info(f"Stamp already owned ({ownership.quantity}x) - skipping")
                    return True  # Consider this a success

            # Navigate to stamp page
            page = await self.session.navigate_to_stamp(colnect_url)

            # Click add to collection button
            add_clicked = await self._click_add_button(page)
            if not add_clicked:
                raise ColnectActionError("Could not find or click 'Add to collection' button")

            # Wait for form to appear
            await asyncio.sleep(1)

            # Fill the form
            form_filled = await self._fill_add_form(page, condition, quantity, comment)
            if not form_filled:
                logger.warning("Could not fill all form fields - proceeding anyway")

            # Submit and verify
            success = await self._submit_and_verify(page)

            if success:
                logger.info(f"Successfully added stamp to collection")
            else:
                logger.warning(f"Add operation completed but success not verified")

            return success

        except ColnectActionError:
            raise
        except Exception as e:
            raise ColnectActionError(f"Failed to add stamp: {e}") from e

    async def _click_add_button(self, page: Page) -> bool:
        """Find and click the 'Add to collection' button.

        Parameters
        ----------
        page : Page
            Playwright page instance on stamp page.

        Returns
        -------
        bool
            True if button was clicked.
        """
        add_btn = await self._find_element(page, "add_button")
        if add_btn:
            await add_btn.click()
            logger.debug("Clicked add to collection button")
            return True

        # Fallback: try clicking by text
        try:
            add_link = await page.query_selector("text=Add to collection")
            if add_link:
                await add_link.click()
                logger.debug("Clicked 'Add to collection' link")
                return True
        except Exception:
            pass

        # Another fallback: look for any "Add" button in the actions area
        try:
            action_btns = await page.query_selector_all(".item-actions button, .stamp-actions button")
            for btn in action_btns:
                text = await btn.text_content()
                if text and "add" in text.lower():
                    await btn.click()
                    logger.debug(f"Clicked action button: {text}")
                    return True
        except Exception:
            pass

        logger.error("Could not find add to collection button")
        return False

    async def _fill_add_form(
        self,
        page: Page,
        condition: str,
        quantity: int,
        comment: Optional[str],
    ) -> bool:
        """Fill the add to collection form.

        Parameters
        ----------
        page : Page
            Playwright page instance with form visible.
        condition : str
            Stamp condition value.
        quantity : int
            Number of copies.
        comment : str | None
            Optional comment.

        Returns
        -------
        bool
            True if form was filled (at least partially).
        """
        filled_any = False

        # Fill condition
        condition_select = await self._find_element(page, "condition_select")
        if condition_select:
            try:
                await condition_select.select_option(value=condition)
                logger.debug(f"Set condition: {condition}")
                filled_any = True
            except Exception:
                # Try by label
                try:
                    await condition_select.select_option(label=condition)
                    logger.debug(f"Set condition by label: {condition}")
                    filled_any = True
                except Exception as e:
                    logger.debug(f"Could not set condition: {e}")

        # Fill quantity
        quantity_input = await self._find_element(page, "quantity_input")
        if quantity_input:
            try:
                await quantity_input.fill(str(quantity))
                logger.debug(f"Set quantity: {quantity}")
                filled_any = True
            except Exception as e:
                logger.debug(f"Could not set quantity: {e}")

        # Fill comment
        if comment:
            comment_input = await self._find_element(page, "comment_input")
            if comment_input:
                try:
                    await comment_input.fill(comment)
                    logger.debug(f"Set comment: {comment[:50]}...")
                    filled_any = True
                except Exception as e:
                    logger.debug(f"Could not set comment: {e}")

        return filled_any

    async def _submit_and_verify(self, page: Page) -> bool:
        """Submit the add form and verify success.

        Parameters
        ----------
        page : Page
            Playwright page instance with filled form.

        Returns
        -------
        bool
            True if submission succeeded.
        """
        # Find and click submit
        submit_btn = await self._find_element(page, "submit_button")
        if submit_btn:
            await submit_btn.click()
            logger.debug("Clicked submit button")
        else:
            # Try pressing Enter on the form
            try:
                await page.keyboard.press("Enter")
                logger.debug("Pressed Enter to submit")
            except Exception:
                logger.warning("Could not submit form")
                return False

        # Wait for response
        await asyncio.sleep(2)

        # Check for success message
        success_elem = await self._find_element(page, "success_message")
        if success_elem:
            logger.debug("Found success message")
            return True

        # Check for error message
        error_elem = await self._find_element(page, "error_message")
        if error_elem:
            try:
                error_text = await error_elem.text_content()
                logger.error(f"Add failed with error: {error_text}")
            except Exception:
                logger.error("Add failed with error (could not read message)")
            return False

        # Check if we're back on the stamp page with owned indicator
        await asyncio.sleep(1)
        owned_elem = await self._find_element(page, "owned_indicator")
        if owned_elem:
            logger.debug("Stamp now shows as owned")
            return True

        # Assume success if no error
        logger.debug("No error found - assuming success")
        return True


def create_colnect_actions(session: CDPSession) -> ColnectActions:
    """Factory function to create ColnectActions.

    Parameters
    ----------
    session : CDPSession
        Active CDP session connected to Chrome.

    Returns
    -------
    ColnectActions
        Configured actions instance.

    Examples
    --------
    >>> async with create_colnect_session() as session:
    ...     actions = create_colnect_actions(session)
    ...     await actions.add_to_collection(url, "MNH", 1)
    """
    return ColnectActions(session)


if __name__ == "__main__":
    """Test Colnect actions with a sample stamp."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("=== Colnect Actions Test ===")
    print("Prerequisites:")
    print("1. Start Chrome with: chrome.exe --remote-debugging-port=9222")
    print("2. Log into Colnect in that Chrome window")
    print()

    # Test URL - a sample space stamp (adjust as needed)
    TEST_STAMP_URL = "https://colnect.com/en/stamps/stamp/1068849-Apollo_11_Moon_Landing_-_25th_Anniversary-USA"

    async def test_actions():
        from src.colnect_api.session import create_colnect_session

        try:
            print("Connecting to Chrome via CDP...")
            async with create_colnect_session() as session:
                print("[OK] Connected to Chrome")

                print("Verifying Colnect login...")
                is_logged_in = await session.verify_colnect_login()

                if not is_logged_in:
                    print("[FAIL] Not logged into Colnect - please log in first")
                    return False

                print("[OK] Logged into Colnect")

                # Create actions
                actions = create_colnect_actions(session)

                # Test ownership check
                print(f"\nChecking ownership of test stamp...")
                print(f"URL: {TEST_STAMP_URL}")
                ownership = await actions.check_owned(TEST_STAMP_URL)
                print(f"Owned: {ownership.owned}")
                print(f"Quantity: {ownership.quantity}")
                print(f"In wishlist: {ownership.in_wishlist}")

                # Only test add if not already owned
                if not ownership.owned:
                    print("\n[INFO] Stamp not owned - would test add_to_collection here")
                    print("       Skipping actual add to avoid modifying your collection")
                    # Uncomment to actually test:
                    # success = await actions.add_to_collection(
                    #     TEST_STAMP_URL,
                    #     condition="MNH",
                    #     quantity=1,
                    #     comment="Test add from automation"
                    # )
                    # print(f"Add result: {success}")
                else:
                    print("\n[INFO] Stamp already owned - skipping add test")

            print("\n[PASS] Colnect actions test completed!")
            return True

        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    success = asyncio.run(test_actions())
    sys.exit(0 if success else 1)
