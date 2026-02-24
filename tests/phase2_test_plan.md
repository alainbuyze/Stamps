# Phase 2 Test Plan: Colnect Scraping

## Prerequisites

Before testing, ensure:
1. Dependencies installed: `uv sync`
2. Playwright browser installed: `playwright install chromium`
3. Database initialized: `uv run stamp-tools init`

---

## Part 1: Unit Tests (Automated)

### 1.1 Run the Test Suite

```powershell
# Run all Phase 2 tests
uv run pytest tests/test_scraping/ -v

# Run with coverage
uv run pytest tests/test_scraping/ -v --cov=src.scraping
```

---

## Part 2: Module Import Tests (Manual)

### 2.1 Test Module Imports

Open a Python REPL and verify imports work:

```powershell
uv run python
```

```python
# Test 1: Import scraping module
from src.scraping import BrowserManager, ColnectScraper
print("OK: Scraping module imports")

# Test 2: Import browser manager
from src.scraping.browser import BrowserManager, create_browser
print("OK: Browser manager imports")

# Test 3: Import colnect scraper
from src.scraping.colnect import ColnectScraper, ScrapeCheckpoint
print("OK: Colnect scraper imports")

# Test 4: Import dependencies
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
print("OK: Dependencies available")

exit()
```

**Expected:** All prints show "OK" with no import errors.

---

## Part 3: Configuration Tests (Manual)

### 3.1 Verify Settings Are Loaded

```powershell
uv run python
```

```python
from src.core.config import get_settings

settings = get_settings()

# Check scraping settings
print(f"SCRAPE_DELAY_SECONDS: {settings.SCRAPE_DELAY_SECONDS}")
print(f"SCRAPE_RETRY_COUNT: {settings.SCRAPE_RETRY_COUNT}")
print(f"SCRAPE_ERROR_BEHAVIOR: {settings.SCRAPE_ERROR_BEHAVIOR}")
print(f"SCRAPE_CHECKPOINT_FILE: {settings.SCRAPE_CHECKPOINT_FILE}")
print(f"BROWSER_HEADLESS: {settings.BROWSER_HEADLESS}")
print(f"BROWSER_TIMEOUT: {settings.BROWSER_TIMEOUT}")
print(f"DEFAULT_THEMES: {settings.themes_list}")

exit()
```

**Expected:** All settings print with reasonable default values.

---

## Part 4: Browser Manager Tests (Manual)

### 4.1 Test Browser Launch and Close

```powershell
uv run python
```

```python
import asyncio
from src.scraping.browser import BrowserManager

async def test_browser_lifecycle():
    print("1. Creating browser manager...")
    browser = BrowserManager(headless=True)

    print("2. Entering context (launching browser)...")
    await browser.__aenter__()
    print("   Browser launched successfully")

    print("3. Creating new page...")
    page = await browser.new_page()
    print(f"   Page created: {page}")

    print("4. Closing page...")
    await page.close()

    print("5. Exiting context (closing browser)...")
    await browser.__aexit__(None, None, None)
    print("   Browser closed successfully")

    print("\nOK: Browser lifecycle test passed")

asyncio.run(test_browser_lifecycle())
exit()
```

**Expected:** All steps complete without errors.

### 4.2 Test Page Navigation

```powershell
uv run python
```

```python
import asyncio
from src.scraping.browser import BrowserManager

async def test_navigation():
    async with BrowserManager(headless=True) as browser:
        page = await browser.new_page()

        # Test 1: Navigate to a simple page
        print("1. Testing navigation to example.com...")
        await browser.goto(page, "https://example.com")
        print("   Navigation successful")

        # Test 2: Get page content
        print("2. Getting page content...")
        content = await browser.get_content(page)
        assert "Example Domain" in content
        print(f"   Content length: {len(content)} chars")

        # Test 3: Extract text
        print("3. Extracting text from h1...")
        title = await browser.extract_text(page, "h1")
        print(f"   Title: {title}")
        assert title == "Example Domain"

        await page.close()
        print("\nOK: Navigation test passed")

asyncio.run(test_navigation())
exit()
```

**Expected:** Successfully navigates and extracts "Example Domain".

### 4.3 Test Rate Limiting

```powershell
uv run python
```

```python
import asyncio
import time
from src.scraping.browser import BrowserManager

async def test_rate_limiting():
    # Use 2 second delay for testing
    async with BrowserManager(headless=True, delay_seconds=2.0) as browser:
        page = await browser.new_page()

        print("Testing rate limiting (2 second delay)...")

        # First request
        start = time.time()
        await browser.goto(page, "https://example.com")
        first_time = time.time() - start
        print(f"1. First request: {first_time:.2f}s")

        # Second request (should be delayed)
        start = time.time()
        await browser.goto(page, "https://example.com")
        second_time = time.time() - start
        print(f"2. Second request: {second_time:.2f}s")

        # The second request should take at least ~2 seconds due to rate limiting
        if second_time >= 1.5:
            print("\nOK: Rate limiting working (delay applied)")
        else:
            print("\nWARNING: Rate limiting may not be working")

        await page.close()

asyncio.run(test_rate_limiting())
exit()
```

**Expected:** Second request shows ~2 second delay.

---

## Part 5: Checkpoint Tests (Manual)

### 5.1 Test Checkpoint Save/Load

```powershell
uv run python
```

```python
import asyncio
from pathlib import Path
from src.scraping.colnect import ColnectScraper, ScrapeCheckpoint

async def test_checkpoint():
    # Use a test checkpoint file
    test_checkpoint = Path("data/test_checkpoint.json")

    async with ColnectScraper(checkpoint_file=test_checkpoint) as scraper:
        # Test 1: Save checkpoint
        print("1. Saving checkpoint...")
        checkpoint = ScrapeCheckpoint(
            theme="Space",
            page_number=5,
            processed_urls=["https://example.com/1", "https://example.com/2"],
            total_scraped=42,
        )
        scraper.save_checkpoint(checkpoint)
        print(f"   Saved to: {test_checkpoint}")

        # Test 2: Verify file exists
        assert test_checkpoint.exists()
        print("   File created successfully")

        # Test 3: Load checkpoint
        print("2. Loading checkpoint...")
        loaded = scraper.load_checkpoint()
        print(f"   Theme: {loaded.theme}")
        print(f"   Page: {loaded.page_number}")
        print(f"   Processed URLs: {len(loaded.processed_urls)}")
        print(f"   Total scraped: {loaded.total_scraped}")

        # Verify values
        assert loaded.theme == "Space"
        assert loaded.page_number == 5
        assert loaded.total_scraped == 42
        print("   Values match!")

        # Test 4: Clear checkpoint
        print("3. Clearing checkpoint...")
        scraper.clear_checkpoint()
        assert not test_checkpoint.exists()
        print("   Checkpoint cleared")

        print("\nOK: Checkpoint test passed")

asyncio.run(test_checkpoint())
exit()
```

**Expected:** Checkpoint saves, loads with correct values, and clears.

---

## Part 6: Colnect Scraper Tests (Manual)

### 6.1 Test Theme URL Generation

```powershell
uv run python
```

```python
from src.scraping.colnect import ColnectScraper

scraper = ColnectScraper.__new__(ColnectScraper)

# Test URL generation
print("Testing theme URL generation:")
print(f"  space page 1: {scraper.get_theme_url('space', 1)}")
print(f"  space page 2: {scraper.get_theme_url('space', 2)}")
print(f"  astronomy page 1: {scraper.get_theme_url('astronomy', 1)}")

# Expected format: https://colnect.com/en/stamps/list/theme/space
# and: https://colnect.com/en/stamps/list/theme/space/page/2
```

**Expected:** URLs follow Colnect's pattern.

### 6.2 Test Single Page Scrape (Live - Requires Internet)

```powershell
uv run python
```

```python
import asyncio
from src.scraping.colnect import ColnectScraper

async def test_single_scrape():
    # Find a real Colnect stamp URL to test with
    # This is a sample - you may need to find a current valid URL
    test_url = "https://colnect.com/en/stamps/stamp/1-United_States"

    print(f"Testing scrape of: {test_url}")
    print("(This test requires internet and a valid Colnect URL)")
    print()

    try:
        async with ColnectScraper() as scraper:
            stamp = await scraper.scrape_single(test_url)

            print("Extracted data:")
            print(f"  Colnect ID: {stamp.colnect_id}")
            print(f"  Title: {stamp.title}")
            print(f"  Country: {stamp.country}")
            print(f"  Year: {stamp.year}")
            print(f"  Image URL: {stamp.image_url[:50]}...")
            print(f"  Themes: {stamp.themes}")
            print(f"  Catalog codes: {stamp.catalog_codes}")

            print("\nOK: Single page scrape successful")
    except Exception as e:
        print(f"\nERROR: {e}")
        print("Note: This may fail if the URL is invalid or site structure changed")

asyncio.run(test_single_scrape())
exit()
```

**Expected:** Extracts stamp data (may fail if URL invalid - find a real Colnect stamp URL).

---

## Part 7: CLI Tests (Manual)

### 7.1 Test CLI Help

```powershell
uv run stamp-tools --help
uv run stamp-tools scrape --help
uv run stamp-tools scrape colnect --help
```

**Expected:** Help text displays for all commands.

### 7.2 Test CLI with Dry Output

```powershell
# This will attempt to scrape - cancel with Ctrl+C after a few seconds
uv run stamp-tools scrape colnect --themes "Space"
```

**Expected:** Shows scraper starting, then Ctrl+C saves checkpoint gracefully.

### 7.3 Test Resume Flag

```powershell
# After cancelling above, try resume
uv run stamp-tools scrape colnect --resume
```

**Expected:** Shows "Resuming from checkpoint" message.

---

## Part 8: Database Integration Tests (Manual)

### 8.1 Verify Database Schema

```powershell
uv run python
```

```python
from src.core.database import get_connection, init_database

# Initialize database
init_database()

# Check tables exist
with get_connection() as conn:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    tables = [row[0] for row in cursor.fetchall()]

print("Tables in database:")
for table in tables:
    print(f"  - {table}")

expected = ["catalog_stamps", "lastdodo_items", "import_tasks"]
for table in expected:
    assert table in tables, f"Missing table: {table}"

print("\nOK: All required tables exist")
exit()
```

**Expected:** All three tables exist.

### 8.2 Test Stamp Upsert

```powershell
uv run python
```

```python
from datetime import datetime
from src.core.database import (
    CatalogStamp,
    upsert_catalog_stamp,
    get_catalog_stamp,
    count_catalog_stamps,
)

# Create test stamp
test_stamp = CatalogStamp(
    colnect_id="TEST123",
    colnect_url="https://colnect.com/test",
    title="Test Space Stamp",
    country="Test Country",
    year=2024,
    image_url="https://example.com/image.jpg",
    themes=["Space", "Rockets"],
    catalog_codes={"michel": "123", "scott": "456"},
    scraped_at=datetime.now(),
)

print("1. Inserting test stamp...")
upsert_catalog_stamp(test_stamp)
print("   Inserted successfully")

print("2. Retrieving stamp...")
retrieved = get_catalog_stamp("TEST123")
print(f"   Title: {retrieved.title}")
print(f"   Country: {retrieved.country}")
print(f"   Themes: {retrieved.themes}")
print(f"   Catalog codes: {retrieved.catalog_codes}")

print("3. Testing update (upsert)...")
test_stamp.title = "Updated Test Stamp"
upsert_catalog_stamp(test_stamp)
retrieved = get_catalog_stamp("TEST123")
assert retrieved.title == "Updated Test Stamp"
print("   Update successful")

print("4. Counting stamps...")
count = count_catalog_stamps()
print(f"   Total stamps: {count}")

print("\nOK: Database operations working")

# Cleanup
from src.core.database import get_connection
with get_connection() as conn:
    conn.execute("DELETE FROM catalog_stamps WHERE colnect_id = 'TEST123'")
print("   Test data cleaned up")

exit()
```

**Expected:** All CRUD operations succeed.

---

## Part 9: Error Handling Tests (Manual)

### 9.1 Test 404 Handling

```powershell
uv run python
```

```python
import asyncio
from src.scraping.browser import BrowserManager
from src.core.errors import PageNotFoundError

async def test_404():
    async with BrowserManager(headless=True) as browser:
        page = await browser.new_page()

        print("Testing 404 handling...")
        try:
            await browser.goto(page, "https://colnect.com/en/stamps/stamp/999999999-NonExistent")
            print("ERROR: Should have raised PageNotFoundError")
        except PageNotFoundError as e:
            print(f"OK: Caught PageNotFoundError: {e}")
        except Exception as e:
            print(f"Got different error (may be expected): {type(e).__name__}: {e}")

        await page.close()

asyncio.run(test_404())
exit()
```

**Expected:** Raises `PageNotFoundError` or similar error.

### 9.2 Test Timeout Handling

```powershell
uv run python
```

```python
import asyncio
from src.scraping.browser import BrowserManager
from src.core.errors import PageTimeoutError

async def test_timeout():
    # Use very short timeout
    async with BrowserManager(headless=True, timeout=100, retry_count=1) as browser:
        page = await browser.new_page()

        print("Testing timeout handling (very short timeout)...")
        try:
            # This should timeout with 100ms
            await browser.goto(page, "https://colnect.com")
            print("Page loaded (network was fast)")
        except PageTimeoutError as e:
            print(f"OK: Caught PageTimeoutError: {e}")
        except Exception as e:
            print(f"Got error: {type(e).__name__}: {e}")

        await page.close()

asyncio.run(test_timeout())
exit()
```

**Expected:** Either loads quickly or raises timeout error.

---

## Part 10: End-to-End Test (Manual)

### 10.1 Full Scrape Test (Small Scale)

This test performs an actual scrape of a small number of stamps.

```powershell
uv run python
```

```python
import asyncio
from src.scraping.colnect import ColnectScraper
from src.core.database import count_catalog_stamps, init_database

async def test_e2e_scrape():
    init_database()

    initial_count = count_catalog_stamps()
    print(f"Initial stamp count: {initial_count}")

    print("\nStarting small-scale scrape test...")
    print("(Will scrape first page of Space theme only)")

    stamps_found = 0

    def on_progress(count, msg):
        nonlocal stamps_found
        stamps_found = count
        print(f"  [{count}] {msg[:60]}")

    async with ColnectScraper() as scraper:
        # Override to only do one page for testing
        page = await scraper._browser.new_page()

        try:
            # Get just the first page of stamps
            urls, has_next = await scraper.get_theme_stamp_urls(page, "space", 1)
            print(f"\nFound {len(urls)} stamp URLs on first page")
            print(f"Has next page: {has_next}")

            # Scrape just the first 3 stamps as a test
            test_urls = urls[:3] if len(urls) >= 3 else urls
            print(f"\nScraping first {len(test_urls)} stamps...")

            for url in test_urls:
                try:
                    stamp = await scraper.scrape_stamp_page(page, url)
                    print(f"  OK: {stamp.colnect_id} - {stamp.title[:40]}")
                except Exception as e:
                    print(f"  ERROR: {url} - {e}")
        finally:
            await page.close()

    final_count = count_catalog_stamps()
    print(f"\nFinal stamp count: {final_count}")
    print(f"New stamps added: {final_count - initial_count}")

    print("\nOK: End-to-end test complete")

asyncio.run(test_e2e_scrape())
exit()
```

**Expected:** Discovers stamp URLs and scrapes a few stamps successfully.

---

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Part 1: Automated Tests | | |
| Part 2: Module Imports | | |
| Part 3: Configuration | | |
| Part 4.1: Browser Lifecycle | | |
| Part 4.2: Navigation | | |
| Part 4.3: Rate Limiting | | |
| Part 5: Checkpoints | | |
| Part 6.1: URL Generation | | |
| Part 6.2: Single Page Scrape | | |
| Part 7.1: CLI Help | | |
| Part 7.2: CLI Execution | | |
| Part 7.3: Resume | | |
| Part 8.1: Database Schema | | |
| Part 8.2: Stamp Upsert | | |
| Part 9.1: 404 Handling | | |
| Part 9.2: Timeout Handling | | |
| Part 10: End-to-End | | |

---

## Troubleshooting

### Browser Won't Launch
```powershell
# Reinstall Playwright browsers
playwright install chromium
```

### Import Errors
```powershell
# Reinstall dependencies
uv sync
```

### Database Errors
```powershell
# Reinitialize database
uv run stamp-tools init
```

### Colnect Page Structure Changed
If extraction fails, the Colnect website structure may have changed. Check:
1. Open a stamp page in browser
2. Inspect HTML structure
3. Update selectors in `src/scraping/colnect.py`
