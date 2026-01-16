# Feature: Phase 2 - Enhancement Pipeline (Image & Translation)

## Summary

Add image downloading, Upscayl-based image enhancement, and Dutch translation to the guide generation pipeline. This transforms raw extracted content into print-ready Dutch guides with high-quality local images. The implementation extends the existing pipeline architecture with three new stages: download → enhance → translate.

## User Story

As a CoderDojo volunteer
I want the generated guides to have enhanced images and be translated to Dutch
So that I can print professional-quality guides for Dutch-speaking students

## Problem Statement

Phase 1 produces Markdown with remote image URLs and English text. This is not print-ready because:
1. Images reference external CDN URLs (unreliable for printing)
2. Image quality from the wiki is often low-resolution
3. Instructions are in English, but students speak Dutch

## Solution Statement

Extend the pipeline with three new processing stages:
1. **Image Downloader** - Download all images locally using httpx (async)
2. **Image Enhancer** - Upscale images using Upscayl CLI (4x resolution)
3. **Translator** - Translate content to Dutch using deep-translator (GoogleTranslator)

Update the generator to reference local images and output translated content.

## Metadata

| Field            | Value                                             |
| ---------------- | ------------------------------------------------- |
| Type             | ENHANCEMENT                                       |
| Complexity       | HIGH                                              |
| Systems Affected | Downloader (new), Enhancer (new), Translator (new), Generator, CLI, Config |
| Dependencies     | deep-translator ^1.11, upscayl-ncnn (external binary) |
| Estimated Tasks  | 12                                                |

---

## UX Design

### Before State

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                              BEFORE STATE (Phase 1)                            ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   ┌─────────────┐         ┌─────────────┐         ┌─────────────┐            ║
║   │   generate  │ ──────► │   Extract   │ ──────► │  Save .md   │            ║
║   │   --url X   │         │   Content   │         │  (English)  │            ║
║   └─────────────┘         └─────────────┘         └─────────────┘            ║
║                                                                               ║
║   OUTPUT:                                                                     ║
║   - Markdown with remote image URLs: ![](https://cdn.aliyun.com/...)         ║
║   - English text only                                                         ║
║   - Low-resolution images                                                     ║
║                                                                               ║
║   PAIN_POINTS:                                                                ║
║   - Remote URLs may break during printing                                     ║
║   - Low-res images look bad when printed                                      ║
║   - English text not suitable for Dutch students                              ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### After State

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                              AFTER STATE (Phase 2)                             ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   ║
║   │   generate  │───►│   Extract   │───►│  Download   │───►│  Enhance    │   ║
║   │   --url X   │    │   Content   │    │   Images    │    │  (Upscayl)  │   ║
║   └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘   ║
║                                                   │                │          ║
║                                                   ▼                ▼          ║
║   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────┐      ║
║   │  Save .md   │◄───│  Translate  │◄───│   images/case_01_*.png      │      ║
║   │  (Dutch)    │    │  (Dutch)    │    │   (local, enhanced)         │      ║
║   └─────────────┘    └─────────────┘    └─────────────────────────────┘      ║
║                                                                               ║
║   OUTPUT:                                                                     ║
║   - Markdown with local image paths: ![](images/case_01_step_1.png)          ║
║   - Dutch translated text                                                     ║
║   - High-resolution enhanced images (4x upscaled)                            ║
║                                                                               ║
║   VALUE_ADD:                                                                  ║
║   - Fully offline printable guides                                            ║
║   - Professional print quality                                                ║
║   - Dutch language accessible to students                                     ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### Interaction Changes

| Location | Before | After | User Impact |
|----------|--------|-------|-------------|
| CLI | `generate --url` only | `generate --url [--no-enhance] [--no-translate]` | Control pipeline stages |
| Output | Single .md file | .md + images/ folder | Complete guide package |
| Images | Remote URLs | Local enhanced files | Print-ready quality |
| Language | English only | Dutch translated | Student accessible |

---

## Mandatory Reading

**CRITICAL: Implementation agent MUST read these files before starting any task:**

| Priority | File | Lines | Why Read This |
|----------|------|-------|---------------|
| P0 | `src/scraper.py` | 18-34, 91-109 | Async context manager and rate limiting patterns |
| P0 | `src/generator.py` | 19-40, 129-161 | Markdown converter and file saving patterns |
| P0 | `src/core/errors.py` | all | Exception hierarchy to extend |
| P0 | `src/core/config.py` | all | Settings pattern to extend |
| P1 | `src/sources/base.py` | 10-18 | ExtractedContent dataclass to extend |
| P1 | `src/cli.py` | 65-141 | CLI async pattern with progress |
| P2 | `tests/test_generator.py` | all | Test patterns to follow |

**External Documentation:**

| Source | Section | Why Needed |
|--------|---------|------------|
| [deep-translator PyPI](https://pypi.org/project/deep-translator/) | GoogleTranslator usage | Translation API |
| [deep-translator Docs](https://deep-translator.readthedocs.io/) | Language codes | Dutch = 'nl' |
| [httpx Clients](https://www.python-httpx.org/advanced/clients/) | AsyncClient streaming | Image download |
| [Upscayl GitHub](https://github.com/upscayl/upscayl) | CLI args | Enhancement integration |
| [upscayl-ncnn](https://github.com/upscayl/upscayl-ncnn) | -i -o -s flags | CLI interface |

---

## Patterns to Mirror

**ASYNC_DOWNLOAD_PATTERN:**
```python
# SOURCE: src/scraper.py:91-109
# ADAPT THIS PATTERN for image downloading:
async def download_image(url: str, output_path: Path, client: httpx.AsyncClient) -> bool:
    """Download a single image."""
    logger.debug(f" * {inspect.currentframe().f_code.co_name} > Downloading: {url}")

    try:
        async with client.stream("GET", url) as response:
            if response.status_code >= 400:
                logger.warning(f"    -> Failed to download: HTTP {response.status_code}")
                return False

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)

        logger.debug(f"    -> Saved to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"    -> Download failed: {e}")
        return False
```

**ERROR_HANDLING_PATTERN:**
```python
# SOURCE: src/core/errors.py:1-27
# EXTEND with new exceptions:
class DownloadError(Exception):
    """Failed to download image."""
    pass

class EnhancementError(Exception):
    """Failed to enhance image with Upscayl."""
    pass

class TranslationError(Exception):
    """Failed to translate content."""
    pass
```

**CONFIG_EXTENSION_PATTERN:**
```python
# SOURCE: src/core/config.py:14-29
# ADD these fields to Settings class:
    # Image settings
    IMAGE_DOWNLOAD_TIMEOUT: int = Field(default=30, description="Image download timeout in seconds")
    IMAGE_OUTPUT_DIR: str = Field(default="images", description="Subdirectory for images")

    # Enhancement settings
    UPSCAYL_PATH: str = Field(default="C:\\Program Files\\Upscayl\\resources\\bin\\upscayl-bin.exe", description="Path to Upscayl binary")
    UPSCAYL_SCALE: int = Field(default=4, description="Upscale factor (2 or 4)")
    UPSCAYL_MODEL: str = Field(default="realesrgan-x4plus", description="Upscayl model name")
    ENHANCE_IMAGES: bool = Field(default=True, description="Enable image enhancement")

    # Translation settings
    TRANSLATE_ENABLED: bool = Field(default=True, description="Enable Dutch translation")
    TRANSLATION_SOURCE: str = Field(default="en", description="Source language")
    TRANSLATION_TARGET: str = Field(default="nl", description="Target language (Dutch)")
```

**LOGGING_PATTERN:**
```python
# SOURCE: src/scraper.py:25, 51, 71
# COPY THIS PATTERN exactly:
logger.debug(f" * {inspect.currentframe().f_code.co_name} > Starting process")
logger.debug("    -> Operation completed successfully")
logger.debug(f"    -> Processed {count} items")
```

**CLI_OPTION_PATTERN:**
```python
# SOURCE: src/cli.py:152-156
# ADD new options:
@click.option("--no-enhance", is_flag=True, help="Skip image enhancement")
@click.option("--no-translate", is_flag=True, help="Skip Dutch translation")
```

**TEST_PATTERN:**
```python
# SOURCE: tests/test_generator.py:9-24
# FOLLOW this structure:
def test_translate_basic():
    """Test basic translation to Dutch."""
    translator = ContentTranslator()

    content = ExtractedContent(
        title="Test Title",
        sections=[{"heading": "Introduction", "level": 2, "content": []}],
        images=[],
        metadata={},
    )

    translated = translator.translate(content)
    assert translated.metadata.get("language") == "nl"
```

---

## Files to Change

| File | Action | Justification |
|------|--------|---------------|
| `pyproject.toml` | UPDATE | Add deep-translator dependency |
| `src/core/errors.py` | UPDATE | Add DownloadError, EnhancementError, TranslationError |
| `src/core/config.py` | UPDATE | Add image, enhancement, translation settings |
| `.env.app` | UPDATE | Add new configuration defaults |
| `src/sources/base.py` | UPDATE | Extend ExtractedContent with local_path field |
| `src/downloader.py` | CREATE | Image downloading module |
| `src/enhancer.py` | CREATE | Upscayl integration module |
| `src/translator.py` | CREATE | Dutch translation module |
| `src/generator.py` | UPDATE | Use local image paths in markdown |
| `src/cli.py` | UPDATE | Add --no-enhance, --no-translate flags |
| `tests/test_downloader.py` | CREATE | Downloader tests |
| `tests/test_translator.py` | CREATE | Translator tests |

---

## NOT Building (Scope Limits)

Explicit exclusions to prevent scope creep:

- **PDF generation** - Phase 4 or post-MVP
- **Custom translation glossary** - Phase 4
- **Multiple target languages** - Post-MVP (Dutch only for now)
- **Image caching** - Phase 3 (batch processing)
- **Resume capability** - Phase 3
- **Batch processing** - Phase 3

---

## Step-by-Step Tasks

Execute in order. Each task is atomic and independently verifiable.

### Task 1: UPDATE `pyproject.toml` - Add deep-translator dependency

- **ACTION**: ADD deep-translator to dependencies
- **IMPLEMENT**:
  ```toml
  dependencies = [
      # ... existing deps ...
      "deep-translator>=1.11",
  ]
  ```
- **VALIDATE**: `uv sync && uv run python -c "from deep_translator import GoogleTranslator; print('OK')"`

### Task 2: UPDATE `src/core/errors.py` - Add new exceptions

- **ACTION**: ADD three new exception classes
- **IMPLEMENT**:
  ```python
  class DownloadError(Exception):
      """Failed to download image."""
      pass

  class EnhancementError(Exception):
      """Failed to enhance image with Upscayl."""
      pass

  class TranslationError(Exception):
      """Failed to translate content."""
      pass
  ```
- **MIRROR**: `src/core/errors.py:1-27` - follow existing exception pattern
- **VALIDATE**: `uv run python -c "from src.core.errors import DownloadError, EnhancementError, TranslationError; print('OK')"`

### Task 3: UPDATE `src/core/config.py` - Add new settings

- **ACTION**: ADD image, enhancement, and translation settings to Settings class
- **IMPLEMENT**: Add fields per CONFIG_EXTENSION_PATTERN above
- **MIRROR**: `src/core/config.py:14-29` - follow existing Field pattern
- **GOTCHA**: Use double backslashes for Windows paths in defaults
- **VALIDATE**: `uv run python -c "from src.core.config import get_settings; s = get_settings(); print(s.UPSCAYL_PATH)"`

### Task 4: UPDATE `.env.app` - Add new configuration

- **ACTION**: ADD new environment variables
- **IMPLEMENT**:
  ```bash
  # Image settings
  IMAGE_DOWNLOAD_TIMEOUT=30
  IMAGE_OUTPUT_DIR="images"

  # Enhancement settings (Upscayl)
  UPSCAYL_PATH="C:\\Program Files\\Upscayl\\resources\\bin\\upscayl-bin.exe"
  UPSCAYL_SCALE=4
  UPSCAYL_MODEL="realesrgan-x4plus"
  ENHANCE_IMAGES=true

  # Translation settings
  TRANSLATE_ENABLED=true
  TRANSLATION_SOURCE="en"
  TRANSLATION_TARGET="nl"
  ```
- **VALIDATE**: `cat .env.app | grep -q UPSCAYL_PATH && echo OK`

### Task 5: UPDATE `src/sources/base.py` - Extend ExtractedContent

- **ACTION**: ADD local_path field to image dict structure
- **IMPLEMENT**: Update docstring to document new field
  ```python
  @dataclass
  class ExtractedContent:
      """Container for extracted tutorial content.

      Images list contains dicts with:
          - src: Remote URL
          - alt: Alt text
          - title: Title attribute
          - local_path: Local file path (added by downloader)
          - enhanced_path: Enhanced file path (added by enhancer)
      """
      title: str
      sections: list[dict[str, Any]] = field(default_factory=list)
      images: list[dict[str, str]] = field(default_factory=list)
      metadata: dict[str, Any] = field(default_factory=dict)
  ```
- **GOTCHA**: Don't change dataclass fields - just add documentation. Paths stored in dict.
- **VALIDATE**: `uv run python -c "from src.sources.base import ExtractedContent; print('OK')"`

### Task 6: CREATE `src/downloader.py` - Image downloading module

- **ACTION**: CREATE async image downloader
- **IMPLEMENT**:
  - `async def download_images(content: ExtractedContent, output_dir: Path) -> ExtractedContent`
  - Use httpx.AsyncClient with streaming for large files
  - Generate filenames from slugified alt text or index
  - Update content.images with local_path
  - Handle failures gracefully (skip failed images, log warning)
- **MIRROR**: `src/scraper.py:91-109` - async pattern with rate limiting
- **IMPORTS**: `import httpx`, `from pathlib import Path`
- **GOTCHA**: Use streaming for large files: `async with client.stream("GET", url)`
- **VALIDATE**: `uv run python -c "from src.downloader import download_images; print('OK')"`

### Task 7: CREATE `src/enhancer.py` - Upscayl integration module

- **ACTION**: CREATE image enhancement using Upscayl CLI
- **IMPLEMENT**:
  - `def enhance_image(input_path: Path, output_path: Path) -> bool`
  - `def enhance_all_images(content: ExtractedContent, output_dir: Path) -> ExtractedContent`
  - Use subprocess.run with timeout
  - Skip enhancement if file too small (< 10KB)
  - Update content.images with enhanced_path
  - Fallback to original if enhancement fails
- **MIRROR**: See subprocess pattern in Patterns to Mirror
- **IMPORTS**: `import subprocess`, `from pathlib import Path`
- **GOTCHA**: Upscayl CLI: `upscayl-bin -i input.png -o output.png -s 4 -n realesrgan-x4plus`
- **GOTCHA**: Check if Upscayl exists before running, skip gracefully if not found
- **VALIDATE**: `uv run python -c "from src.enhancer import enhance_image; print('OK')"`

### Task 8: CREATE `src/translator.py` - Dutch translation module

- **ACTION**: CREATE translation using deep-translator
- **IMPLEMENT**:
  - `def translate_text(text: str, source: str = "en", target: str = "nl") -> str`
  - `def translate_content(content: ExtractedContent) -> ExtractedContent`
  - Translate: title, section headings, section content text
  - Preserve: image alt text, code blocks, URLs
  - Add metadata["language"] = "nl"
  - Handle rate limits with retry
- **MIRROR**: `src/extractor.py:34-65` - error handling pattern
- **IMPORTS**: `from deep_translator import GoogleTranslator`
- **GOTCHA**: GoogleTranslator has rate limits - add small delay between calls
- **GOTCHA**: Don't translate technical terms in code blocks
- **VALIDATE**: `uv run python -c "from src.translator import translate_text; print(translate_text('Hello'))"`

### Task 9: UPDATE `src/generator.py` - Use local image paths

- **ACTION**: UPDATE GuideMarkdownConverter to prefer local paths
- **IMPLEMENT**:
  - Check for local_path or enhanced_path in image dict
  - Use local path if available, fall back to remote URL
  - Add function to update image references in content
- **MIRROR**: `src/generator.py:19-40` - existing convert_img method
- **GOTCHA**: Handle both enhanced and non-enhanced local paths
- **VALIDATE**: Integration test will verify

### Task 10: UPDATE `src/cli.py` - Add new CLI options

- **ACTION**: ADD --no-enhance and --no-translate flags
- **IMPLEMENT**:
  - Add options to generate command
  - Update _generate() to call downloader, enhancer, translator
  - Update progress reporting for new stages
  - Handle errors gracefully for each stage
- **MIRROR**: `src/cli.py:87-116` - progress pattern
- **GOTCHA**: Each stage should be independently skippable
- **VALIDATE**: `uv run python -m src.cli generate --help | grep -q no-enhance && echo OK`

### Task 11: CREATE `tests/test_downloader.py` - Downloader tests

- **ACTION**: CREATE unit tests for downloader
- **IMPLEMENT**:
  - test_download_single_image (mock httpx)
  - test_download_handles_404
  - test_download_updates_content
  - test_filename_generation
- **MIRROR**: `tests/test_generator.py` - test structure
- **GOTCHA**: Use pytest-httpx or mock for HTTP calls
- **VALIDATE**: `uv run pytest tests/test_downloader.py -v`

### Task 12: CREATE `tests/test_translator.py` - Translator tests

- **ACTION**: CREATE unit tests for translator
- **IMPLEMENT**:
  - test_translate_basic_text
  - test_translate_preserves_code
  - test_translate_content_updates_metadata
  - test_translate_handles_errors
- **MIRROR**: `tests/test_generator.py` - test structure
- **GOTCHA**: Mock GoogleTranslator to avoid actual API calls in tests
- **VALIDATE**: `uv run pytest tests/test_translator.py -v`

---

## Testing Strategy

### Unit Tests to Write

| Test File | Test Cases | Validates |
|-----------|------------|-----------|
| `tests/test_downloader.py` | download success, 404 handling, filename gen | Image downloading |
| `tests/test_enhancer.py` | enhance success, skip small, fallback | Upscayl integration |
| `tests/test_translator.py` | translate text, preserve code, error handling | Dutch translation |

### Edge Cases Checklist

- [ ] Image URL returns 404
- [ ] Image URL times out
- [ ] Upscayl binary not found
- [ ] Upscayl enhancement fails
- [ ] Translation API rate limited
- [ ] Very long text to translate
- [ ] Text with code blocks (should not translate)
- [ ] Empty content to translate
- [ ] Non-ASCII characters in image filename

---

## Validation Commands

### Level 1: STATIC_ANALYSIS

```bash
uv run ruff check src/ && uv run ruff format --check src/
```

**EXPECT**: Exit 0, no errors

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
# Test with enhancement (requires Upscayl installed)
uv run python -m src.cli generate \
  --url "https://wiki.elecfreaks.com/en/microbit/building-blocks/nezha-inventors-kit/Nezha_Inventor_s_kit_for_microbit_case_01" \
  --output ./test_output \
  -v

# Test without enhancement
uv run python -m src.cli generate \
  --url "https://wiki.elecfreaks.com/en/microbit/building-blocks/nezha-inventors-kit/Nezha_Inventor_s_kit_for_microbit_case_01" \
  --output ./test_output_no_enhance \
  --no-enhance \
  -v
```

**EXPECT**:
- Output folder contains .md file and images/ subdirectory
- Markdown references local image paths
- Content is translated to Dutch
- Images are enhanced (when --no-enhance not used)

---

## Acceptance Criteria

- [ ] Images are downloaded locally to images/ subdirectory
- [ ] Downloaded images are enhanced with Upscayl (4x resolution)
- [ ] Content (title, headings, text) is translated to Dutch
- [ ] Markdown output references local image paths
- [ ] `--no-enhance` flag skips image enhancement
- [ ] `--no-translate` flag skips translation
- [ ] CLI shows progress for each pipeline stage
- [ ] Graceful fallback when Upscayl not installed
- [ ] All unit tests pass
- [ ] Generated guide is print-ready

---

## Completion Checklist

- [ ] All 12 tasks completed in dependency order
- [ ] Each task validated immediately after completion
- [ ] Level 1: Static analysis passes
- [ ] Level 2: Unit tests pass
- [ ] Level 3: Full test suite succeeds
- [ ] Level 4: Integration test produces valid output
- [ ] All acceptance criteria met

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Upscayl not installed on user machine | HIGH | MEDIUM | Graceful fallback - skip enhancement, warn user |
| Translation API rate limiting | MEDIUM | LOW | Add delays between calls, retry with backoff |
| Large images cause timeout | MEDIUM | LOW | Streaming download, configurable timeout |
| Upscayl CLI interface changes | LOW | HIGH | Pin version, document exact CLI args used |
| Translation quality issues | MEDIUM | MEDIUM | Log warnings, allow --no-translate override |

---

## Notes

**Upscayl Binary Location:**
- Windows: `C:\Program Files\Upscayl\resources\bin\upscayl-bin.exe`
- The CLI takes: `-i input -o output -s scale -n model`
- Models available: realesrgan-x4plus, realesrgan-x4plus-anime, etc.

**Translation Strategy:**
- Use GoogleTranslator from deep-translator (free, no API key needed)
- Dutch language code: 'nl'
- Preserve technical terms by not translating content inside code blocks
- Add small delay (0.5s) between translation calls to avoid rate limits

**Image Filename Convention:**
- Use slugified alt text if available
- Fall back to index-based naming: `image_001.png`, `image_002.png`
- Preserve original extension

**Pipeline Order:**
1. Extract content (Phase 1)
2. Download images (new)
3. Enhance images (new)
4. Translate content (new)
5. Generate markdown (updated)
6. Save output (existing)
