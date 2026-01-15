# CLAUDE.md Template

Use this template as a starting point for new Python AI/ML projects. Copy, customize, and rename to `CLAUDE.md` in your project root.

---

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

[PROJECT_NAME] is a [brief description]. It processes [inputs] and generates [outputs].

## Common Commands

### Running the Application

```bash
# Start full application (Streamlit UI + FastAPI backend)
python run_app.py

# Start UI only (port 8507)
python run_app.py --ui-only

# Start backend only (port 8000)
python run_app.py --backend-only
```

### Docker Commands

```bash
# Build and start multi-container setup
docker-compose up --build

# Development mode with hot-reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_specific.py -v
```

### Development Tools

```bash
# Code formatting
black src/ tests/

# Linting
flake8 src/ tests/

# Import sorting
isort src/ tests/
```

## Architecture Overview

### Three-Layer Architecture

1. **Frontend (UI Layer)**: Streamlit application
2. **Backend (API Layer)**: FastAPI application
3. **Data Layer**: Supabase (PostgreSQL + pgvector)

### Project Structure

```
project-root/
├── src/
│   ├── api/              # FastAPI backend
│   │   ├── routers/      # API endpoints
│   │   └── services/     # Business logic
│   ├── core/             # Configuration, logging, errors
│   ├── data_models/      # Pydantic models
│   ├── rag/              # RAG pipeline (if applicable)
│   ├── tools/            # CLI tools
│   └── ui/               # Streamlit pages
├── tests/                # Test suite
├── config/               # Configuration files
├── docker/               # Docker files
├── docs/                 # Documentation
├── .env.app              # App defaults (committed)
├── .env.keys             # Secrets (gitignored)
├── .env.local            # Local overrides (gitignored)
└── pyproject.toml        # Project configuration
```

## Configuration Management

### Four-Tier Environment System

Files are loaded in order (later overrides earlier):
1. `.env.app` - Application defaults (committed)
2. `.env.keys` - API keys & secrets (NEVER commit)
3. `.env.local` - User-specific overrides
4. `.env.docker` - Docker-specific overrides

### Standard Configuration Pattern

```python
from core.config import get_settings

settings = get_settings()  # Singleton cached instance
api_key = settings.GROQ_API_KEY
```

### LLM Configuration (Groq Primary)

```bash
# Primary LLM (Groq - fast inference, cost-effective)
AGENT_PROVIDER="groq"
GROQ_API_KEY="gsk_..."
GROQ_MODEL="openai/gpt-oss-120b"
GROQ_TEMPERATURE=0.3
GROQ_MAX_TOKENS=8192

# Embeddings (OpenAI - industry standard)
OPENAI_API_KEY="sk-..."
RAG_EMBEDDING_MODEL="text-embedding-3-small"

# Fallback (optional)
ANTHROPIC_API_KEY="sk-ant-..."
```

**Recommended Groq Models:**
- `openai/gpt-oss-120b` - **Default** - Best quality, complex reasoning
- `llama-3.3-70b-versatile` - General purpose, document analysis
- `llama-3.1-8b-instant` - Fast responses, simple tasks
- `mixtral-8x7b-32768` - Long context (32k tokens)

### Path Construction Rules

**ALWAYS use `Path(a, b, c)` for joining paths - NEVER use `/` operator**

```python
from pathlib import Path

# CORRECT
data_file = Path(settings.DATA_DIR, "subfolder", "file.txt")

# WRONG - Never use / operator
data_file = settings.DATA_DIR / "subfolder" / "file.txt"
```

## Logging Standards

### Standard Import Pattern
```python
import logging
import inspect
from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)  # ALWAYS use __name__
```

### Message Formatting

```python
# Function entry - include function name
logger.debug(
    f" * {inspect.currentframe().f_code.co_name} > Starting with param={param}"
)

# Debug messages - use "    -> " prefix for operational flow
logger.debug("    -> Operation completed successfully")
logger.debug(f"    -> Processing {count} documents")

# Info - important status updates
logger.info("Processing started")

# Warning - recoverable issues
logger.warning("Using fallback method")

# Error - with context
logger.error(f"Failed to process: {error}")
```

### Error Logging with Context
```python
try:
    result = process_data(data)
except Exception as e:
    error_context = {
        'input': data,
        'error_type': type(e).__name__
    }
    logger.error(f"Processing failed: {e} | Context: {error_context}")
    raise
```

### Project-Aware Logging
```python
from core.logging import set_log_directory

# Set project-specific log directory
set_log_directory(project_id="12345", project_name="My Project")
```

### Environment Configuration (.env.app)
```bash
LOG_LEVEL="INFO"
LOG_MAX_SIZE_MB=2
LOG_BACKUP_COUNT=5
LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(funcName)s:%(lineno)d]"
LOG_FILE_NAME="app.log"
LOG_DIR="logs"
```

## Development Guidelines

### Data Validation

Use Pydantic models for all data structures:

```python
from pydantic import BaseModel, Field

class MyModel(BaseModel):
    name: str
    count: int = Field(default=0, ge=0)
```

### Error Handling

```python
try:
    result = process_data(data)
except Exception as e:
    logger.error(f"Processing failed: {e}")
    raise
```

### Code Style

- Follow PEP8
- Use type hints for all functions
- Format with `black` (line length: 100)
- Write Google-style docstrings

### Testing Strategy

- Write `pytest` unit tests for new features
- Each feature needs: expected case, edge case, failure case tests
- Use markers: `@pytest.mark.unit`, `@pytest.mark.integration`

## Key Architectural Patterns

### Multi-Engine Fallback

For document processing, use fallback pattern:
```python
engines = [PrimaryEngine, FallbackEngine1, FallbackEngine2]
for engine in engines:
    try:
        return engine.process(document)
    except EngineError:
        continue
raise ProcessingError("All engines failed")
```

### Background Processing

Long operations should use CLI tools launched as background processes:
```python
import subprocess

process = subprocess.Popen(
    ['python', 'tools/process_cli.py', '--id', item_id],
    stdout=subprocess.PIPE
)
```

### UI State Management

All state through `st.session_state`:
```python
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.data = []
```

## Important Notes

- **Secrets**: NEVER commit `.env.keys`
- **Configuration**: Always access via `get_settings()` singleton
- **Logging**: Use standard Python logging with `logging.getLogger(__name__)`
- **Testing**: Run `pytest` before committing

## Documentation

- `docs/DESIGN.md` - Architecture and design principles
- `docs/TECHNICAL.md` - Technical implementation details
- `docs/guides/` - How-to guides
