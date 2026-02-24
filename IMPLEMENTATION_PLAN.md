# Stamp Collection Toolset — Implementation Plan

**Created:** 2026-02-23
**Status:** Ready for Implementation
**Estimated Total Effort:** 38-52 hours (7 phases)

---

## Current State Assessment

| Component | Status | Notes |
|-----------|--------|-------|
| Documentation | ✅ Complete | CLAUDE.md, PRD.md fully written |
| Core/Logging | ✅ Complete | Production-ready with Rich integration |
| Core/Config | ❌ Wrong | Contains settings from different project - needs rewrite |
| Core/Errors | ⚠️ Partial | Has base exceptions, missing domain-specific ones |
| Core/Database | ❌ Missing | SQLite operations not implemented |
| CLI | ❌ Missing | Entry point not created |
| Scraping | ❌ Missing | Browser, Colnect, LASTDODO modules |
| RAG | ❌ Missing | Embeddings, Supabase, indexer, search |
| Vision | ❌ Missing | Camera, YOLO detector, Groq describer |
| Identification | ❌ Missing | Pipeline orchestration |
| Migration | ❌ Missing | LASTDODO → Colnect workflow |
| Colnect API | ❌ Missing | CDP browser automation |
| Tests | ❌ Missing | No test suite |

---

## Phase 1: Core Infrastructure (4-6 hours)

**Goal:** Establish working foundation with CLI, database, and configuration.

### 1.1 Fix Configuration (`src/core/config.py`)

Replace incorrect settings with stamp-specific configuration:

```python
class Settings(BaseSettings):
    # Database
    DATABASE_PATH: str = "data/stamps.db"

    # Scraping
    SCRAPE_DELAY_SECONDS: float = 1.5
    SCRAPE_RETRY_COUNT: int = 3
    SCRAPE_ERROR_BEHAVIOR: str = "skip"  # skip | abort

    # RAG
    RAG_MATCH_AUTO_THRESHOLD: float = 0.9
    RAG_MATCH_MIN_THRESHOLD: float = 0.5
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Vision - Groq
    GROQ_MODEL: str = "llama-3.2-11b-vision-preview"
    GROQ_RATE_LIMIT_PER_MINUTE: int = 30

    # Object Detection
    YOLO_MODEL_PATH: str = "models/yolov8n.pt"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.5

    # Browser Automation
    CHROME_CDP_URL: str = "http://localhost:9222"

    # API Keys (from .env.keys)
    SUPABASE_URL: str
    SUPABASE_KEY: str
    OPENAI_API_KEY: str
    GROQ_API_KEY: str

    # Logging (already configured)
    LOG_LEVEL: str = "INFO"
```

### 1.2 Add Domain Exceptions (`src/core/errors.py`)

Add missing exceptions:

```python
# Database
class DatabaseError(StampToolsError): ...
class RecordNotFoundError(DatabaseError): ...
class DuplicateRecordError(DatabaseError): ...

# RAG
class RAGError(StampToolsError): ...
class EmbeddingError(RAGError): ...
class SearchError(RAGError): ...

# Identification
class IdentificationError(StampToolsError): ...
class CameraError(IdentificationError): ...
class DetectionError(IdentificationError): ...

# Migration
class MigrationError(StampToolsError): ...
class MatchingError(MigrationError): ...
class ImportError(MigrationError): ...

# Browser Automation
class BrowserAutomationError(StampToolsError): ...
class CDPConnectionError(BrowserAutomationError): ...
class ColnectActionError(BrowserAutomationError): ...
```

### 1.3 Implement Database Module (`src/core/database.py`)

SQLite operations with these tables:

```sql
-- CatalogStamp: Scraped from Colnect
CREATE TABLE catalog_stamps (
    colnect_id TEXT PRIMARY KEY,
    colnect_url TEXT NOT NULL,
    title TEXT NOT NULL,
    country TEXT NOT NULL,
    year INTEGER NOT NULL,
    themes TEXT,  -- JSON array
    image_url TEXT NOT NULL,
    catalog_codes TEXT,  -- JSON {michel, scott, yvert, sg, fisher}
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LastdodoItem: Scraped from LASTDODO
CREATE TABLE lastdodo_items (
    lastdodo_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    country TEXT,
    year INTEGER,
    michel_number TEXT,
    yvert_number TEXT,
    scott_number TEXT,
    sg_number TEXT,
    fisher_number TEXT,
    condition TEXT NOT NULL,
    condition_mapped TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    value_eur REAL,
    image_url TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ImportTask: Migration tracking
CREATE TABLE import_tasks (
    id TEXT PRIMARY KEY,
    lastdodo_id TEXT NOT NULL REFERENCES lastdodo_items(lastdodo_id),
    colnect_id TEXT REFERENCES catalog_stamps(colnect_id),
    status TEXT NOT NULL DEFAULT 'pending',
    match_method TEXT,
    condition_final TEXT,
    quantity_final INTEGER,
    comment TEXT,
    error_message TEXT,
    reviewed_at TIMESTAMP,
    imported_at TIMESTAMP,
    dry_run INTEGER DEFAULT 0,
    CHECK (status IN ('pending', 'matched', 'needs_review', 'imported', 'failed', 'skipped'))
);

-- Indexes
CREATE INDEX idx_catalog_country_year ON catalog_stamps(country, year);
CREATE INDEX idx_import_status ON import_tasks(status);
```

**Functions to implement:**
- `get_connection()` - Get SQLite connection
- `init_database()` - Create tables if not exist
- `upsert_catalog_stamp(stamp: CatalogStamp)` - Insert/update stamp
- `get_catalog_stamps(country=None, year=None)` - Query with filters
- `upsert_lastdodo_item(item: LastdodoItem)` - Insert/update item
- `get_lastdodo_items()` - Get all items
- `create_import_task(task: ImportTask)` - Create task
- `update_import_task(task_id, **fields)` - Update task
- `get_import_tasks(status=None)` - Query by status

### 1.4 Create CLI Entry Point (`src/cli.py`)

Click-based CLI with subcommand groups:

```python
@click.group()
@click.version_option()
def cli():
    """Stamp Collection Toolset - AI-powered stamp management."""
    pass

@cli.command()
def init():
    """Initialize database and verify connections."""
    # Create data/ directory
    # Initialize SQLite database
    # Download YOLOv8 model
    # Verify Supabase connection
    # Verify Groq API key
    # Create RAG table in Supabase

@cli.group()
def scrape():
    """Web scraping commands."""
    pass

@cli.group()
def rag():
    """RAG database commands."""
    pass

@cli.command()
def identify():
    """Stamp identification commands."""
    pass

@cli.group()
def migrate():
    """LASTDODO migration commands."""
    pass

@cli.group()
def config():
    """Configuration commands."""
    pass
```

### 1.5 Create .env.app with Correct Defaults

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
LOG_FORMAT=%(asctime)s | %(name)s | %(levelname)s | %(message)s
LOG_MAX_SIZE_MB=10
LOG_BACKUP_COUNT=3
```

### Phase 1 Deliverables

- [ ] `src/core/config.py` - Stamp-specific settings
- [ ] `src/core/errors.py` - All domain exceptions
- [ ] `src/core/database.py` - SQLite operations
- [ ] `src/cli.py` - Click CLI skeleton
- [ ] `.env.app` - Fixed application defaults
- [ ] `stamp-tools init` command working

---

## Phase 2: Colnect Scraping (6-8 hours)

**Goal:** Scrape space-themed stamps from Colnect catalog.

### 2.1 Browser Manager (`src/scraping/browser.py`)

Playwright wrapper for web scraping:

```python
class BrowserManager:
    """Manages Playwright browser for scraping."""

    async def __aenter__(self) -> "BrowserManager": ...
    async def __aexit__(self, *args): ...

    async def new_page(self) -> Page: ...
    async def goto(self, url: str, wait_until="networkidle"): ...
    async def wait_for_selector(self, selector: str): ...
    async def get_page_content(self) -> str: ...
```

### 2.2 Colnect Scraper (`src/scraping/colnect.py`)

**Site structure analysis needed:**
- Theme listing page: `https://colnect.com/en/stamps/themes/`
- Country listing: `https://colnect.com/en/stamps/countries/`
- Stamp page: `https://colnect.com/en/stamps/stamp/{id}-{slug}`

**Functions:**
```python
class ColnectScraper:
    """Scrapes stamp data from Colnect catalog."""

    async def get_theme_stamps(self, theme: str) -> list[str]:
        """Get all stamp URLs for a theme."""

    async def scrape_stamp_page(self, url: str) -> CatalogStamp:
        """Extract stamp data from page."""
        # colnect_id, title, country, year, themes, image_url, catalog_codes

    async def scrape_all_themes(
        self,
        themes: list[str],
        checkpoint_file: Path = None
    ) -> int:
        """Scrape all stamps for given themes with checkpoint support."""
```

**Data extraction:**
- Title: Page heading
- Country: Breadcrumb or metadata
- Year: Metadata field
- Image URL: Main stamp image `src`
- Catalog codes: Michel, Scott, Yvert, SG, Fisher from metadata table
- Themes: From page metadata

### 2.3 CLI Commands

```python
@scrape.command("colnect")
@click.option("--themes", default="Space,Astronomy,Rockets,Satellites,Scientists")
@click.option("--country", help="Filter by country")
@click.option("--year", type=int, help="Filter by year")
@click.option("--resume", is_flag=True, help="Resume from checkpoint")
def scrape_colnect(themes, country, year, resume):
    """Scrape Colnect for space-themed stamps."""
```

### Phase 2 Deliverables

- [ ] `src/scraping/__init__.py`
- [ ] `src/scraping/browser.py` - Playwright manager
- [ ] `src/scraping/colnect.py` - Colnect scraper
- [ ] `stamp-tools scrape colnect` command
- [ ] Checkpoint/resume support
- [ ] Rate limiting (1.5s delay)

---

## Phase 3: RAG Pipeline (6-8 hours)

**Goal:** Build searchable vector database in Supabase.

### 3.1 Groq Vision Describer (`src/vision/describer.py`)

```python
class StampDescriber:
    """Generates descriptions via Groq vision API."""

    def __init__(self, api_key: str, model: str):
        self.client = groq.Groq(api_key=api_key)
        self.model = model
        self.prompt_template = load_prompt("config/llava_prompt.txt")

    async def describe(self, image_url: str) -> str:
        """Generate description for stamp image."""
        # Rate limit: 30 req/min

    async def describe_batch(
        self,
        stamps: list[CatalogStamp],
        progress_callback=None
    ) -> dict[str, str]:
        """Batch describe with rate limiting."""
```

### 3.2 OpenAI Embeddings (`src/rag/embeddings.py`)

```python
class EmbeddingGenerator:
    """Generates embeddings via OpenAI API."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    async def embed(self, text: str) -> list[float]:
        """Generate 1536-dim embedding for text."""

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embed for efficiency."""
```

### 3.3 Supabase Client (`src/rag/supabase_client.py`)

```python
class SupabaseRAG:
    """Manages RAG entries in Supabase with pgvector."""

    def __init__(self, url: str, key: str):
        self.client = supabase.create_client(url, key)

    async def init_table(self):
        """Create stamps_rag table with vector column."""

    async def upsert(self, entry: RAGEntry):
        """Insert or update RAG entry."""

    async def search(
        self,
        embedding: list[float],
        limit: int = 10,
        country: str = None,
        year: int = None
    ) -> list[tuple[RAGEntry, float]]:
        """Vector similarity search with optional filters."""

    async def get_stats(self) -> dict:
        """Return count, countries, year range."""
```

### 3.4 RAG Indexer (`src/rag/indexer.py`)

```python
class RAGIndexer:
    """Orchestrates the indexing pipeline."""

    def __init__(
        self,
        describer: StampDescriber,
        embedder: EmbeddingGenerator,
        supabase: SupabaseRAG
    ):
        ...

    async def index_stamp(self, stamp: CatalogStamp) -> RAGEntry:
        """Full pipeline: describe → embed → store."""

    async def index_all(
        self,
        stamps: list[CatalogStamp],
        regenerate: bool = False,
        progress_callback=None
    ) -> int:
        """Index all stamps with progress reporting."""
```

### 3.5 RAG Search (`src/rag/search.py`)

```python
class RAGSearcher:
    """Performs similarity search for stamp identification."""

    async def search(
        self,
        description: str,
        top_k: int = 3,
        min_threshold: float = 0.5
    ) -> list[SearchResult]:
        """Search by text description."""

    async def identify(
        self,
        image_description: str,
        auto_threshold: float = 0.9
    ) -> IdentificationResult:
        """Full identification with auto-accept logic."""
```

### 3.6 CLI Commands

```python
@rag.command("index")
@click.option("--country", help="Filter by country")
@click.option("--year", type=int, help="Filter by year")
@click.option("--regenerate", is_flag=True, help="Regenerate descriptions")
def rag_index(country, year, regenerate):
    """Index stamps into Supabase RAG."""

@rag.command("search")
@click.option("--query", required=True, help="Search query")
def rag_search(query):
    """Manual similarity search."""

@rag.command("stats")
def rag_stats():
    """Show RAG database statistics."""
```

### Phase 3 Deliverables

- [ ] `src/vision/__init__.py`
- [ ] `src/vision/describer.py` - Groq vision integration
- [ ] `src/rag/__init__.py`
- [ ] `src/rag/embeddings.py` - OpenAI embeddings
- [ ] `src/rag/supabase_client.py` - Supabase operations
- [ ] `src/rag/indexer.py` - Indexing pipeline
- [ ] `src/rag/search.py` - Similarity search
- [ ] `stamp-tools rag index|search|stats` commands

---

## Phase 4: Stamp Detection & Identification (6-8 hours)

**Goal:** Detect stamps in images and identify them via RAG.

### 4.1 Camera Capture (`src/vision/camera.py`)

```python
class CameraCapture:
    """OpenCV camera capture for stamp images."""

    def __init__(self, camera_index: int = 0):
        self.cap = cv2.VideoCapture(camera_index)

    def capture_frame(self) -> np.ndarray:
        """Capture single frame from camera."""

    def preview_with_detection(
        self,
        detector: "StampDetector",
        on_capture: callable = None
    ):
        """Live preview with bounding boxes, capture on keypress."""
```

### 4.2 YOLO Detector (`src/vision/detector.py`)

```python
class StampDetector:
    """YOLOv8 stamp detection."""

    def __init__(
        self,
        model_path: str = "models/yolov8n.pt",
        confidence: float = 0.5
    ):
        self.model = YOLO(model_path)
        self.confidence = confidence

    def detect(self, image: np.ndarray) -> list[Detection]:
        """Detect stamps, return bounding boxes."""

    def crop_detections(
        self,
        image: np.ndarray,
        detections: list[Detection]
    ) -> list[np.ndarray]:
        """Crop detected stamp regions."""
```

### 4.3 Identifier Pipeline (`src/identification/identifier.py`)

```python
class StampIdentifier:
    """Orchestrates the identification pipeline."""

    def __init__(
        self,
        detector: StampDetector,
        describer: StampDescriber,
        searcher: RAGSearcher
    ):
        ...

    async def identify_image(
        self,
        image: np.ndarray
    ) -> list[IdentificationResult]:
        """
        Full pipeline:
        1. Detect stamps with YOLO
        2. For each detection:
           a. Crop image
           b. Generate description with Groq
           c. Search RAG for matches
           d. Apply threshold logic
        """

    async def identify_from_camera(self) -> list[IdentificationResult]:
        """Capture from camera and identify."""

    async def identify_from_file(self, path: Path) -> list[IdentificationResult]:
        """Load image file and identify."""
```

### 4.4 Results Display (`src/identification/results.py`)

```python
class ResultsDisplay:
    """Rich console display for identification results."""

    def show_auto_match(self, result: IdentificationResult):
        """Display auto-accepted match (>90%)."""

    def show_candidates(
        self,
        result: IdentificationResult
    ) -> Optional[CatalogStamp]:
        """Display top 3, prompt for selection."""

    def show_no_match(self, result: IdentificationResult):
        """Display no match found message."""
```

### 4.5 CLI Commands

```python
@cli.group()
def identify():
    """Stamp identification commands."""

@identify.command("camera")
@click.option("--add-to-colnect", is_flag=True)
def identify_camera(add_to_colnect):
    """Identify stamps from camera."""

@identify.command("image")
@click.option("--path", required=True, type=click.Path(exists=True))
@click.option("--add-to-colnect", is_flag=True)
def identify_image(path, add_to_colnect):
    """Identify stamps from image file."""
```

### Phase 4 Deliverables

- [ ] `src/vision/camera.py` - OpenCV capture
- [ ] `src/vision/detector.py` - YOLO detection
- [ ] `src/identification/__init__.py`
- [ ] `src/identification/identifier.py` - Pipeline orchestration
- [ ] `src/identification/results.py` - Rich display
- [ ] `stamp-tools identify camera|image` commands

---

## Phase 5: Colnect Browser Automation (4-6 hours)

**Goal:** Add identified stamps to Colnect collection via CDP.

### 5.1 CDP Session Manager (`src/colnect_api/session.py`)

```python
class CDPSession:
    """Manages Chrome DevTools Protocol connection."""

    def __init__(self, cdp_url: str = "http://localhost:9222"):
        self.cdp_url = cdp_url

    async def connect(self) -> Browser:
        """Connect to existing Chrome via CDP."""

    async def verify_colnect_login(self) -> bool:
        """Check if user is logged into Colnect."""

    async def get_page(self) -> Page:
        """Get or create Colnect page."""
```

### 5.2 Colnect Actions (`src/colnect_api/actions.py`)

```python
class ColnectActions:
    """Browser automation for Colnect operations."""

    def __init__(self, session: CDPSession):
        self.session = session

    async def add_to_collection(
        self,
        colnect_url: str,
        condition: str = "MNH",
        quantity: int = 1,
        comment: str = None
    ) -> bool:
        """Add stamp to collection."""
        # Navigate to page
        # Click "Add to collection"
        # Fill condition, quantity, comment
        # Submit

    async def check_owned(self, colnect_url: str) -> bool:
        """Check if stamp already in collection."""
```

### Phase 5 Deliverables

- [ ] `src/colnect_api/__init__.py`
- [ ] `src/colnect_api/session.py` - CDP connection
- [ ] `src/colnect_api/actions.py` - Collection operations
- [ ] Integration with identification pipeline

---

## Phase 6: LASTDODO Migration (8-10 hours)

**Goal:** Migrate collection from LASTDODO to Colnect.

### 6.1 LASTDODO Scraper (`src/scraping/lastdodo.py`)

```python
class LastdodoScraper:
    """Scrapes user's LASTDODO collection."""

    async def scrape_collection(self) -> list[LastdodoItem]:
        """
        Scrape all items from logged-in collection.
        Requires Chrome with logged-in session.
        """
        # Navigate to collection
        # Paginate through all items
        # Extract: title, catalog numbers, condition, quantity, etc.
```

### 6.2 Catalog Matcher (`src/migration/matcher.py`)

```python
class CatalogMatcher:
    """Matches LASTDODO items to Colnect stamps."""

    PRIORITY = ["michel", "yvert", "scott", "sg", "fisher"]

    async def match(
        self,
        item: LastdodoItem
    ) -> Optional[tuple[CatalogStamp, str]]:
        """
        Match by catalog number priority.
        Returns (stamp, match_method) or None.
        """

    async def match_all(
        self,
        items: list[LastdodoItem],
        progress_callback=None
    ) -> MatchResult:
        """Match all items, report statistics."""
```

### 6.3 Condition Mapper (`src/migration/mapper.py`)

```python
class ConditionMapper:
    """Maps Dutch conditions to English."""

    MAPPING = {
        "Postfris": "MNH",
        "Ongebruikt": "MNH",
        "Gestempeld": "Used",
    }

    def map(self, condition: str) -> str:
        """Map single condition."""

    def consolidate(
        self,
        items: list[LastdodoItem]
    ) -> ConsolidatedItem:
        """
        Consolidate multiple items of same stamp.
        MNH takes precedence.
        Comment contains breakdown.
        """
```

### 6.4 Import Orchestrator (`src/migration/importer.py`)

```python
class CollectionImporter:
    """Orchestrates the import process."""

    async def import_all(
        self,
        dry_run: bool = True,
        progress_callback=None
    ) -> ImportReport:
        """
        Import matched items to Colnect.
        1. Get all matched ImportTasks
        2. For each task:
           a. Navigate to Colnect page
           b. Add with condition, quantity, comment
           c. Update task status
        3. Generate report
        """
```

### 6.5 Manual Review CLI (`src/migration/review.py`)

```python
class ReviewCLI:
    """Interactive CLI for manual review."""

    def review_unmatched(self):
        """
        Display unmatched items one by one.
        User can:
        - Enter Colnect URL → match
        - Skip → mark skipped
        - Quit → save progress
        """
```

### 6.6 CLI Commands

```python
@migrate.command("match")
def migrate_match():
    """Match LASTDODO items to Colnect catalog."""

@migrate.command("import")
@click.option("--dry-run", is_flag=True, default=True)
def migrate_import(dry_run):
    """Import matched items to Colnect."""

@migrate.command("review")
def migrate_review():
    """Manual review queue for unmatched items."""

@migrate.command("status")
def migrate_status():
    """Show migration status."""
```

### Phase 6 Deliverables

- [ ] `src/scraping/lastdodo.py` - Collection scraper
- [ ] `src/migration/__init__.py`
- [ ] `src/migration/matcher.py` - Catalog matching
- [ ] `src/migration/mapper.py` - Condition mapping
- [ ] `src/migration/importer.py` - Import orchestration
- [ ] `src/migration/review.py` - Manual review CLI
- [ ] `stamp-tools scrape lastdodo` command
- [ ] `stamp-tools migrate match|import|review|status` commands

---

## Phase 7: Polish & Testing (4-6 hours)

**Goal:** Quality assurance and documentation.

### 7.1 Test Suite

```
tests/
├── conftest.py              # Fixtures
├── test_core/
│   ├── test_config.py
│   ├── test_database.py
│   └── test_errors.py
├── test_scraping/
│   ├── test_colnect.py
│   └── test_lastdodo.py
├── test_rag/
│   ├── test_embeddings.py
│   ├── test_indexer.py
│   └── test_search.py
├── test_vision/
│   ├── test_detector.py
│   └── test_describer.py
├── test_identification/
│   └── test_identifier.py
└── test_migration/
    ├── test_matcher.py
    └── test_mapper.py
```

### 7.2 Configuration Commands

```python
@config.command("show")
def config_show():
    """Show current configuration."""

@config.command("validate")
def config_validate():
    """Validate all settings and connections."""
```

### 7.3 Documentation

- Update CLAUDE.md with any changes
- Add docstrings to all public functions
- Create `--help` text for all CLI commands

### Phase 7 Deliverables

- [ ] Complete test suite with pytest
- [ ] `stamp-tools config show|validate` commands
- [ ] All docstrings complete
- [ ] Help text for all commands
- [ ] Edge case handling

---

## Implementation Priority

```
Phase 1 (Core Infrastructure)
    ↓
Phase 2 (Colnect Scraping)
    ↓
Phase 3 (RAG Pipeline)
    ↓
Phase 4 (Identification)
    ↓
Phase 5 (Browser Automation)
    ↓
Phase 6 (Migration) ← Can run in parallel with 5
    ↓
Phase 7 (Polish)
```

**Minimum Viable Product (Phases 1-5):** Identification capability working
**Full Product (Phases 1-7):** Migration and polish complete

---

## File Creation Order

### Phase 1 Files
1. `src/core/config.py` (rewrite)
2. `src/core/errors.py` (extend)
3. `src/core/database.py` (new)
4. `src/cli.py` (new)
5. `.env.app` (fix)

### Phase 2 Files
6. `src/scraping/__init__.py`
7. `src/scraping/browser.py`
8. `src/scraping/colnect.py`

### Phase 3 Files
9. `src/vision/__init__.py`
10. `src/vision/describer.py`
11. `src/rag/__init__.py`
12. `src/rag/embeddings.py`
13. `src/rag/supabase_client.py`
14. `src/rag/indexer.py`
15. `src/rag/search.py`

### Phase 4 Files
16. `src/vision/camera.py`
17. `src/vision/detector.py`
18. `src/identification/__init__.py`
19. `src/identification/identifier.py`
20. `src/identification/results.py`

### Phase 5 Files
21. `src/colnect_api/__init__.py`
22. `src/colnect_api/session.py`
23. `src/colnect_api/actions.py`

### Phase 6 Files
24. `src/scraping/lastdodo.py`
25. `src/migration/__init__.py`
26. `src/migration/matcher.py`
27. `src/migration/mapper.py`
28. `src/migration/importer.py`
29. `src/migration/review.py`

### Phase 7 Files
30. `tests/` (entire test suite)

---

## Risk Mitigations

| Risk | Mitigation |
|------|------------|
| Colnect page structure changes | Modular selectors in separate config, easy to update |
| Groq rate limits (30/min) | Built-in rate limiter with exponential backoff |
| YOLOv8 poor detection | Pre-trained model first, custom training optional (Could Have) |
| RAG match quality | Tune prompt, try larger Groq model if needed |
| Chrome CDP issues | Clear error messages, setup documentation |
| Supabase free tier | Monitor usage (~350MB expected, limit 500MB) |

---

## Success Criteria

- [ ] `stamp-tools init` creates database, downloads YOLO, verifies APIs
- [ ] `stamp-tools scrape colnect` scrapes ~50,000 space stamps with checkpoint
- [ ] `stamp-tools rag index` indexes all stamps in ~6-16 hours
- [ ] `stamp-tools identify camera` identifies stamps with >80% accuracy
- [ ] `stamp-tools migrate import --dry-run` matches 80%+ of LASTDODO items
- [ ] All tests pass
- [ ] Monthly cost < €1
