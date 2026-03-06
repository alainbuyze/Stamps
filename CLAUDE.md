# Stamp Collection Toolset

An AI-powered CLI application to manage a space-themed stamp collection: build a searchable RAG database from Colnect, identify physical stamps via camera, and migrate collections from LASTDODO.

## Tech Stack

- **Language:** Python 3.11+
- **Package Manager:** UV
- **CLI:** Click
- **Console UI:** Rich (progress bars, tables, formatted output)
- **Configuration:** Pydantic Settings (.env files)
- **Local Database:** SQLite (built-in)
- **Vector Database:** Supabase + pgvector
- **Embeddings:** OpenAI text-embedding-3-small
- **Vision/Detection:** Groq API (primary) + Claude Haiku (fallback)
- **Vision/Description:** Groq API (llama-3.2-11b-vision)
- **Web Scraping:** Playwright + BeautifulSoup4
- **Browser Automation:** Playwright CDP (Chrome DevTools Protocol)
- **Image Processing:** Pillow, OpenCV (preprocessing only)
- **HTTP Client:** httpx

Review technical standards in `@guides\technical_stack.md`

## Project Structure

```
src/
├── __init__.py
├── cli.py                        # Click CLI entry point
│
├── core/                         # Shared infrastructure
│   ├── __init__.py
│   ├── config.py                 # Pydantic Settings
│   ├── errors.py                 # Custom exceptions
│   ├── logging.py                # Rich logging setup
│   └── database.py               # SQLite connection & operations
│
├── scraping/                     # Web scraping module
│   ├── __init__.py
│   ├── browser.py                # Playwright browser manager
│   ├── colnect.py                # Colnect stamp catalog scraper
│   └── lastdodo.py               # LASTDODO collection scraper
│
├── rag/                          # RAG database module
│   ├── __init__.py
│   ├── embeddings.py             # OpenAI embedding generation
│   ├── supabase_client.py        # Supabase connection & operations
│   ├── indexer.py                # Index stamps into RAG
│   └── search.py                 # Similarity search
│
├── vision/                       # Vision & identification module
│   ├── __init__.py
│   ├── preprocessing.py          # Image preprocessing strategies
│   ├── vision_detector.py        # Hybrid Groq/Claude detection
│   ├── identification_pipeline.py # Single/multi stamp modes
│   ├── inspection.py             # Inspection viewer & CLI
│   └── camera.py                 # OpenCV camera capture
│
├── feedback/                     # Scan feedback & visualization
│   ├── __init__.py
│   ├── models.py                 # DetectionFeedback, ScanSession
│   ├── visualizer.py             # Annotated image generator
│   ├── session_manager.py        # Session persistence
│   └── console.py                # Rich console output
│
├── migration/                    # LASTDODO → Colnect migration
│   ├── __init__.py
│   ├── matcher.py                # Catalog number matching
│   ├── mapper.py                 # Condition mapping logic
│   ├── importer.py               # Import orchestration
│   └── review.py                 # CLI manual review interface
│
└── colnect_api/                  # Browser automation for Colnect
    ├── __init__.py
    ├── session.py                # CDP session management
    └── actions.py                # Add to collection, etc.

config/
└── llava_prompt.txt              # Configurable vision prompt template

data/                             # Runtime data (gitignored)
├── stamps.db                     # SQLite database
├── inspection/                   # All intermediate inspection data
├── sessions/                     # Scan session archives
├── missed_stamps/                # Stamps for re-ingestion
└── logs/                         # Application logs

tests/                            # Test files
guides/                           # Development documentation
```

## Common Commands

### Setup

```powershell
# Install dependencies
uv sync

# Install Playwright browser (for scraping)
playwright install chromium

# Initialize database and verify connections
uv run stamp-tools init
```

### Scraping

```powershell
# Scrape Colnect for space-themed stamps (uses default themes)
uv run stamp-tools scrape colnect

# Scrape with specific themes
uv run stamp-tools scrape colnect --themes "Space,Astronomy,Rockets"

# Scrape specific country/year (partial re-ingestion)
uv run stamp-tools scrape colnect --country "Australia" --year 2021

# Resume interrupted scrape
uv run stamp-tools scrape colnect --resume

# Scrape LASTDODO collection (requires logged-in Chrome session)
uv run stamp-tools scrape lastdodo
```

### RAG Database

```powershell
# Index scraped stamps into Supabase RAG
uv run stamp-tools rag index

# Re-index specific country/year
uv run stamp-tools rag index --country "Australia" --year 2021

# Regenerate descriptions (re-run Groq vision)
uv run stamp-tools rag index --regenerate

# Manual search (for testing)
uv run stamp-tools rag search --query "rocket launch astronaut"

# Show RAG statistics
uv run stamp-tools rag stats
```

### Stamp Identification

```powershell
# Identify stamps from camera (auto-detects single vs multi)
uv run stamp-tools identify camera

# Identify from image file
uv run stamp-tools identify image --path "C:\path\to\photo.jpg"

# Force single-stamp mode (skip detection, go direct to RAG)
uv run stamp-tools identify image --path "stamp.jpg" --mode single

# Force multi-stamp mode (album page)
uv run stamp-tools identify image --path "album.jpg" --mode multi

# Auto-add confirmed matches to Colnect
uv run stamp-tools identify camera --add-to-colnect
```

### Inspection & Debug

```powershell
# List recent inspection sessions
uv run stamp-tools inspect sessions

# View session details
uv run stamp-tools inspect session <session_id>

# View specific identification details
uv run stamp-tools inspect identification <session_id> <identification_id>

# Open session images in viewer
uv run stamp-tools inspect open-images <session_id>

# Test preprocessing strategies on an image
uv run stamp-tools inspect preprocess-test path/to/image.jpg
```

### Review & Feedback

```powershell
# Review missed stamps (no RAG match)
uv run stamp-tools review missed

# List recent scan sessions
uv run stamp-tools review sessions

# Open specific session details
uv run stamp-tools review session <session_id>
```

### LASTDODO Migration

```powershell
# Match LASTDODO items to Colnect catalog
uv run stamp-tools migrate match

# Dry-run import (simulate without updating Colnect)
uv run stamp-tools migrate import --dry-run

# Live import to Colnect
uv run stamp-tools migrate import

# Manual review queue for unmatched items
uv run stamp-tools migrate review

# Show migration status
uv run stamp-tools migrate status
```

### Configuration

```powershell
# Show current configuration
uv run stamp-tools config show

# Validate all settings and connections
uv run stamp-tools config validate
```

### Testing & Linting

```powershell
uv run pytest
uv run ruff check src/
uv run ruff format src/
```

## Configuration

### Environment Files

| File | Purpose | Committed |
|------|---------|-----------|
| `.env.app` | Application defaults | ✅ Yes |
| `.env.keys` | API keys and secrets | ❌ No (gitignored) |
| `.env.local` | User-specific overrides | ❌ No (gitignored) |

### Key Settings (.env.app)

```env
# Database
DATABASE_PATH=data/stamps.db

# Scraping
SCRAPE_DELAY_SECONDS=1.5
SCRAPE_ERROR_BEHAVIOR=skip

# RAG
RAG_MATCH_AUTO_THRESHOLD=0.9
RAG_MATCH_MIN_THRESHOLD=0.5

# Vision LLM Detection
DETECTION_PRIMARY_PROVIDER=groq
DETECTION_FALLBACK_PROVIDER=claude_haiku
DETECTION_ENABLE_FALLBACK=true

# Preprocessing
PREPROCESSING_STRATEGY=compress
PREPROCESSING_MAX_DIM=640
PREPROCESSING_JPEG_QUALITY=85

# Identification
IDENTIFICATION_DEFAULT_MODE=auto

# Inspection
SAVE_INTERMEDIATES=true
INSPECTION_DIR=data/inspection

# Browser Automation
CHROME_CDP_URL=http://localhost:9222
```

### Secrets (.env.keys)

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-service-role-key
OPENAI_API_KEY=sk-xxxxx
GROQ_API_KEY=gsk_xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

## Code Conventions

- **Type hints** on all function signatures
- **Pydantic** for configuration and data validation
- **Rich** for all console output (progress bars, tables, colors)
- **Pathlib** for all file operations (cross-platform)
- **Docstrings** on all public functions and classes (see documentation conventions below)
- Functions focused and testable
- Logging at appropriate levels (DEBUG for flow, INFO for status, ERROR for failures)

### Documentation Standards

**Review full documentation conventions in `@guides\documentation_conventions.md`**

Every module MUST include:

1. **Module docstring** with: Goal, How to Use, Function Tree, Configuration Parameters table, Usage Examples
2. **`if __name__ == "__main__":` block** with hardcoded test case
3. **Package `__init__.py`** with module overview and deprecated module flags

```python
# Module docstring template (condensed)
"""Module name - one-line description.

Goal
----
What problem this module solves.

How to Use
----------
    from src.package.module import MainClass
    result = MainClass().process(data)

Function Tree
-------------
- MainClass
  - process(data) -> Result

Configuration Parameters
------------------------
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| PARAM_ONE | str | "value" | Description |
"""

# Required __main__ block
if __name__ == "__main__":
    """Test with hardcoded input."""
    print("=== Module Test ===")
    # Self-contained test case
    test_input = {"key": "value"}
    result = process(test_input)
    assert result is not None
    print("[PASS] Test completed!")
```

### Path Handling (Windows)

```python
from pathlib import Path
from src.core.config import get_settings

settings = get_settings()

# ✅ GOOD - Cross-platform
db_path = Path(settings.DATABASE_PATH)
output_dir = Path("data") / "sessions"

# ❌ BAD - Windows-specific hardcoding
db_path = "data\\stamps.db"
```

### Error Handling Pattern

```python
from src.core.errors import ScrapingError

try:
    result = scrape_page(url)
except Exception as e:
    context = {'url': url, 'error_type': type(e).__name__}
    logger.error(f"Scraping failed: {e} | Context: {context}")
    raise ScrapingError(f"Failed to scrape {url}") from e
```

### Configuration Rules

**ALL configuration parameters MUST come from `src/core/config.py` exclusively.**

- No hardcoded defaults in dataclasses or module code
- All config field names use UPPERCASE (e.g., `DETECTION_NMS_ENABLED`)
- Factory functions like `create_*_from_env()` load values from `get_settings()`
- Dataclass fields should be required (no default values) - defaults live in config.py
- Classes should access settings directly via `get_settings()` - do NOT pass configuration as constructor parameters

```python
# ✅ GOOD - Class accesses settings directly
class InspectionViewer:
    def __init__(self):
        settings = get_settings()
        self.inspection_dir = settings.inspection_path

# ❌ BAD - Passing config as parameter creates indirection
class InspectionViewer:
    def __init__(self, inspection_dir: Path):  # Don't do this
        self.inspection_dir = inspection_dir

# ✅ GOOD - Config dataclass with required fields
@dataclass
class DetectionConfig:
    primary_provider: DetectionProvider  # Required, no default
    enable_fallback: bool                # Required, no default

def create_detector_from_env() -> Detector:
    settings = get_settings()
    config = DetectionConfig(
        primary_provider=DetectionProvider(settings.DETECTION_PRIMARY_PROVIDER),
        enable_fallback=settings.DETECTION_ENABLE_FALLBACK,
    )
    return Detector(config)

# ❌ BAD - Hardcoded defaults
@dataclass
class DetectionConfig:
    primary_provider: str = "groq"  # Don't do this
    enable_fallback: bool = True    # Don't do this
```

### Output Directory Rules

**ALL execution output MUST go to `OUTPUT_ROOT_DIR`, not the project directory.**

- `OUTPUT_ROOT_DIR` is set in `.env.local` (e.g., `D:/Stamps`)
- Database, logs, inspection, sessions, feedback all go under this root
- Use computed properties from settings for full paths:
  - `settings.database_path` → `OUTPUT_ROOT_DIR/stamps.db`
  - `settings.log_path` → `OUTPUT_ROOT_DIR/logs/`
  - `settings.inspection_path` → `OUTPUT_ROOT_DIR/inspection/`
  - `settings.feedback_output_path` → `OUTPUT_ROOT_DIR/feedback/`

```python
# ✅ GOOD - Use settings paths
from src.core.config import get_settings

settings = get_settings()
output_dir = settings.inspection_path  # Full path from OUTPUT_ROOT_DIR

# ❌ BAD - Relative to project
output_dir = Path("data/inspection")  # Don't do this
```

## Detection Architecture (Vision LLM)

The stamp detection uses Vision LLM with hybrid provider support, replacing the earlier OpenCV approach for better reliability with variable input.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      INPUT IMAGE                            │
│                           │                                 │
│            ┌──────────────┴──────────────┐                 │
│            ▼                              ▼                 │
│     ┌─────────────┐              ┌─────────────┐          │
│     │   SINGLE    │              │    MULTI    │          │
│     │   STAMP     │              │   (ALBUM)   │          │
│     └──────┬──────┘              └──────┬──────┘          │
│            │                            │                  │
│            │                 ┌──────────┴──────────┐      │
│            │                 ▼                     │      │
│            │        ┌─────────────────┐           │      │
│            │        │  PREPROCESSING  │           │      │
│            │        │  (7 strategies) │           │      │
│            │        └────────┬────────┘           │      │
│            │                 │                     │      │
│            │                 ▼                     │      │
│            │        ┌─────────────────┐           │      │
│            │        │  GROQ DETECTION │◄── Primary       │
│            │        └────────┬────────┘   (cheap)  │      │
│            │                 │                     │      │
│            │           Fail? ├── No ───────┐      │      │
│            │                 │             │      │      │
│            │                Yes            │      │      │
│            │                 ▼             │      │      │
│            │        ┌─────────────────┐   │      │      │
│            │        │  CLAUDE HAIKU   │   │      │      │
│            │        │  FALLBACK       │   │      │      │
│            │        └────────┬────────┘   │      │      │
│            │                 │             │      │      │
│            │                 └──────┬──────┘      │      │
│            │                        │             │      │
│            │                        ▼             │      │
│            │               ┌─────────────────┐   │      │
│            └──────────────►│  CROP STAMPS    │◄──┘      │
│                            │  (full-res)     │          │
│                            └────────┬────────┘          │
│                                     │                    │
│                                     ▼                    │
│                            ┌─────────────────┐          │
│                            │  GROQ VISION    │          │
│                            │  DESCRIPTION    │          │
│                            └────────┬────────┘          │
│                                     │                    │
│                                     ▼                    │
│                            ┌─────────────────┐          │
│                            │  RAG SEARCH     │          │
│                            └────────┬────────┘          │
│                                     │                    │
│                                     ▼                    │
│                            ┌─────────────────┐          │
│                            │  INSPECTION &   │          │
│                            │  RESULTS        │          │
│                            └─────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### Operation Modes

| Mode | Description | Detection | Use Case |
|------|-------------|-----------|----------|
| `auto` | Auto-detect based on image | If needed | Default |
| `single` | Skip detection, treat as one stamp | Skipped | Single stamp photos |
| `multi` | Always run detection | Always | Album pages |

### Detection Providers

| Provider | Role | Cost | Quality |
|----------|------|------|---------|
| Groq (llama-3.2-11b-vision) | Primary | ~$0.0003/image | Good |
| Claude Haiku | Fallback | ~$0.0004/image | Excellent |
| Claude Sonnet | Optional | ~$0.0045/image | Best |

Fallback triggered when:
- Groq API error
- JSON parse error
- Fewer than `DETECTION_MIN_DETECTIONS` stamps found

### Preprocessing Strategies

| Strategy | Description | Token Reduction |
|----------|-------------|-----------------|
| `original` | No change | 0% |
| `downscale` | Reduce resolution only | ~75% |
| `compress` | Downscale + JPEG compression | ~80% **(default)** |
| `posterize` | Color quantization | ~85% |
| `high_contrast` | CLAHE enhancement | ~80% |
| `edge_enhanced` | Edges on posterized | ~85% |
| `minimal` | Most aggressive | ~95% |

### Inspection System

Every identification session saves full inspection data:

```
data/inspection/<session_id>/
├── original.jpg              # Original input
├── session.json              # Complete session data
├── inspection_report.json    # Summary
│
├── preprocessed/
│   └── preprocessed.jpg      # Image sent to detection API
│
├── annotated/
│   ├── detection.jpg         # Detection boxes
│   └── final_result.jpg      # Final results with status colors
│
└── crops/
    ├── <id>_001.jpg          # Individual stamp crops (full-res)
    ├── <id>_002.jpg
    └── ...
```

## Feedback System

Every scan session produces visual feedback for review and re-ingestion:

### Color Coding

| Status | Color | Meaning |
|--------|-------|---------|
| 🟩 Identified | Green | Successfully matched in RAG (≥90%) |
| 🟨 Needs Review | Yellow | Matched but below auto-accept (<90%) |
| 🟧 No Match | Orange | Stamp detected but not in database |
| 🟥 Rejected | Red | Not identified as stamp |

### Session Output

```
data/sessions/<session_id>/
├── original.png              # Raw capture
├── annotated.png             # With colored overlays
├── session.json              # Full details
└── crops/
    ├── 001_identified_AU5352.png
    ├── 002_no_match_unmatched.png
    └── ...

data/missed_stamps/           # For later re-ingestion
└── <session_id>_002.png
```

## Data Model

### Local SQLite Entities

**CatalogStamp** — Scraped from Colnect
- `colnect_id` (PK), `colnect_url`, `title`, `country`, `year`
- `themes` (JSON), `image_url`, `catalog_codes` (JSON), `scraped_at`

**LastdodoItem** — Scraped from LASTDODO
- `lastdodo_id` (PK), `title`, `country`, `year`
- `michel_number`, `yvert_number`, `scott_number`, `sg_number`, `fisher_number`
- `condition`, `condition_mapped`, `quantity`, `value_eur`, `image_url`, `scraped_at`

**ImportTask** — Migration tracking
- `id` (PK), `lastdodo_id`, `colnect_id`, `status`
- `match_method`, `condition_final`, `quantity_final`, `comment`
- `error_message`, `reviewed_at`, `imported_at`, `dry_run`

### Supabase RAG Entity

**RAGEntry** — Vector search index
- `id` (PK), `colnect_id` (unique), `colnect_url`, `image_url`
- `description` (Groq-generated), `embedding` (vector 1536)
- `country`, `year`, `created_at`, `updated_at`

## Key Workflows

### 1. Initialization Pipeline

```
stamp-tools init
    │
    ├── Create SQLite database (data/stamps.db)
    ├── Create inspection/session directories
    ├── Verify Supabase connection
    ├── Verify Groq API key
    ├── Verify Anthropic API key (for fallback)
    └── Create RAG table in Supabase
```

### 2. Scrape → Index Pipeline

```
stamp-tools scrape colnect
    │
    ├── Discover stamp URLs by theme
    ├── For each stamp page:
    │   ├── Extract: id, title, country, year, image_url, catalog_codes
    │   └── Save to SQLite (CatalogStamp)
    └── Checkpoint progress for resume

stamp-tools rag index
    │
    ├── Load CatalogStamp entries
    ├── For each stamp:
    │   ├── Call Groq API with image_url → description
    │   ├── Call OpenAI API → embedding (1536 dim)
    │   └── Upsert to Supabase RAGEntry
    └── Report statistics
```

### 3. Identification Pipeline

```
stamp-tools identify camera
    │
    ├── Capture frame from camera (OpenCV)
    │
    ├── Determine mode (auto/single/multi)
    │
    ├── If MULTI mode:
    │   ├── Preprocess image (downscale, compress)
    │   ├── Call Groq detection API
    │   │   └── If fails: Call Claude Haiku fallback
    │   ├── Parse JSON response → bounding boxes
    │   └── Extract crops from ORIGINAL (full-res)
    │
    ├── If SINGLE mode:
    │   └── Use entire image as crop
    │
    ├── For each stamp crop:
    │   ├── Call Groq vision → description
    │   ├── Generate embedding → search Supabase
    │   ├── If score ≥ 90%: auto-accept
    │   └── Else: show top 3 for selection
    │
    ├── Save inspection data (all intermediates)
    │
    └── For confirmed matches:
        └── Browser automation → add to Colnect
```

### 4. Migration Pipeline

```
stamp-tools scrape lastdodo → scrape collection
stamp-tools migrate match   → match by catalog numbers
stamp-tools migrate import --dry-run → simulate
stamp-tools migrate review  → handle unmatched
stamp-tools migrate import  → live import
stamp-tools migrate status  → verify completion
```

## Browser Automation (CDP)

The toolset connects to an existing Chrome session via Chrome DevTools Protocol.

### Start Chrome with CDP

```powershell
# Windows - Start Chrome with remote debugging
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

**Important:** Log into Colnect and LASTDODO manually before running automation commands.

## External Services

| Service | Purpose | Auth | Free Tier |
|---------|---------|------|-----------|
| **Colnect** | Stamp catalog, collection | Browser session | Premium membership |
| **LASTDODO** | Source collection | Browser session | Free account |
| **Supabase** | Vector database | API key | 500MB |
| **OpenAI** | Embeddings | API key | Pay-per-use (~€0.50 total) |
| **Groq** | Vision detection & description | API key | 30 req/min free |
| **Anthropic** | Detection fallback (Claude Haiku) | API key | Pay-per-use |

## Cost Estimate

### Per 100 Album Pages (~8 stamps each)

| Component | Cost |
|-----------|------|
| Detection (Groq + Haiku fallback) | ~$0.04 |
| Description (Groq) | ~$0.24 |
| RAG search (Supabase) | Free tier |
| **Total** | **~$0.28** |

### One-time Setup (50K stamps)

| Component | Cost |
|-----------|------|
| Groq descriptions | ~€5-15 |
| OpenAI embeddings | ~€0.50 |
| **Total** | **~€6-16** |

### Ongoing

- Monthly: <€0.05 (occasional identification)
- Supabase: Free tier (<500MB)

## Default Themes

```
Space, Space Traveling, Astronomy, Rockets, Satellites, Scientists
```

Configurable via `--themes` parameter.

## Important Context

- **Hardware:** AMD Ryzen 9 6900HX (no ROCm support for integrated GPU)
- **Vision:** Cloud-only via Groq/Claude APIs (no local models)
- **Primary platform:** Colnect (source of truth for collection)
- **LASTDODO:** One-time migration only, no sync back
- **Cost target:** < €1/month ongoing, ~€6-16 one-time setup
- **Catalog size:** ~50,000 space-themed stamps expected

## Identification Thresholds

- **Auto-accept:** ≥ 90% similarity score
- **Show top 3:** < 90% but ≥ 50%
- **No match:** < 50%

## Development Workflow

1. Use `/project:core_piv_loop:prime` to load project context
2. Use `/project:core_piv_loop:plan-feature` to plan new features
3. Use `/project:core_piv_loop:execute` to implement plans
4. Use `/project:validation:validate` to verify changes
5. Use `/project:commit` to commit changes

## Environment Instructions

This is a **Windows environment**. However, the Bash tool has limited reliability.

### CRITICAL: Use Specialized Tools, NOT Bash

**NEVER use Bash for file operations.** Always use the dedicated Claude Code tools:

| Task | ✅ USE THIS TOOL | ❌ NEVER USE BASH |
|------|------------------|-------------------|
| Read file contents | **Read** tool | `cat`, `type`, `Get-Content` |
| Search in files | **Grep** tool | `grep`, `findstr`, `Select-String` |
| Find files by pattern | **Glob** tool | `find`, `dir`, `Get-ChildItem` |
| Edit files | **Edit** tool | `sed`, `awk`, text manipulation |
| Create files | **Write** tool | `echo >`, `cat <<EOF` |

### When to Use Bash

Bash is ONLY for commands that have no tool equivalent:
- `git` commands (commit, push, status, etc.)
- `uv run` / `uv sync` for Python
- `pytest` for running tests
- Build/compile commands

### Path Format
- Always use Windows paths: `C:\Users\alain\...`
- Do NOT use Unix paths like `/c/Users/...`
- Quote paths with spaces: `"C:\Program Files\..."`

### Examples

```python
# ✅ CORRECT - Read file content
# Use the Read tool with file_path="C:\Users\alain\CascadeProjects\Stamps\.env.app"

# ✅ CORRECT - Search for pattern in files
# Use the Grep tool with pattern="DETECTION" and path="C:\Users\alain\CascadeProjects\Stamps"

# ✅ CORRECT - Find Python files
# Use the Glob tool with pattern="**/*.py"

# ✅ CORRECT - Run Python via Bash (no tool equivalent)
uv run python -c "print('hello')"

# ✅ CORRECT - Git operations via Bash
git status
git add .
git commit -m "message"
```

## External Resources

- [PRD.md](./PRD.md) - Full product requirements document
- [Colnect Stamps](https://colnect.com/en/stamps/) - Primary catalog
- [LASTDODO](https://www.lastdodo.nl/) - Source collection
- [Supabase Vector](https://supabase.com/docs/guides/ai/vector-columns) - pgvector docs
- [Groq Vision](https://console.groq.com/docs/vision) - Vision API
- [Anthropic Claude](https://docs.anthropic.com/) - Claude API
- [Playwright Python](https://playwright.dev/python/) - Browser automation
