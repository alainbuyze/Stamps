# Initialize Python Project

Set up and start a Python project in the current directory using UV for dependency management.

## Prerequisites

Ensure UV is installed globally:
```bash
pip install uv
```

## 1. Initialize UV Project

```bash
uv init
```

Creates `pyproject.toml` and `uv.lock` files for dependency management.

## 2. Install Dependencies

```bash
uv sync
```

Installs all Python packages including dev dependencies (pytest, ruff, httpx, etc.) as defined in `pyproject.toml`.

## 3. Add Common Dependencies (Optional)

Add essential packages for a typical Python project:

```bash
# Core framework (FastAPI example)
uv add fastapi uvicorn pydantic pydantic-settings

# Development tools
uv add --dev pytest pytest-cov pytest-asyncio black isort flake8

# HTTP client
uv add httpx aiohttp

# AI/ML packages (if needed)
uv add groq openai anthropic pydantic-ai
```

## 4. Start Development Server

For FastAPI applications:
```bash
uv run uvicorn app.main:app --reload --port 8000
```

For other applications, use the appropriate command:
```bash
uv run python main.py
```

## 5. Run Tests

```bash
uv run pytest
```

## 6. Code Quality Checks

```bash
# Format code
uv run black .
uv run isort .

# Lint code
uv run flake8
```

## Project Structure

A typical Python project structure:
```
project-root/
├── src/
│   ├── api/              # API endpoints (if FastAPI)
│   ├── core/             # Configuration, logging, errors
│   ├── data_models/      # Pydantic models
│   └── services/         # Business logic
├── tests/                # Test suite
├── .env.app              # Application defaults
├── .env.keys             # API keys (gitignored)
├── .env.local            # Local overrides (gitignored)
├── pyproject.toml        # Project configuration
└── uv.lock              # Dependency lock file
```

## Configuration

Use Pydantic Settings for configuration management:

**IMPORTANT:** Always include the output directory parameters in every project configuration to ensure consistent file organization:

- `OUTPUT_ROOT_DIR` - Root directory for all output files
- `OUTPUT_DIR` - Specific output directory for generated content  
- `CACHE_DIR` - Cache directory for temporary files

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.app", ".env.keys", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )

    # Output settings (always include these)
    OUTPUT_ROOT_DIR: str = Field(default="./output", description="Root directory for all output files")
    OUTPUT_DIR: str = Field(default="./output", description="Output directory for generated content")
    CACHE_DIR: str = Field(default="./cache", description="Cache directory for temporary files")

    # Application-specific settings
    API_KEY: str = Field(..., description="API key")
    MAX_RETRIES: int = Field(default=3, description="Max retry attempts")

settings = Settings()
```

## Common Development Commands

```bash
# Add new dependency
uv add package_name

# Add dev dependency
uv add --dev package_name

# Run Python script
uv run python script.py

# Start interactive shell
uv run python

# Update dependencies
uv sync --upgrade

# Remove dependency
uv remove package_name
```

## Cleanup

To stop services:
- Development server: Ctrl+C in terminal

## Notes

- UV manages virtual environments automatically
- All dependencies are locked in `uv.lock` for reproducible builds
- Use `uv run` to execute commands in the project environment
- Configuration files follow four-tier system: `.env.app`, `.env.keys`, `.env.local`, `.env.docker`
