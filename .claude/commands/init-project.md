# Initialize Python Project

Set up and start a Python project in the current directory using UV for dependency management.

## Prerequisites

Ensure UV is installed globally:

**Windows (PowerShell):**
```powershell
pip install uv
```

**Windows (Command Prompt):**
```cmd
pip install uv
```

**Linux/macOS:**
```bash
pip install uv
```

## 1. Initialize UV Project

**Windows (PowerShell):**
```powershell
uv init
```

**Windows (Command Prompt):**
```cmd
uv init
```

**Linux/macOS:**
```bash
uv init
```

Creates `pyproject.toml` and `uv.lock` files for dependency management.

## 2. Install Dependencies

**Windows (PowerShell):**
```powershell
uv sync
```

**Windows (Command Prompt):**
```cmd
uv sync
```

**Linux/macOS:**
```bash
uv sync
```

Installs all Python packages including dev dependencies (pytest, ruff, httpx, etc.) as defined in `pyproject.toml`.

## 2.1. Setup Logging Configuration

Add logging configuration to your `.env.app` file:

```env
# Logging Configuration - Recommended Defaults
LOG_DIR=logs
LOG_LEVEL=INFO
LOG_MAX_SIZE_MB=2
LOG_BACKUP_COUNT=5
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(funcName)s:%(lineno)d]
LOG_FILE_NAME=app.log
LOG_ERROR_FILE_NAME=errors.log
```

This creates the following directory structure:
```
project-root/
├── output/
│   └── logs/
│       ├── app.log           # Main application logs
│       ├── app.log.1         # Rotated backup
│       ├── errors.log        # Error logs in JSONL format
│       └── errors.log.1      # Error log backups
```

## 3. Add Common Dependencies (Optional)

Add essential packages for a typical Python project:

**Windows (PowerShell):**
```powershell
# Core framework (FastAPI example)
uv add fastapi uvicorn pydantic pydantic-settings

# Development tools
uv add --dev pytest pytest-cov pytest-asyncio black isort flake8

# HTTP client
uv add httpx aiohttp

# AI/ML packages (if needed)
uv add groq openai anthropic pydantic-ai
```

**Windows (Command Prompt):**
```cmd
# Core framework (FastAPI example)
uv add fastapi uvicorn pydantic pydantic-settings

# Development tools
uv add --dev pytest pytest-cov pytest-asyncio black isort flake8

# HTTP client
uv add httpx aiohttp

# AI/ML packages (if needed)
uv add groq openai anthropic pydantic-ai
```

**Linux/macOS:**
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

**Windows (PowerShell):**
```powershell
uv run uvicorn app.main:app --reload --port 8000
```

**Windows (Command Prompt):**
```cmd
uv run uvicorn app.main:app --reload --port 8000
```

**Linux/macOS:**
```bash
uv run uvicorn app.main:app --reload --port 8000
```

For other applications, use the appropriate command:

**Windows:**
```powershell
uv run python main.py
```

**Linux/macOS:**
```bash
uv run python main.py
```

## 4.1. Application Entry Point with Logging

Create a main application file that initializes logging:

```python
# main.py
import logging
from src.core.logging import setup_logging, log_error
from src.core.config import get_settings

def main():
    """Main application entry point."""
    # Initialize logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Application starting up")
        
        # Your application logic here
        settings = get_settings()
        logger.info(f"Output directory: {settings.output_path}")
        logger.info(f"Log directory: {settings.log_path}")
        
        # Start your application
        start_application()
        
        logger.info("Application started successfully")
        
    except Exception as e:
        log_error(e, context={'phase': 'startup'})
        logger.error("Failed to start application")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
```

## 5. Run Tests

**Windows (PowerShell):**
```powershell
uv run pytest
```

**Windows (Command Prompt):**
```cmd
uv run pytest
```

**Linux/macOS:**
```bash
uv run pytest
```

## 6. Code Quality Checks

**Windows (PowerShell):**
```powershell
# Format code
uv run black .
uv run isort .

# Lint code
uv run flake8
```

**Windows (Command Prompt):**
```cmd
# Format code
uv run black .
uv run isort .

# Lint code
uv run flake8
```

**Linux/macOS:**
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
from pathlib import Path
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
    LOG_DIR: str = Field(default="logs", description="Logs directory within output")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_MAX_SIZE_MB: int = Field(default=2, description="Max log file size in MB")
    LOG_BACKUP_COUNT: int = Field(default=5, description="Number of log backup files")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(funcName)s:%(lineno)d]",
        description="Log message format"
    )
    LOG_FILE_NAME: str = Field(default="app.log", description="Main log file name")
    LOG_ERROR_FILE_NAME: str = Field(default="errors.log", description="Error log file name")

    # Application-specific settings
    API_KEY: str = Field(..., description="API key")
    MAX_RETRIES: int = Field(default=3, description="Max retry attempts")

    @property
    def output_root_path(self) -> Path:
        """Get OUTPUT_ROOT_DIR as Path object for cross-platform compatibility."""
        return Path(self.OUTPUT_ROOT_DIR)

    @property
    def output_path(self) -> Path:
        """Get OUTPUT_DIR as Path object for cross-platform compatibility."""
        return Path(self.OUTPUT_DIR)

    @property
    def cache_path(self) -> Path:
        """Get CACHE_DIR as Path object for cross-platform compatibility."""
        return Path(self.CACHE_DIR)

    @property
    def log_path(self) -> Path:
        """Get log directory path for cross-platform compatibility."""
        return self.output_root_path / self.LOG_DIR

settings = Settings()
```

## 2.2. Initialize Logging in Your Application

Create a logging setup module or add to your main application:

```python
# src/core/logging.py or main.py
import logging
import logging.handlers
from pathlib import Path
from pydantic_settings import BaseSettings

def setup_logging():
    """Initialize logging with file rotation and structured error handling."""
    settings = get_settings()
    
    # Create log directory
    log_dir = settings.log_path
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup main log file with rotation
    log_file = log_dir / settings.LOG_FILE_NAME
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=settings.LOG_MAX_SIZE_MB * 1024 * 1024,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    
    # Setup error log file (JSONL format)
    error_file = log_dir / settings.LOG_ERROR_FILE_NAME
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=settings.LOG_MAX_SIZE_MB * 1024 * 1024,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    
    # Configure formatters
    formatter = logging.Formatter(settings.LOG_FORMAT)
    file_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Also add console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

def log_error(exception: Exception, context: dict = None, severity: str = 'ERROR'):
    """Log exception with structured context."""
    import json
    import traceback
    from datetime import datetime
    
    settings = get_settings()
    error_file = settings.log_path / settings.LOG_ERROR_FILE_NAME
    
    error_entry = {
        'timestamp': datetime.now().isoformat(),
        'error_type': type(exception).__name__,
        'error_message': str(exception),
        'traceback': traceback.format_exc(),
        'context': context or {},
        'severity': severity
    }
    
    # Write to error log file
    with open(error_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(error_entry) + '\n')
    
    # Also log to standard logger
    logger = logging.getLogger(__name__)
    logger.error(f"{exception}: {context}")

# Initialize logging when module is imported
setup_logging()
```

## Windows Compatibility Guide

### Cross-Platform Path Handling

**Always use `pathlib.Path` instead of string concatenation for paths:**

```python
from pathlib import Path

# ✅ GOOD - Cross-platform compatible
output_dir = Path(settings.OUTPUT_DIR)
image_path = output_dir / "images" / "photo.jpg"
config_file = Path(__file__).parent / "config.yaml"

# ❌ BAD - Windows-specific
output_dir = settings.OUTPUT_DIR + "\\images\\photo.jpg"  # Uses backslashes
config_file = __file__ + "/../config.yaml"  # Uses forward slashes
```

**Resolving paths for subprocess commands:**

```python
import subprocess
from pathlib import Path

def run_command_with_paths(input_file: Path, output_file: Path):
    """Run subprocess command with cross-platform path handling."""
    # Convert to absolute paths to avoid working directory issues
    input_abs = input_file.resolve()
    output_abs = output_file.resolve()
    
    # Build command as list (avoids shell injection issues)
    cmd = [
        "program-name",
        "-i", str(input_abs),  # Convert Path to string
        "-o", str(output_abs),
        "--option", "value"
    ]
    
    # Run command
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,  # Handle text encoding automatically
        timeout=120
    )
    
    return result
```

### Windows-Specific Subprocess Handling

**For Windows executables (.exe files):**

```python
import shutil
from pathlib import Path

def find_windows_executable(program_name: str) -> Path | None:
    """Find Windows executable in common locations."""
    # Check configured path first
    configured_path = Path(f"C:\\Program Files\\{program_name}\\{program_name}.exe")
    if configured_path.exists():
        return configured_path
    
    # Check x86 Program Files
    x86_path = Path(f"C:\\Program Files (x86)\\{program_name}\\{program_name}.exe")
    if x86_path.exists():
        return x86_path
    
    # Check if in PATH
    which_result = shutil.which(program_name)
    if which_result:
        return Path(which_result)
    
    return None
```

**Multi-line commands for Windows:**

```python
import subprocess
from pathlib import Path

def run_complex_command(input_dir: Path, output_dir: Path):
    """Run complex command with proper Windows handling."""
    # Use absolute paths
    input_abs = input_dir.resolve()
    output_abs = output_dir.resolve()
    
    # Build command as list (works on all platforms)
    cmd = [
        "program.exe",
        "--input", str(input_abs),
        "--output", str(output_abs),
        "--recursive",
        "--threads", "4"
    ]
    
    # Set working directory if needed
    working_dir = input_abs.parent
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(working_dir),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            print(f"Command failed: {result.stderr}")
            return False
            
        print(f"Success: {result.stdout}")
        return True
        
    except subprocess.TimeoutExpired:
        print("Command timed out")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False
```

### Environment Variable Handling

**Windows environment variables in .env files:**

```env
# .env.app - Use forward slashes (Python will handle conversion)
OUTPUT_ROOT_DIR=./output
OUTPUT_DIR=./output/guides
CACHE_DIR=./cache

# Windows-specific paths (use forward slashes in .env files)
UPSCAYL_PATH=C:/Program Files/Upscayl/resources/bin/upscayl-bin.exe
PROGRAM_DATA=C:/ProgramData/MyApp/config
```

**Reading environment variables with path conversion:**

```python
import os
from pathlib import Path

def get_env_path(env_var: str, default: str = "./") -> Path:
    """Get environment variable as Path object."""
    path_str = os.getenv(env_var, default)
    return Path(path_str)

# Usage
upscayl_path = get_env_path("UPSCAYL_PATH", "./upscayl.exe")
output_dir = get_env_path("OUTPUT_DIR", "./output")
```

## Common Development Commands

**Windows (PowerShell):**
```powershell
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

**Windows (Command Prompt):**
```cmd
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

**Linux/macOS:**
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

## Windows-Specific Setup

### PowerShell Execution Policy

If you encounter PowerShell execution policy issues:

```powershell
# Check current policy
Get-ExecutionPolicy

# Set policy for current user (recommended)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or set policy for current session only
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

### Windows Terminal Setup

**Install Windows Terminal (recommended):**
- Download from Microsoft Store or GitHub
- Provides better command line experience than default Command Prompt
- Supports tabs, multiple shells, and better text rendering

**Python Path Configuration:**
- Ensure Python is in your system PATH
- UV automatically manages virtual environments, but system Python should be accessible

### Common Windows Issues

**"Command not found" errors:**
1. Ensure UV is installed and in PATH: `pip install uv`
2. Restart terminal after installation
3. Check PATH environment variable

**Permission issues:**
1. Run terminal as Administrator if needed
2. Check folder permissions for output directories
3. Use `mkdir` command to create directories if needed

**Path separator issues:**
- Always use `pathlib.Path` in Python code (never hard-code backslashes)
- Environment files can use forward slashes (Python handles conversion)
- Command line paths work with both forward and backslashes in modern Windows

## Cleanup

**To stop services:**
- Development server: `Ctrl+C` in terminal
- UV processes: `Ctrl+C` or close terminal window

**To clean up virtual environment:**
```powershell
# Windows
uv venv --clear

# Or remove .venv folder manually
rmdir /s .venv
```

## Notes

- **UV manages virtual environments automatically** - no manual venv creation needed
- **All dependencies are locked in `uv.lock`** for reproducible builds
- **Use `uv run` to execute commands** in the project environment
- **Configuration files follow four-tier system**: `.env.app`, `.env.keys`, `.env.local`, `.env.docker`
- **Cross-platform compatibility**: Use `pathlib.Path` for all file operations
- **Windows paths**: Environment variables can use forward slashes, Python handles conversion
- **Subprocess commands**: Build commands as lists, not strings, for Windows compatibility
