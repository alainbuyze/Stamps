# Technical Stack Reference

This document serves as a reference for the default technical stack patterns used in this project. Use it as a template for similar Python-based AI/ML applications.

## Overview

This stack is designed for AI-powered document processing applications with the following characteristics:
- Multi-format document ingestion (PDF, Word, PowerPoint)
- RAG (Retrieval-Augmented Generation) semantic search
- AI-powered synthesis and generation
- Multi-container deployment

---

## 1. Core Framework Stack

### Backend API: FastAPI
```
fastapi
uvicorn              # ASGI server
pydantic             # Data validation
pydantic-settings    # Configuration management
python-jose          # JWT authentication
```

**Why FastAPI:**
- Async-first design for I/O-bound AI operations
- Automatic OpenAPI documentation
- Native Pydantic integration for request/response validation
- Easy dependency injection

### Frontend UI: Streamlit
```
streamlit
altair               # Charting
```

**Why Streamlit:**
- Rapid prototyping for data-centric applications
- Built-in session state management
- Easy integration with Python data processing
- Live reload during development

### Database: Supabase (PostgreSQL + pgvector)
```
supabase
postgrest
vecs                 # Vector operations
```

**Why Supabase:**
- PostgreSQL with pgvector for semantic search
- Built-in authentication
- Real-time subscriptions
- REST API auto-generation

---

## 2. AI/ML Stack

### LLM Providers (Multi-provider support)
```
groq                 # Primary LLM provider (fast inference, cost-effective)
openai               # Secondary provider (embeddings, fallback)
anthropic>=0.54.0    # Claude models (complex reasoning)
google-generativeai  # Gemini models (multimodal)
```

**Why Groq as Primary:**
- Extremely fast inference (lowest latency)
- Cost-effective for high-volume processing
- Compatible with OpenAI API format
- Excellent for document processing and RAG queries

### Groq Configuration
```bash
# Primary LLM Configuration
GROQ_API_KEY="gsk_..."
GROQ_MODEL="openai/gpt-oss-120b"      # Best balance of speed/quality
GROQ_TEMPERATURE=0.3                       # Lower for consistent outputs
GROQ_MAX_TOKENS=8192
GROQ_REASONING_EFFORT="medium"             # low, medium, high
```

**Recommended Groq Models:**
| Model | Use Case |
|-------|----------|
| `openai/gpt-oss-120b` | **Default** - Best quality, complex reasoning |
| `llama-3.3-70b-versatile` | General purpose, document analysis |
| `llama-3.1-8b-instant` | Fast responses, simple tasks |
| `mixtral-8x7b-32768` | Long context (32k tokens) |

### Agent Framework: PydanticAI
```
pydantic-ai          # Agent orchestration
```

**Why PydanticAI:**
- Type-safe agent definitions
- Built-in tool pattern with `@agent.tool` decorator
- Structured outputs with Pydantic models
- Provider-agnostic (works with Groq, OpenAI, Anthropic, Gemini)

### Embeddings & Semantic Search
```
sentence-transformers # Local embeddings (optional)
tiktoken             # Token counting
cohere               # Reranking (optional)
```

### NLP Tools
```
spacy                # Named entity recognition
nltk                 # Text processing
langdetect           # Language detection
rapidfuzz            # Fuzzy string matching
```

---

## 3. Document Processing Stack

### PDF Processing (Multi-engine fallback pattern)
```
PyMuPDF              # Fast PDF parsing (primary)
pymupdf4llm          # LLM-optimized extraction
pdf2image            # PDF to image conversion
pdfminer.six         # Text extraction
pypdf                # PDF manipulation
marker-pdf           # Vision-based extraction
```

### Document Analysis
```
unstructured[all-docs] # Universal document loader
docling[vlm,easyocr]   # Vision-language models
```

### OCR
```
pytesseract          # Tesseract OCR
pillow               # Image processing
opencv-python        # Computer vision
```

### Office Documents
```
python-pptx          # PowerPoint generation (implied)
python-docx          # Word documents (implied)
openpyxl             # Excel files (implied)
```

---

## 4. Web Scraping Stack

```
playwright           # Browser automation (primary)
beautifulsoup4       # HTML parsing
requests             # HTTP client
aiohttp              # Async HTTP
httpx                # Modern HTTP client
```

**Pattern:** Smart browser selection with fallback:
```
Brave (with profile) → Chromium → Standard Chromium → Playwright-managed
```

---

## 5. Configuration Management

### Four-Tier Environment System
```
.env.app             # Application defaults (committed, Docker-included)
.env.keys            # API keys & secrets (gitignored, NEVER commit)
.env.local           # User-specific overrides (gitignored)
.env.docker          # Docker-specific overrides (committed)
```

Files are loaded in order (later overrides earlier).

### Configuration Pattern (Pydantic Settings)
```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.app", ".env.keys", ".env.local", ".env.docker"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )

    # Define fields with validation
    API_KEY: str = Field(..., description="API key")
    MAX_RETRIES: int = Field(default=3, description="Max retry attempts")

# Singleton pattern
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### Environment Variable Naming
- **UPPERCASE** for all configuration values
- **Prefixed** by category: `RAG_`, `OPENAI_`, `BROWSER_`, etc.
- **Suffixed** by type: `_PATH`, `_DIR`, `_URL`, `_KEY`, etc.

---

## 6. Code Quality & Testing

### Formatting & Linting
```
black                # Code formatter (line-length: 100)
flake8               # Linting
isort                # Import sorting
```

### Testing
```
pytest               # Test framework
pytest-cov           # Coverage reporting
pytest-asyncio       # Async test support
pytest-mock          # Mocking
pytest-env           # Environment variables for tests
```

### pyproject.toml Configuration
```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
addopts = "-v --cov=src --cov-report=term-missing"

[tool.black]
line-length = 100
target-version = ['py312', 'py311', 'py310', 'py39', 'py38']

[tool.isort]
line_length = 88
include_trailing_comma = true
multi_line_output = 3

[tool.flake8]
max-line-length = 100
extend-ignore = ["E203", "E501"]
```

---

## 7. Docker & Infrastructure

### Multi-Container Architecture
```yaml
services:
  app-ui:            # Streamlit frontend (port 8507)
  app-api:           # FastAPI backend (port 8000)
  app-worker:        # Background processing (optional)
  redis:             # Job queue (optional)
```

### Dockerfile Patterns
- Multi-stage builds for size optimization
- Non-root user for security
- Health checks for all services
- Four-tier env system in containers

### Docker Compose Features
```yaml
# Profile-based optional services
profiles:
  - worker
  - background-jobs
  - full

# Health checks
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

---

## 8. Project Structure

```
project-root/
├── src/
│   ├── api/              # FastAPI backend
│   │   ├── routers/      # API endpoints
│   │   └── services/     # Business logic
│   ├── core/             # Configuration, logging, errors
│   ├── data_models/      # Pydantic models
│   ├── document_processing/  # Document handlers
│   ├── presentation/     # Output generation
│   ├── project_processing/   # Project workflows
│   ├── rag/              # RAG pipeline
│   │   ├── chunkers/     # Document chunking
│   │   ├── database/     # Vector store
│   │   ├── enrichers/    # Contextual enrichment
│   │   ├── loaders/      # Document loading
│   │   ├── pipeline/     # Orchestration
│   │   └── vectorizers/  # Embedding generation
│   ├── tools/            # CLI tools
│   ├── ui/               # Streamlit pages
│   └── web_scraping/     # Web scraping utilities
├── tests/                # Test suite
├── config/               # Configuration files
├── docker/               # Docker files
├── docs/                 # Documentation
├── .env.app              # App defaults
├── .env.keys             # Secrets (gitignored)
├── .env.local            # Local overrides (gitignored)
├── .env.docker           # Docker overrides
├── pyproject.toml        # Project configuration
└── requirements.txt      # Dependencies
```

---

## 9. RAG Pipeline Architecture

### Pipeline Flow
```
Source Documents → Loader → Metadata Extraction → Chunker
→ Contextual Enricher → Vectorizer → Vector Store
→ Similarity Search + AI Synthesis → Response with Sources
```

### Chunking Strategies
- **SEMANTIC**: NLP-based boundary detection
- **TOKEN_BASED**: Fixed token windows
- **HYBRID**: Combination approach (recommended)

### Configuration Parameters
```bash
RAG_CHUNK_SIZE=600           # Target chunk size (tokens)
RAG_CHUNK_OVERLAP=150        # Overlap between chunks
RAG_EMBEDDING_MODEL=text-embedding-3-small
RAG_VECTOR_SEARCH_TOP_K=20   # Results to retrieve
RAG_SIMILARITY_THRESHOLD=0.7 # Minimum similarity
RAG_ENABLE_CONTEXTUAL_ENRICHMENT=True
RAG_PARALLEL_PROCESSING=True
```

### Database Schema (pgvector)
```sql
-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,  -- For change detection
    metadata JSONB
);

-- Chunks with embeddings
CREATE TABLE rag_chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    content TEXT NOT NULL,
    embedding VECTOR(1536),   -- OpenAI dimensions
    chunk_index INTEGER,
    -- Dedicated metadata columns for performance
    section_title TEXT,
    document_type TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vector index
CREATE INDEX ON rag_chunks USING ivfflat (embedding vector_cosine_ops);
```

---

## 10. Logging Standards

The logging system provides centralized configuration, structured error reporting, dynamic log directories, and automatic rotation.

### Standard Import Pattern
```python
import logging
import inspect
from core.GOVC_config import get_settings

# Get application settings
settings = get_settings()

# Initialize logger for the module - ALWAYS use __name__
logger = logging.getLogger(__name__)
```

**Key Rules:**
- Always use `logging.getLogger(__name__)` for module-specific loggers
- Import settings via `get_settings()` singleton
- No custom logging utilities - use standard Python logging only

### Environment Configuration (.env.app)
```bash
# Logging Configuration
LOG_LEVEL="INFO"
LOG_MAX_SIZE_MB=2
LOG_BACKUP_COUNT=5
LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(funcName)s:%(lineno)d]"
LOG_FILE_NAME="app.log"
LOG_ERROR_FILE_NAME="error.log"
LOG_DIR="logs"
```

### Logging Levels and Message Formatting

#### Debug Messages - Use `    -> ` Prefix
```python
# Debug messages for operational flow and success
logger.debug("    -> Operation completed successfully")
logger.debug(f"    -> Processing {count} documents")
logger.debug(f"    -> Response received in {elapsed_time:.2f}s")
```

#### Function Entry Logging - Include Function Name
```python
import inspect

logger.debug(
    f" * {inspect.currentframe().f_code.co_name} > Starting operation with param={param}"
)
```

#### Standard Levels
```python
# Debug - operational flow and success messages
logger.debug("    -> Initialized client successfully")

# Info - important status updates
logger.info("Processing started")

# Warning - recoverable issues
logger.warning("Using fallback method due to API limit")

# Error - errors and exceptions
logger.error(f"Failed to process document: {error}")
```

### Project-Aware Logging
```python
from core.GOVC_logging import set_log_directory, reset_log_directory

# Set project-specific logging
set_log_directory(project_id="12345", project_name="My Project")
# Logs go to: {ROOT_PROJECT_DIR_PATH}/12345_My_Project/logs/

# Reset to default when done
reset_log_directory()
```

### Complete Logging Example
```python
import logging
import inspect
from pathlib import Path
from typing import Dict, Any
from core.GOVC_config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Example processor following logging standards."""

    def __init__(self, model_name: str = None):
        logger.debug(
            f" * {inspect.currentframe().f_code.co_name} > Initializing with model={model_name}"
        )
        self.model_name = model_name or settings.DEFAULT_MODEL
        logger.debug(f"    -> Using model: {self.model_name}")
        logger.debug("    -> DocumentProcessor initialized successfully")

    def process_document(self, document_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a document with comprehensive logging."""
        options = options or {}
        logger.debug(
            f" * {inspect.currentframe().f_code.co_name} > Processing: {document_path}"
        )
        logger.debug(f"    -> Options: {options}")

        try:
            # Validate input
            if not document_path or not Path(document_path).exists():
                error_msg = f"Invalid document path: {document_path}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.debug("    -> Input validation passed")

            # Process
            logger.debug("    -> Starting document analysis")
            result = self._analyze(document_path, options)
            logger.debug(f"    -> Analysis completed: {result.get('status')}")

            logger.info(f"Document processed successfully: {document_path}")
            return result

        except Exception as e:
            # Include context in error
            error_context = {
                'document_path': document_path,
                'options': options,
                'error_type': type(e).__name__
            }
            logger.error(f"Processing failed: {e} | Context: {error_context}")
            raise
```

### Progress Logging for Batch Operations
```python
def process_batch(self, items: list) -> list:
    logger.info(f"Starting batch processing of {len(items)} items")

    results = []
    for i, item in enumerate(items, 1):
        logger.debug(f"    -> Processing item {i}/{len(items)}: {item.get('id', 'unknown')}")

        try:
            result = self.process_item(item)
            logger.debug(f"    -> Item {i} processed successfully")
            results.append(result)

        except Exception as e:
            logger.error(f"Failed to process item {i}: {str(e)}")
            continue

    logger.info(f"Batch processing completed: {len(results)}/{len(items)} successful")
    return results
```

### Logging Key Takeaways

1. **Always use standard Python logging** - no custom utilities
2. **Follow the import pattern** - `logging.getLogger(__name__)` and `get_settings()`
3. **Use consistent formatting** - `    -> ` prefix for debug messages
4. **Include function names** - use `inspect.currentframe().f_code.co_name`
5. **Log at appropriate levels** - debug for flow, info for status, error for failures
6. **Provide context in errors** - include relevant parameters and state
7. **Configure via environment** - all settings in `.env.app` file
8. **Use project-specific directories** - leverage `set_log_directory()` for organization

---

## 11. Path Construction Rules

**CRITICAL:** Always use `Path(a, b, c)` for joining paths. NEVER use the `/` operator.

```python
from pathlib import Path

# CORRECT
data_file = Path(settings.DATA_DIR, "subfolder", "file.txt")
config_path = Path(project_root, "config", "settings.json")

# WRONG - Never use / operator
data_file = settings.DATA_DIR / "subfolder" / "file.txt"
```

---

## 12. Error Handling Pattern

### Custom Exceptions
```python
# In core/errors.py
class DocumentProcessingError(Exception):
    """Base exception for document processing errors."""
    pass

class ChunkingError(DocumentProcessingError):
    """Error during document chunking."""
    pass

class VectorizationError(DocumentProcessingError):
    """Error during embedding generation."""
    pass
```

### Error Context Pattern
```python
try:
    result = process_document(doc_path)
except Exception as e:
    error_context = {
        'document_path': str(doc_path),
        'error_type': type(e).__name__,
        'operation': 'process_document'
    }
    logger.error(f"Processing failed: {e} | Context: {error_context}")
    raise
```

---

## 13. Data Validation Pattern

Use Pydantic models for all data structures:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class DocumentMetadata(BaseModel):
    """Metadata for a processed document."""
    file_path: str
    file_hash: str
    document_type: str
    page_count: int
    processed_at: datetime = Field(default_factory=datetime.now)
    sections: List[str] = Field(default_factory=list)

class ChunkResult(BaseModel):
    """Result from document chunking."""
    chunk_index: int
    content: str
    token_count: int
    metadata: Optional[DocumentMetadata] = None
```

---

## 14. Async Patterns

### Async Context Manager for Resources
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_browser():
    browser = await playwright.chromium.launch()
    try:
        yield browser
    finally:
        await browser.close()

# Usage
async with get_browser() as browser:
    page = await browser.new_page()
    await page.goto(url)
```

### Parallel Processing with Limits
```python
import asyncio
from typing import List

async def process_batch(items: List, max_concurrent: int = 4):
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_limit(item):
        async with semaphore:
            return await process_item(item)

    return await asyncio.gather(*[process_with_limit(i) for i in items])
```

---

## 15. Background Job Pattern

### CLI Tool Pattern
```python
# tools/process_cli.py
import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-id', required=True)
    parser.add_argument('--mode', default='full')
    args = parser.parse_args()

    # Status file for UI tracking
    status_file = Path(f"status_{args.project_id}.json")

    def update_status(stage: str, progress: float):
        status_file.write_text(json.dumps({
            'stage': stage,
            'progress': progress,
            'timestamp': datetime.now().isoformat()
        }))

    # Process with status updates
    update_status('starting', 0.0)
    # ... processing ...
    update_status('complete', 1.0)

if __name__ == '__main__':
    main()
```

### UI Integration
```python
import subprocess
import json

# Launch background job
process = subprocess.Popen(
    ['python', 'tools/process_cli.py', '--project-id', project_id],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Poll status file
status = json.loads(Path(f"status_{project_id}.json").read_text())
st.progress(status['progress'])
```

---

## 16. Multi-Provider LLM Pattern

### Provider Selection Strategy
```python
from core.config import get_settings

settings = get_settings()

# Provider hierarchy (configured in .env.app)
AGENT_PROVIDER = "groq"          # Primary: fast, cost-effective
FALLBACK_PROVIDER = "openai"     # Fallback: reliable, full-featured

# Task-specific providers
EMBEDDING_PROVIDER = "openai"    # OpenAI embeddings are industry standard
REASONING_PROVIDER = "anthropic" # Claude for complex reasoning (optional)
```

### LLM Client Factory Pattern
```python
from groq import Groq
from openai import OpenAI
from anthropic import Anthropic

def get_llm_client(provider: str = None):
    """Get LLM client based on provider configuration."""
    provider = provider or settings.AGENT_PROVIDER

    if provider == "groq":
        return Groq(api_key=settings.GROQ_API_KEY)
    elif provider == "openai":
        return OpenAI(api_key=settings.OPENAI_API_KEY)
    elif provider == "anthropic":
        return Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    else:
        raise ValueError(f"Unknown provider: {provider}")
```

### Environment Configuration
```bash
# Primary LLM (Groq)
AGENT_PROVIDER="groq"
GROQ_API_KEY="gsk_..."
GROQ_MODEL="openai/gpt-oss-120b"
GROQ_TEMPERATURE=0.3
GROQ_MAX_TOKENS=8192

# Embeddings (OpenAI - industry standard)
OPENAI_API_KEY="sk-..."
RAG_EMBEDDING_MODEL="text-embedding-3-small"

# Fallback/Complex Reasoning (optional)
ANTHROPIC_API_KEY="sk-ant-..."
ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
```

---

## Summary

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend API** | FastAPI | Async REST API |
| **Frontend** | Streamlit | Data-centric UI |
| **Database** | Supabase + pgvector | Vector storage |
| **Primary LLM** | Groq (gpt-oss-120b) | Fast inference, document processing |
| **Embeddings** | OpenAI text-embedding-3 | Semantic search vectors |
| **Fallback LLM** | OpenAI, Anthropic | Complex tasks, reliability |
| **Agents** | PydanticAI | Agent orchestration |
| **PDF** | PyMuPDF, Marker, Unstructured | Document parsing |
| **OCR** | Tesseract, Docling | Text extraction |
| **Web Scraping** | Playwright | Browser automation |
| **Config** | Pydantic Settings | Environment management |
| **Testing** | pytest | Test framework |
| **Formatting** | black, isort | Code quality |
| **Container** | Docker Compose | Deployment |

This stack is optimized for:
- **Fast AI inference** with Groq as primary LLM
- AI-powered document processing
- Semantic search and RAG
- Multi-provider LLM support with fallbacks
- Scalable containerized deployment
- Type-safe Python development
