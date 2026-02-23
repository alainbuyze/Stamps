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
- **Vision/Description:** Groq API (llama-3.2-11b-vision, configurable)
- **Object Detection:** YOLOv8 (Ultralytics)
- **Web Scraping:** Playwright + BeautifulSoup4
- **Browser Automation:** Playwright CDP (Chrome DevTools Protocol)
- **Image Processing:** Pillow, OpenCV
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
├── vision/                       # Computer vision module
│   ├── __init__.py
│   ├── camera.py                 # OpenCV camera capture
│   ├── detector.py               # YOLOv8 stamp detection
│   └── describer.py              # Groq vision API descriptions
│
├── identification/               # Stamp identification module
│   ├── __init__.py
│   ├── identifier.py             # Pipeline orchestration
│   └── results.py                # Result display & user selection
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

models/                           # YOLO weights (gitignored, auto-downloaded)
data/                             # SQLite DB + logs (gitignored)
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
# Identify stamps from camera
uv run stamp-tools identify camera

# Identify from image file
uv run stamp-tools identify image --path "C:\path\to\photo.jpg"

# Auto-add confirmed matches to Colnect
uv run stamp-tools identify camera --add-to-colnect
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
SCRAPE_RETRY_COUNT=3
SCRAPE_ERROR_BEHAVIOR=skip

# RAG
RAG_MATCH_AUTO_THRESHOLD=0.9
RAG_MATCH_MIN_THRESHOLD=0.5
EMBEDDING_MODEL=text-embedding-3-small

# Vision - Groq
GROQ_MODEL=llama-3.2-11b-vision-preview
GROQ_RATE_LIMIT_PER_MINUTE=30

# Object Detection
YOLO_MODEL_PATH=models/yolov8n.pt
YOLO_CONFIDENCE_THRESHOLD=0.5

# Browser Automation
CHROME_CDP_URL=http://localhost:9222

# Logging
LOG_LEVEL=INFO
```

### Secrets (.env.keys)

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-service-role-key
OPENAI_API_KEY=sk-xxxxx
GROQ_API_KEY=gsk_xxxxx
```



## Code Conventions

- **Type hints** on all function signatures
- **Pydantic** for configuration and data validation
- **Rich** for all console output (progress bars, tables, colors)
- **Pathlib** for all file operations (cross-platform)
- **Docstrings** on all public functions and classes
- Functions focused and testable
- Logging at appropriate levels (DEBUG for flow, INFO for status, ERROR for failures)

### Path Handling (Windows)

```python
from pathlib import Path
from src.core.config import get_settings

settings = get_settings()

# ✅ GOOD - Cross-platform
db_path = Path(settings.DATABASE_PATH)
model_path = Path(settings.YOLO_MODEL_PATH)
output_dir = Path("data") / "output"

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

### Logging Pattern

```python
import logging
logger = logging.getLogger(__name__)

# Function entry
logger.debug(f" * scrape_stamp_page > Starting for {url}")

# Operational flow
logger.debug("    -> Extracting title and country")

# Status updates
logger.info(f"Scraped {count} stamps from {theme}")

# Errors with context
logger.error(f"Failed: {error} | URL: {url}")
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

### Condition Mapping

| LASTDODO (Dutch) | Colnect (English) |
|------------------|-------------------|
| Postfris | MNH |
| Ongebruikt | MNH |
| Gestempeld | Used |

When multiple conditions: MNH takes precedence, comment contains breakdown (e.g., `MNH:3, U:1`).

## Key Workflows

### 1. Initialization Pipeline

```
stamp-tools init
    │
    ├── Create SQLite database (data/stamps.db)
    ├── Download YOLOv8 model (models/yolov8n.pt)
    ├── Verify Supabase connection
    ├── Verify Groq API key
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
    ├── Detect stamps with YOLOv8 → bounding boxes
    ├── For each detection:
    │   ├── Crop stamp region
    │   ├── Call Groq API → description
    │   ├── Generate embedding → search Supabase
    │   ├── If score > 90%: auto-accept
    │   └── Else: show top 3 for selection
    ├── For confirmed matches:
    │   └── Browser automation → add to Colnect
    └── Display summary
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

### Usage in Code

```python
from playwright.sync_api import sync_playwright

# Connect to existing Chrome
browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
page = browser.contexts[0].pages[0]

# User must be logged into Colnect/LASTDODO
```

**Important:** Log into Colnect and LASTDODO manually before running automation commands.

## External Services

| Service | Purpose | Auth | Free Tier |
|---------|---------|------|-----------|
| **Colnect** | Stamp catalog, collection | Browser session | Premium membership |
| **LASTDODO** | Source collection | Browser session | Free account |
| **Supabase** | Vector database | API key | 500MB |
| **OpenAI** | Embeddings | API key | Pay-per-use (~€0.50 total) |
| **Groq** | Vision descriptions | API key | 30 req/min free |

## Default Themes

```
Space, Space Traveling, Astronomy, Rockets, Satellites, Scientists
```

Configurable via `--themes` parameter.

## Important Context

- **Hardware:** AMD Ryzen 9 6900HX (no ROCm support for integrated GPU)
- **Vision:** Cloud-only via Groq API (no local LLaVA)
- **Primary platform:** Colnect (source of truth for collection)
- **LASTDODO:** One-time migration only, no sync back
- **Cost target:** < €1/month ongoing, ~€6-16 one-time setup
- **Catalog size:** ~50,000 space-themed stamps expected

## Identification Thresholds

- **Auto-accept:** > 90% similarity score
- **Show top 3:** ≤ 90% but ≥ 50%
- **No match:** < 50%

## Development Workflow

1. Use `/project:core_piv_loop:prime` to load project context
2. Use `/project:core_piv_loop:plan-feature` to plan new features
3. Use `/project:core_piv_loop:execute` to implement plans
4. Use `/project:validation:validate` to verify changes
5. Use `/project:commit` to commit changes

## Environment Instructions

This is a Windows environment using PowerShell/CMD, NOT bash.

### Shell Commands
- Use PowerShell commands, not bash/Unix commands
- Use `Get-Content` instead of `cat`
- Use Windows paths: `C:\Users\alain\...`
- Do NOT use Unix paths like `/c/Users/...`

### File Operations
- Reading files: `Get-Content "C:\path\to\file"`
- Listing directories: `Get-ChildItem` or `dir`
- Current directory: `Get-Location` or `pwd`

## External Resources

- [PRD.md](./PRD.md) - Full product requirements document
- [Colnect Stamps](https://colnect.com/en/stamps/) - Primary catalog
- [LASTDODO](https://www.lastdodo.nl/) - Source collection
- [Ultralytics YOLOv8](https://docs.ultralytics.com/) - Object detection
- [Supabase Vector](https://supabase.com/docs/guides/ai/vector-columns) - pgvector docs
- [Groq Vision](https://console.groq.com/docs/vision) - Vision API
- [Playwright Python](https://playwright.dev/python/) - Browser automation
