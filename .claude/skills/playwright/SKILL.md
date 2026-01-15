---
name: playwright
description: Browser automation and end-to-end testing with Playwright. Use when automating browsers, writing E2E tests, scraping dynamic websites, taking screenshots, generating PDFs, or when user mentions Playwright, browser testing, or web automation.
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Playwright Browser Automation

## Overview

Playwright is a modern browser automation framework for end-to-end testing and web scraping. It supports Chromium, Firefox, and WebKit browsers.

## When to Use This Skill

- Writing end-to-end (E2E) tests
- Automating browser interactions
- Scraping JavaScript-rendered websites
- Taking screenshots or generating PDFs
- Testing web applications across browsers
- Automating form submissions and user flows

## Project Setup

### Installation

```bash
# Using pip
pip install playwright
playwright install

# Using uv
uv add playwright
uv run playwright install
```

### Project Structure

```
tests/
├── conftest.py          # Pytest fixtures
├── e2e/
│   ├── test_auth.py     # Authentication tests
│   ├── test_checkout.py # Checkout flow tests
│   └── test_search.py   # Search functionality
├── pages/               # Page Object Models
│   ├── base_page.py
│   ├── login_page.py
│   └── home_page.py
└── utils/
    └── helpers.py
```

## Core Patterns

### Basic Browser Automation

```python
from playwright.sync_api import sync_playwright

def run_automation():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate
        page.goto("https://example.com")

        # Interact with elements
        page.fill("input[name='username']", "user@example.com")
        page.fill("input[name='password']", "password123")
        page.click("button[type='submit']")

        # Wait for navigation
        page.wait_for_url("**/dashboard")

        # Get content
        title = page.title()
        content = page.content()

        browser.close()
        return title
```

### Async Version

```python
import asyncio
from playwright.async_api import async_playwright

async def run_async():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://example.com")
        title = await page.title()
        await browser.close()
        return title

# Run
result = asyncio.run(run_async())
```

### Page Object Model (Recommended)

```python
# pages/base_page.py
class BasePage:
    def __init__(self, page):
        self.page = page

    def navigate(self, url: str):
        self.page.goto(url)

    def get_title(self) -> str:
        return self.page.title()

# pages/login_page.py
class LoginPage(BasePage):
    URL = "/login"

    # Locators
    USERNAME_INPUT = "input[name='username']"
    PASSWORD_INPUT = "input[name='password']"
    SUBMIT_BUTTON = "button[type='submit']"
    ERROR_MESSAGE = ".error-message"

    def login(self, username: str, password: str):
        self.page.fill(self.USERNAME_INPUT, username)
        self.page.fill(self.PASSWORD_INPUT, password)
        self.page.click(self.SUBMIT_BUTTON)

    def get_error(self) -> str:
        return self.page.text_content(self.ERROR_MESSAGE)
```

## Pytest Integration

### Conftest Fixtures

```python
# conftest.py
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

@pytest.fixture
def authenticated_page(page):
    """Page with logged-in user."""
    page.goto("/login")
    page.fill("#username", "testuser")
    page.fill("#password", "testpass")
    page.click("button[type='submit']")
    page.wait_for_url("**/dashboard")
    yield page
```

### Test Examples

```python
# test_login.py
def test_successful_login(page):
    page.goto("https://example.com/login")
    page.fill("#username", "valid_user")
    page.fill("#password", "valid_pass")
    page.click("button[type='submit']")

    # Assert redirect to dashboard
    assert page.url.endswith("/dashboard")
    assert page.is_visible(".welcome-message")

def test_invalid_login(page):
    page.goto("https://example.com/login")
    page.fill("#username", "invalid")
    page.fill("#password", "wrong")
    page.click("button[type='submit']")

    # Assert error message
    error = page.text_content(".error")
    assert "Invalid credentials" in error

def test_form_validation(page):
    page.goto("https://example.com/register")
    page.click("button[type='submit']")

    # Check validation errors appear
    assert page.is_visible(".field-error")
```

## Selectors

### Selector Types

```python
# CSS selectors (default)
page.click("button.submit")
page.fill("input#email", "test@example.com")

# Text selectors
page.click("text=Sign In")
page.click("text=/submit/i")  # Case-insensitive regex

# XPath
page.click("xpath=//button[@type='submit']")

# Role-based (accessibility)
page.get_by_role("button", name="Submit").click()
page.get_by_label("Email").fill("test@example.com")
page.get_by_placeholder("Enter email").fill("test@example.com")
page.get_by_text("Welcome").is_visible()

# Test IDs (recommended)
page.get_by_test_id("submit-btn").click()
```

## Waiting Strategies

```python
# Wait for element
page.wait_for_selector(".loading", state="hidden")
page.wait_for_selector(".content", state="visible")

# Wait for navigation
page.wait_for_url("**/success")
page.wait_for_load_state("networkidle")

# Wait for response
with page.expect_response("**/api/data") as response_info:
    page.click("#load-data")
response = response_info.value

# Custom wait
page.wait_for_function("() => document.querySelector('.items').children.length > 5")

# Explicit timeout
page.click("button", timeout=10000)  # 10 seconds
```

## Screenshots and PDFs

```python
# Screenshot
page.screenshot(path="screenshot.png")
page.screenshot(path="fullpage.png", full_page=True)

# Element screenshot
page.locator(".chart").screenshot(path="chart.png")

# PDF generation
page.pdf(path="page.pdf", format="A4")
page.pdf(
    path="report.pdf",
    format="Letter",
    print_background=True,
    margin={"top": "1cm", "bottom": "1cm"}
)
```

## Network Interception

```python
# Block images for faster scraping
page.route("**/*.{png,jpg,jpeg,gif}", lambda route: route.abort())

# Mock API responses
def handle_api(route):
    route.fulfill(
        status=200,
        content_type="application/json",
        body='{"status": "mocked"}'
    )

page.route("**/api/data", handle_api)

# Modify requests
def modify_request(route, request):
    headers = {**request.headers, "X-Custom": "value"}
    route.continue_(headers=headers)

page.route("**/*", modify_request)
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with browser visible
pytest tests/ -v --headed

# Run specific browser
pytest tests/ -v --browser chromium
pytest tests/ -v --browser firefox
pytest tests/ -v --browser webkit

# Run with tracing for debugging
pytest tests/ -v --tracing on

# Generate HTML report
pytest tests/ -v --html=report.html

# Parallel execution
pytest tests/ -v -n auto
```

## Debugging

```python
# Pause execution for debugging
page.pause()

# Enable tracing
context.tracing.start(screenshots=True, snapshots=True)
# ... do actions ...
context.tracing.stop(path="trace.zip")

# View trace
# playwright show-trace trace.zip
```

## Best Practices

1. **Use Page Object Model** - Encapsulate page logic in classes
2. **Prefer role-based selectors** - More resilient to UI changes
3. **Add data-testid attributes** - Explicit test hooks
4. **Handle waits properly** - Avoid arbitrary sleeps
5. **Run headless in CI** - Faster execution
6. **Use fixtures** - Share browser/context across tests
7. **Isolate tests** - Each test should be independent
8. **Mock external services** - Faster and more reliable

## Common Issues

| Issue | Solution |
|-------|----------|
| Timeout errors | Increase timeout or add explicit waits |
| Element not found | Check selector, wait for element |
| Flaky tests | Use proper waiting strategies |
| Slow tests | Run headless, mock network |
| Auth issues | Use storage state for session persistence |
