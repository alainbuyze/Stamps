# Feature: Phase 1 - Foundation (Scraping & Content Extraction)

## Summary

Build the foundational components for the CoderDojo Guide Generator: a Playwright-based web scraper to fetch tutorial pages from Elecfreaks wiki, a BeautifulSoup content extractor to isolate main tutorial content, and a basic CLI with the `generate` command that outputs raw Markdown. This phase establishes the pipeline architecture and proves the core scraping/extraction workflow before adding enhancement and translation features.

## User Story

As a CoderDojo volunteer
I want to run a command with a tutorial URL and get a Markdown file with the tutorial content
So that I can start preparing printed materials from online tutorials

## Problem Statement

Elecfreaks wiki tutorials are only available online and in English. The content is embedded in a complex page with navigation, sidebars, and footer elements that make direct printing impractical. Volunteers need a way to extract just the tutorial content (text and image references) into a clean format.

## Solution Statement

Create a Python CLI tool that:
1. Uses Playwright to render the full page (handling any JavaScript)
2. Uses BeautifulSoup to extract the main article content
3. Uses markdownify to convert HTML to clean Markdown
4. Outputs a structured Markdown file with image references

## Metadata

| Field            | Value                                             |
| ---------------- | ------------------------------------------------- |
| Type             | NEW_CAPABILITY                                    |
| Complexity       | MEDIUM                                            |
| Systems Affected | CLI, Scraper, Extractor, Generator                |
| Dependencies     | playwright ^1.40, beautifulsoup4 ^4.12, markdownify ^0.11, click ^8.1, rich ^13.7, httpx ^0.26, pydantic ^2.5 |
| Estimated Tasks  | 12                                                |

---

## UX Design

### Before State

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                              BEFORE STATE                                      ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   ┌─────────────┐         ┌─────────────┐         ┌─────────────┐            ║
║   │   Volunteer │ ──────► │   Browser   │ ──────► │  Print Page │            ║
║   │  Wants Guide│         │  Open Wiki  │         │  (Messy!)   │            ║
║   └─────────────┘         └─────────────┘         └─────────────┘            ║
║                                                                               ║
║   USER_FLOW:                                                                  ║
║   1. Open browser, navigate to Elecfreaks wiki                                ║
║   2. Find tutorial page                                                       ║
║   3. Try to print → includes navigation, sidebar, footer                      ║
║   4. Manually copy/paste content to Word → loses formatting                   ║
║   5. Re-add images manually → time-consuming                                  ║
║                                                                               ║
║   PAIN_POINT: Manual process, messy output, 30+ minutes per guide            ║
║   DATA_FLOW: Browser → Manual copy → Word/Google Docs                         ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### After State

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                               AFTER STATE                                      ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   ┌─────────────┐         ┌─────────────┐         ┌─────────────┐            ║
║   │   Volunteer │ ──────► │ CLI Command │ ──────► │ Clean .md   │            ║
║   │  Runs Tool  │         │  generate   │         │    File     │            ║
║   └─────────────┘         └─────────────┘         └─────────────┘            ║
║                                   │                                           ║
║                                   ▼                                           ║
║                    ┌──────────────────────────┐                              ║
║                    │     Pipeline Stages      │                              ║
║                    │  Scrape → Extract → MD   │                              ║
║                    └──────────────────────────┘                              ║
║                                                                               ║
║   USER_FLOW:                                                                  ║
║   1. Copy tutorial URL                                                        ║
║   2. Run: python -m src.cli generate --url "<URL>"                           ║
║   3. Wait ~10 seconds for processing                                          ║
║   4. Open output/guide.md → clean, formatted content                          ║
║                                                                               ║
║   VALUE_ADD: Automated extraction, <1 minute, clean output                   ║
║   DATA_FLOW: URL → Playwright → BeautifulSoup → Markdown file                ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### Interaction Changes

| Location        | Before               | After                    | User Impact              |
| --------------- | -------------------- | ------------------------ | ------------------------ |
| Terminal        | No tool exists       | `generate --url` command | Single command execution |
| Output folder   | Manual Word docs     | Structured .md files     | Consistent format        |
| Image handling  | Manual download      | References in markdown   | Auto-referenced          |

---

## Mandatory Reading

**CRITICAL: Implementation agent MUST read these files before starting any task:**

| Priority | File | Lines | Why Read This |
|----------|------|-------|---------------|
| P0 | `guides/technical_stack.md` | 155-168 | Web scraping stack patterns (Playwright + BS4) |
| P0 | `guides/technical_stack.md` | 382-551 | Logging standards - MUST follow exactly |
| P0 | `guides/technical_stack.md` | 555-568 | Path construction rules - CRITICAL |
| P0 | `guides/claude_md_template.md` | 99-133 | Configuration management pattern |
| P1 | `guides/technical_stack.md` | 184-212 | Pydantic Settings pattern |
| P1 | `guides/technical_stack.md` | 572-602 | Error handling pattern |
| P2 | `PRD.md` | 156-187 | Tool/feature specifications |

**External Documentation:**

| Source | Section | Why Needed |
|--------|---------|------------|
| [Playwright Python Docs](https://playwright.dev/python/docs/library) | Async API | Browser automation patterns |
| [BeautifulSoup Docs v4.13](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) | find/select methods | Content extraction |
| [Click Docs](https://click.palletsprojects.com/en/stable/) | Commands/Options | CLI structure |
| [markdownify GitHub](https://github.com/matthewwithanm/python-markdownify) | Custom converters | HTML→MD conversion |
| [Rich Docs](https://rich.readthedocs.io/) | Progress/Console | User feedback |

---

## Patterns to Mirror

**LOGGING_PATTERN:**
```python
# SOURCE: guides/technical_stack.md:386-397
# COPY THIS PATTERN:
import logging
import inspect
from src.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)  # ALWAYS use __name__

# Function entry - include function name
logger.debug(
    f" * {inspect.currentframe().f_code.co_name} > Starting with param={param}"
)

# Debug messages - use "    -> " prefix for operational flow
logger.debug("    -> Operation completed successfully")
```

**CONFIG_PATTERN:**
```python
# SOURCE: guides/technical_stack.md:184-206
# COPY THIS PATTERN:
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.app", ".env.keys", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )

    # Define fields with validation
    OUTPUT_DIR: str = Field(default="./output", description="Output directory")
    CACHE_DIR: str = Field(default="./cache", description="Cache directory")

# Singleton pattern
_settings = None
def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

**PATH_CONSTRUCTION:**
```python
# SOURCE: guides/technical_stack.md:555-568
# CRITICAL - ALWAYS use Path(a, b, c), NEVER use / operator
from pathlib import Path

# CORRECT
output_file = Path(settings.OUTPUT_DIR, "guides", "case_01", "guide.md")

# WRONG - Never do this
output_file = settings.OUTPUT_DIR / "guides" / "case_01" / "guide.md"
```

**ERROR_HANDLING:**
```python
# SOURCE: guides/technical_stack.md:572-602
# COPY THIS PATTERN:
class ScrapingError(Exception):
    """Base exception for scraping errors."""
    pass

class PageNotFoundError(ScrapingError):
    """Page URL returned 404."""
    pass

class ExtractionError(ScrapingError):
    """Failed to extract content from page."""
    pass

# Usage with context
try:
    result = scrape_page(url)
except Exception as e:
    error_context = {
        'url': url,
        'error_type': type(e).__name__
    }
    logger.error(f"Scraping failed: {e} | Context: {error_context}")
    raise
```

**ASYNC_BROWSER_PATTERN:**
```python
# SOURCE: External - Playwright docs
# COPY THIS PATTERN:
from playwright.async_api import async_playwright
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_browser():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            yield browser
        finally:
            await browser.close()

# Usage
async with get_browser() as browser:
    page = await browser.new_page()
    await page.goto(url)
    content = await page.content()
```

---

## Files to Change

| File                             | Action | Justification                            |
| -------------------------------- | ------ | ---------------------------------------- |
| `pyproject.toml`                 | UPDATE | Add dependencies                         |
| `src/__init__.py`                | CREATE | Package init                             |
| `src/core/__init__.py`           | CREATE | Core module init                         |
| `src/core/config.py`             | CREATE | Settings management                      |
| `src/core/errors.py`             | CREATE | Custom exceptions                        |
| `src/core/logging.py`            | CREATE | Logging configuration                    |
| `src/scraper.py`                 | CREATE | Playwright page fetcher                  |
| `src/extractor.py`               | CREATE | BeautifulSoup content extraction         |
| `src/sources/__init__.py`        | CREATE | Sources package init                     |
| `src/sources/base.py`            | CREATE | Base source adapter interface            |
| `src/sources/elecfreaks.py`      | CREATE | Elecfreaks-specific extraction rules     |
| `src/generator.py`               | CREATE | Markdown generation                      |
| `src/cli.py`                     | CREATE | Click CLI interface                      |
| `.env.app`                       | CREATE | Default configuration                    |

---

## NOT Building (Scope Limits)

Explicit exclusions to prevent scope creep:

- **Image downloading** - Phase 1 only references images by URL, downloading is Phase 2
- **Image enhancement** - Upscayl integration is Phase 2
- **Translation** - Dutch translation is Phase 2
- **Batch processing** - Index page parsing is Phase 3
- **Resume capability** - State persistence is Phase 3
- **Error recovery** - Advanced retry logic is Phase 3

---

## Step-by-Step Tasks

Execute in order. Each task is atomic and independently verifiable.

### Task 1: UPDATE `pyproject.toml` - Add dependencies

- **ACTION**: ADD all required dependencies to pyproject.toml
- **IMPLEMENT**:
  ```toml
  dependencies = [
      "playwright>=1.40",
      "beautifulsoup4>=4.12",
      "markdownify>=0.11",
      "click>=8.1",
      "rich>=13.7",
      "httpx>=0.26",
      "pydantic>=2.5",
      "pydantic-settings>=2.0",
      "python-dotenv>=1.0",
  ]

  [project.optional-dependencies]
  dev = [
      "pytest>=7.0",
      "pytest-asyncio>=0.21",
      "ruff>=0.1",
  ]
  ```
- **VALIDATE**: `uv sync && uv run python -c "import playwright; import bs4; import click; print('OK')"`

### Task 2: CREATE `src/__init__.py` - Package init

- **ACTION**: CREATE empty package init
- **IMPLEMENT**: Empty file or version string
- **VALIDATE**: `uv run python -c "import src; print('OK')"`

### Task 3: CREATE `src/core/__init__.py` - Core module init

- **ACTION**: CREATE core package init with exports
- **IMPLEMENT**:
  ```python
  from src.core.config import get_settings
  from src.core.errors import ScrapingError, ExtractionError

  __all__ = ["get_settings", "ScrapingError", "ExtractionError"]
  ```
- **VALIDATE**: `uv run python -c "from src.core import get_settings; print('OK')"`

### Task 4: CREATE `src/core/config.py` - Settings management

- **ACTION**: CREATE Pydantic settings class
- **IMPLEMENT**: Follow CONFIG_PATTERN from Patterns to Mirror section
- **FIELDS**:
  - `OUTPUT_DIR: str = "./output"`
  - `CACHE_DIR: str = "./cache"`
  - `RATE_LIMIT_SECONDS: float = 2.0`
  - `BROWSER_HEADLESS: bool = True`
  - `BROWSER_TIMEOUT: int = 30000`
  - `LOG_LEVEL: str = "INFO"`
- **VALIDATE**: `uv run python -c "from src.core.config import get_settings; s = get_settings(); print(s.OUTPUT_DIR)"`

### Task 5: CREATE `src/core/errors.py` - Custom exceptions

- **ACTION**: CREATE exception hierarchy
- **IMPLEMENT**: Follow ERROR_HANDLING pattern
- **CLASSES**:
  - `ScrapingError(Exception)` - Base for scraping errors
  - `PageNotFoundError(ScrapingError)` - 404 errors
  - `PageTimeoutError(ScrapingError)` - Timeout errors
  - `ExtractionError(Exception)` - Content extraction failures
  - `GenerationError(Exception)` - Markdown generation failures
- **VALIDATE**: `uv run python -c "from src.core.errors import ScrapingError; raise ScrapingError('test')" 2>&1 | grep -q ScrapingError && echo OK`

### Task 6: CREATE `src/core/logging.py` - Logging configuration

- **ACTION**: CREATE logging setup function
- **IMPLEMENT**: Follow LOGGING_PATTERN
- **FUNCTION**: `setup_logging(level: str = "INFO") -> None`
- **FEATURES**:
  - Configure root logger with format from technical_stack.md
  - Set up console handler with Rich formatting
  - Support LOG_LEVEL from settings
- **VALIDATE**: `uv run python -c "from src.core.logging import setup_logging; setup_logging(); print('OK')"`

### Task 7: CREATE `src/scraper.py` - Playwright page fetcher

- **ACTION**: CREATE async scraper module
- **IMPLEMENT**: Follow ASYNC_BROWSER_PATTERN
- **FUNCTIONS**:
  - `async def fetch_page(url: str) -> str` - Returns page HTML
  - `async def get_browser()` - Context manager for browser
- **FEATURES**:
  - Headless Chromium browser
  - Auto-wait for content
  - Timeout handling
  - Rate limiting between requests
- **GOTCHA**: Must run `playwright install chromium` after install
- **VALIDATE**: Create test that fetches a simple page

### Task 8: CREATE `src/sources/base.py` - Base source adapter

- **ACTION**: CREATE abstract base class for source adapters
- **IMPLEMENT**:
  ```python
  from abc import ABC, abstractmethod
  from bs4 import BeautifulSoup
  from dataclasses import dataclass

  @dataclass
  class ExtractedContent:
      title: str
      sections: list[dict]
      images: list[dict]
      metadata: dict

  class BaseSourceAdapter(ABC):
      @abstractmethod
      def can_handle(self, url: str) -> bool:
          """Check if this adapter can handle the given URL."""
          pass

      @abstractmethod
      def extract(self, soup: BeautifulSoup) -> ExtractedContent:
          """Extract content from parsed HTML."""
          pass
  ```
- **VALIDATE**: `uv run python -c "from src.sources.base import BaseSourceAdapter; print('OK')"`

### Task 9: CREATE `src/sources/elecfreaks.py` - Elecfreaks adapter

- **ACTION**: CREATE Elecfreaks-specific extraction rules
- **IMPLEMENT**: Inherit from BaseSourceAdapter
- **EXTRACTION_RULES**:
  - Main content: `article` or `div.theme-doc-markdown`
  - Remove: `.navbar`, `.sidebar`, `.footer`, `.breadcrumbs`, `.toc`
  - Title: First `h1` in content
  - Images: All `img` tags with `src` attribute
  - Sections: Split by `h2` headers
- **GOTCHA**: Elecfreaks uses Docusaurus - look for `.theme-doc-markdown` class
- **VALIDATE**: Test with sample HTML fixture

### Task 10: CREATE `src/extractor.py` - Content extraction orchestrator

- **ACTION**: CREATE extractor that uses source adapters
- **IMPLEMENT**:
  ```python
  from bs4 import BeautifulSoup
  from src.sources.elecfreaks import ElecfreaksAdapter
  from src.sources.base import ExtractedContent

  class ContentExtractor:
      def __init__(self):
          self.adapters = [ElecfreaksAdapter()]

      def extract(self, html: str, url: str) -> ExtractedContent:
          soup = BeautifulSoup(html, "html.parser")
          for adapter in self.adapters:
              if adapter.can_handle(url):
                  return adapter.extract(soup)
          raise ExtractionError(f"No adapter for URL: {url}")
  ```
- **VALIDATE**: `uv run python -c "from src.extractor import ContentExtractor; print('OK')"`

### Task 11: CREATE `src/generator.py` - Markdown generation

- **ACTION**: CREATE Markdown generator
- **IMPLEMENT**:
  - Use markdownify for HTML→MD conversion
  - Custom image handling to preserve URLs
  - Section formatting with headers
- **OUTPUT_FORMAT**:
  ```markdown
  # {title}

  ## {section_name}
  {section_content}

  ![{alt}]({image_url})
  ```
- **VALIDATE**: Test with sample ExtractedContent

### Task 12: CREATE `src/cli.py` - Click CLI interface

- **ACTION**: CREATE CLI with generate command
- **IMPLEMENT**:
  ```python
  import click
  import asyncio
  from rich.console import Console
  from pathlib import Path

  @click.group()
  def cli():
      """CoderDojo Guide Generator - Create printable guides from online tutorials."""
      pass

  @cli.command()
  @click.option("--url", required=True, help="Tutorial page URL")
  @click.option("--output", "-o", default="./output", help="Output directory")
  @click.option("--verbose", "-v", is_flag=True, help="Verbose output")
  def generate(url: str, output: str, verbose: bool):
      """Generate a guide from a single tutorial URL."""
      asyncio.run(_generate(url, output, verbose))
  ```
- **FEATURES**:
  - Rich console output for progress
  - Error handling with helpful messages
  - Creates output directory if needed
- **VALIDATE**: `uv run python -m src.cli --help`

### Task 13: CREATE `.env.app` - Default configuration

- **ACTION**: CREATE default environment file
- **IMPLEMENT**:
  ```bash
  # CoderDojo Guide Generator Configuration

  # Output settings
  OUTPUT_DIR="./output"
  CACHE_DIR="./cache"

  # Scraping settings
  RATE_LIMIT_SECONDS=2
  BROWSER_HEADLESS=true
  BROWSER_TIMEOUT=30000

  # Logging
  LOG_LEVEL="INFO"
  LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  ```
- **VALIDATE**: `cat .env.app && echo OK`

### Task 14: INTEGRATION TEST - End-to-end flow

- **ACTION**: TEST full pipeline with real URL
- **TEST_URL**: `https://wiki.elecfreaks.com/en/microbit/building-blocks/nezha-inventors-kit/Nezha_Inventor_s_kit_for_microbit_case_01`
- **STEPS**:
  1. Run: `uv run python -m src.cli generate --url "<URL>" -v`
  2. Verify output file created in `./output/`
  3. Verify Markdown contains title, sections, image references
  4. Verify no navigation/sidebar content in output
- **EXPECTED**: Clean Markdown file with tutorial content

---

## Testing Strategy

### Unit Tests to Write

| Test File                                | Test Cases                 | Validates      |
| ---------------------------------------- | -------------------------- | -------------- |
| `tests/test_config.py`                   | settings load, defaults    | Configuration  |
| `tests/test_scraper.py`                  | fetch success, timeout     | Page fetching  |
| `tests/test_extractor.py`                | extract content, no match  | Extraction     |
| `tests/test_elecfreaks.py`               | parse sample HTML          | Elecfreaks rules |
| `tests/test_generator.py`                | markdown output            | Generation     |
| `tests/test_cli.py`                      | command execution          | CLI interface  |

### Edge Cases Checklist

- [ ] Invalid URL format
- [ ] URL returns 404
- [ ] Page timeout
- [ ] No main content found
- [ ] No images in page
- [ ] Special characters in title
- [ ] Very long page content
- [ ] Malformed HTML

---

## Validation Commands

### Level 1: STATIC_ANALYSIS

```bash
uv run ruff check src/ && uv run ruff format --check src/
```

**EXPECT**: Exit 0, no errors or warnings

### Level 2: UNIT_TESTS

```bash
uv run pytest tests/ -v
```

**EXPECT**: All tests pass

### Level 3: FULL_SUITE

```bash
uv run pytest tests/ -v && uv run ruff check src/
```

**EXPECT**: All tests pass, no lint errors

### Level 4: INTEGRATION_VALIDATION

```bash
# Install Playwright browser
uv run playwright install chromium

# Run integration test
uv run python -m src.cli generate \
  --url "https://wiki.elecfreaks.com/en/microbit/building-blocks/nezha-inventors-kit/Nezha_Inventor_s_kit_for_microbit_case_01" \
  --output ./test_output \
  -v
```

**EXPECT**: Markdown file created with tutorial content

---

## Acceptance Criteria

- [ ] `generate` command accepts URL and produces Markdown output
- [ ] Output contains tutorial title as H1
- [ ] Output contains all section headings (Materials, Assembly, etc.)
- [ ] Output contains image references with URLs
- [ ] No navigation, sidebar, or footer content in output
- [ ] CLI shows progress/status during execution
- [ ] Errors are handled gracefully with helpful messages
- [ ] All unit tests pass
- [ ] Code follows project logging standards
- [ ] Code follows project path construction rules

---

## Completion Checklist

- [ ] All 14 tasks completed in dependency order
- [ ] Each task validated immediately after completion
- [ ] Level 1: Static analysis passes
- [ ] Level 2: Unit tests pass
- [ ] Level 3: Full test suite succeeds
- [ ] Level 4: Integration test produces valid output
- [ ] All acceptance criteria met

---

## Risks and Mitigations

| Risk               | Likelihood   | Impact       | Mitigation                              |
| ------------------ | ------------ | ------------ | --------------------------------------- |
| Elecfreaks page structure changes | MEDIUM | HIGH | Test with fixtures; modular adapter design |
| Playwright install issues | LOW | MEDIUM | Document install steps; add to setup guide |
| Rate limiting by server | MEDIUM | LOW | Built-in delay between requests |
| Missing content selectors | MEDIUM | MEDIUM | Fallback selectors; detailed logging |

---

## Notes

**Why Playwright over requests?**
The Elecfreaks wiki uses Docusaurus which may render content with JavaScript. Playwright ensures we get the fully-rendered page. If we later find the content is static, we could optimize with requests+BS4 directly.

**Image handling strategy:**
Phase 1 only references images by their original URLs. Phase 2 will download and enhance them. This separation keeps Phase 1 focused and testable.

**Adapter pattern rationale:**
Using adapters (src/sources/) allows adding support for other kit manufacturers (Keyestudio, DFRobot) in the future without modifying core extraction logic.
