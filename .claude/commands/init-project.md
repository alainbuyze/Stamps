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

settings = Settings()
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
