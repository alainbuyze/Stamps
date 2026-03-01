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
- **Object Detection:** OpenCV (primary) + YOLOv8 (fallback)
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
│   ├── describer.py              # Groq vision API descriptions
│   └── detection/                # Two-stage detection pipeline
│       ├── __init__.py
│       ├── polygon_detector.py   # Stage 1A: Classical CV
│       ├── stamp_classifier.py   # Stage 1B: Heuristic filter
│       ├── yolo_detector.py      # Stage 1C: YOLO fallback
│       └── pipeline.py           # Orchestration
│
├── feedback/                     # Scan feedback & visualization
│   ├── __init__.py
│   ├── models.py                 # DetectionFeedback, ScanSession
│   ├── visualizer.py             # Annotated image generator
│   ├── session_manager.py        # Session persistence
│   └── console.py                # Rich console output
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
data/                             # SQLite DB + logs + sessions (gitignored)
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

# Vision - Groq
GROQ_MODEL=llama-3.2-11b-vision-preview

# Detection (Two-Stage)
DETECTION_MODE=album
DETECTION_MIN_VERTICES=3
DETECTION_MAX_VERTICES=4
CLASSIFIER_CONFIDENCE_THRESHOLD=0.6
DETECTION_FALLBACK_TO_YOLO=true

# Feedback
FEEDBACK_SAVE_ANNOTATED=true
FEEDBACK_SAVE_CROPS=true

# Browser Automation
CHROME_CDP_URL=http://localhost:9222
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

## Detection Architecture (Two-Stage)

The stamp detection uses a two-stage pipeline optimized for album pages:

### Stage 1A: Classical CV Polygon Detection

Uses OpenCV for efficient, training-free detection:

```python
# Conceptual flow
1. Preprocess: grayscale → blur → adaptive threshold
2. Find contours (cv2.findContours)
3. Approximate polygons (cv2.approxPolyDP)
4. Filter by:
   - Vertices: 3 (triangle) or 4 (quadrilateral)
   - Area: reasonable stamp size
   - Convexity: must be convex shape
   - Aspect ratio: 0.3 to 3.0
5. Perspective correction → clean rectangular crops
```

**Supported shapes:**
- Triangles (3 vertices)
- Rectangles, squares, diamonds (4 vertices)
- Miniature sheets detected as single items

### Stage 1B: Stamp Classifier (Heuristics)

Filters false positives with weighted checks:

| Check | Weight | Description |
|-------|--------|-------------|
| Color variance | 0.35 | Stamps are colorful, not blank |
| Edge complexity | 0.30 | Stamps have detailed content |
| Size plausibility | 0.20 | Reasonable dimensions |
| Perforation hint | 0.15 | Optional wavy edge pattern |

Confidence threshold: **0.6** to accept as stamp.

### Stage 1C: YOLO Fallback

Triggered only when Stage 1A finds no candidates:
- Pre-trained or fine-tuned YOLOv8
- Only loaded when needed (lazy loading)
- Configurable via `DETECTION_FALLBACK_TO_YOLO`

### Stage 2: RAG Identification

Clean crops from Stage 1 feed into:
1. Groq vision → description
2. OpenAI → embedding  
3. Supabase → similarity search

## Feedback System

Every scan session produces visual feedback for review and re-ingestion:

### Color Coding

| Status | Color | Meaning |
|--------|-------|---------|
| 🟩 Identified | Green | Successfully matched in RAG |
| 🟧 No Match | Orange | Stamp detected but not in database |
| 🟥 Rejected | Red | Failed classifier (not a stamp) |
| 🟪 YOLO | Purple | Detected by YOLO fallback |

### Session Output Structure

```
data/
├── sessions/
│   └── 20260222_143052_abc123/
│       ├── original.png          # Raw camera capture
│       ├── annotated.png         # With colored overlays
│       ├── session.json          # Full detection details
│       └── crops/
│           ├── 001_identified_AU5352.png
│           ├── 002_no_match_unmatched.png
│           └── 003_rejected_low_variance.png
│
└── missed_stamps/                # For later re-ingestion
    └── 20260222_143052_abc123_002.png
```

### Console Output

After each scan, Rich displays:
- Summary table with counts by status
- Detailed table of identified stamps with confidence
- Warning panel for stamps needing review
- Path to annotated image

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
    ├── Create session directories
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
    │
    ├── Stage 1A: Polygon detection (OpenCV)
    │   └── Find triangles + quadrilaterals
    │
    ├── Stage 1B: Classify each polygon
    │   └── Accept stamps, reject non-stamps
    │
    ├── Stage 1C: YOLO fallback (if nothing found)
    │
    ├── For each accepted stamp:
    │   ├── Call Groq API → description
    │   ├── Generate embedding → search Supabase
    │   ├── If score > 90%: auto-accept
    │   └── Else: show top 3 for selection
    │
    ├── Save session (annotated image + crops + JSON)
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
