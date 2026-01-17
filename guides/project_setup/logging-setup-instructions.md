# Logging Setup Instructions

A comprehensive guide for setting up robust logging in Python applications using standard logging and structured logging patterns.

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Configuration Options](#2-configuration-options)
3. [Environment Setup](#3-environment-setup)
4. [Basic Usage](#4-basic-usage)
5. [Advanced Features](#5-advanced-features)
6. [Error Logging](#6-error-logging)
7. [Log Rotation & Management](#7-log-rotation--management)
8. [Integration Patterns](#8-integration-patterns)
9. [Testing Logging](#9-testing-logging)
10. [Best Practices](#10-best-practices)

---

## 1. Quick Start

### Minimal Setup

```python
from core.logging import setup_logging, log_error

# Initialize logging
setup_logging()

# Start logging
import logging
logger = logging.getLogger(__name__)
logger.info("Application started")
```

### With Error Handling

```python
from core.logging import setup_logging, log_error

setup_logging()

try:
    risky_operation()
except Exception as e:
    log_error(e, context={'operation': 'risky_operation'})
```

---

## 2. Configuration Options

### Environment Variables

Configure these in your `.env` file:

```bash
# Basic logging configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_MAX_SIZE_MB=2                 # Max file size before rotation
LOG_BACKUP_COUNT=5                 # Number of backup files to keep
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(funcName)s:%(lineno)d]
LOG_FILE_NAME=app.log             # Main application log file
LOG_ERROR_FILE_NAME=errors.log    # Error-specific log file

# Directory structure configuration
ROOT_OUTPUT_DIR=output            # Main output directory (required for /logs subdirectory)
LOG_DIR=logs                    # Logs subdirectory within ROOT_OUTPUT_DIR
```

### Default Setup for `/logs` Subdirectory

To ensure logs are always saved in a `/logs` subdirectory of your main output directory, add this to your `.env` file:

```bash
# Recommended default configuration
ROOT_OUTPUT_DIR=output
LOG_DIR=logs
LOG_LEVEL=INFO
LOG_MAX_SIZE_MB=2
LOG_BACKUP_COUNT=5
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(funcName)s:%(lineno)d]
LOG_FILE_NAME=app.log
LOG_ERROR_FILE_NAME=errors.log
```

This configuration ensures:
- Main logs go to: `output/logs/app.log`
- Error logs go to: `output/logs/errors.log`
- Automatic rotation when files exceed 2MB
- 5 backup files kept during rotation

### Directory Structure

With the recommended configuration above, your directory structure will be:

```
project_root/
├── output/
│   └── logs/
│       ├── app.log           # Main application logs
│       ├── app.log.1         # Rotated backup
│       ├── errors.log        # Error logs in JSONL format
│       └── errors.log.1      # Error log backups
```

**Note**: The `output/logs/` structure is created automatically when you use the recommended `.env` configuration. If you don't set `ROOT_OUTPUT_DIR`, logs may be saved directly to a `logs/` directory or wherever `LOG_DIR` points to.

---

## 3. Environment Setup

### Development Environment

```python
# For development - console output with colors
setup_logging()
# Logs appear in console with detailed formatting
```

### Production Environment

```python
# For production - file-based logging with rotation
import os
if os.environ.get('ENVIRONMENT') == 'production':
    setup_logging()
# Logs written to files with automatic rotation
```

### CLI vs Application Context

```python
import sys

# Detect if running as CLI subprocess
is_subprocess = not hasattr(sys, "ps1") and sys.stdin is None

if is_subprocess:
    # Simple file handler (no rotation conflicts)
    setup_logging()
else:
    # Full rotating file handler
    setup_logging()
```

---

## 4. Basic Usage

### Rich-Enhanced Logging

```python
import logging
from rich.console import Console
from src.core.logging import setup_logging

# Initialize Rich logging
setup_logging()
logger = logging.getLogger(__name__)
console = Console()

# Rich-formatted log messages
logger.info("[green]✓[/green] Process completed successfully")
logger.warning("[yellow]⚠[/yellow] Deprecated API used")
logger.error("[red]✗[/red] Connection failed")

# Rich console output for important messages
console.print("[bold blue]ℹ[/bold blue] Information: [dim]Additional details[/dim]")
console.print("[bold green]✓[/bold green] Success: Operation completed")
console.print("[bold red]✗[/bold red] Error: Something went wrong")
```

### Rich-Enhanced Context Logging

```python
import logging
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()

# Log with Rich formatting and extra context
logger.info(
    "[green]✓[/green] User action completed: [cyan]%s[/cyan]",
    "create_habit",
    extra={
        'user_id': 123,
        'action': 'create_habit',
        'duration_ms': 150
    }
)

# Rich console output with structured data
console.print("[bold]User Action:[/bold]")
console.print(f"  ID:       [cyan]{123}[/cyan]")
console.print(f"  Action:   [green]{create_habit}[/green]")
console.print(f"  Duration: [yellow]{150}ms[/yellow]")
```

### Rich-Enhanced Error Logging

```python
from src.core.logging import log_error
from rich.console import Console

console = Console()

# Log exceptions with Rich formatting and context
try:
    process_document(file_path)
except FileNotFoundError as e:
    # Rich console error display
    console.print(f"[bold red]✗ File Not Found:[/bold red] {file_path}")
    console.print(f"[dim]Operation:[/dim] document_processing")
    
    # Structured error logging
    log_error(
        e,
        context={
            'file_path': str(file_path),
            'operation': 'document_processing',
            'user_id': user.id
        },
        severity='ERROR'
    )

# Rich error with different severity levels
try:
    validate_input(data)
except ValueError as e:
    console.print(f"[bold yellow]⚠ Validation Warning:[/bold yellow] {e}")
    log_error(e, severity='WARNING')

try:
    critical_system_operation()
except SystemError as e:
    console.print(f"[bold red]✗ Critical Error:[/bold red] {e}")
    console.print("[bold white on red]System requires immediate attention![/bold white on red]")
    log_error(e, severity='CRITICAL')
```

---

## 5. Advanced Features

### Dynamic Log Directory Management

```python
# Note: The current CoderDojo implementation uses fixed log directories
# For dynamic directory management, you would extend the setup_logging function

from src.core.logging import setup_logging
from src.core.config import get_settings
from pathlib import Path

def setup_project_logging(project_id: str):
    """Setup logging for a specific project."""
    settings = get_settings()
    
    # Create project-specific log directory
    project_log_dir = settings.output_root_path / f"project_{project_id}" / "logs"
    project_log_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize Rich logging with project directory
    setup_logging()
    
    console = Console()
    console.print(f"[green]✓[/green] Logging configured for project: [cyan]{project_id}[/cyan]")
    console.print(f"[dim]Log directory:[/dim] {project_log_dir}")

# Usage
setup_project_logging("proj_123")
```

### Rich Console Integration

```python
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from src.core.logging import setup_logging

# Initialize Rich logging
setup_logging()
console = Console()

# Rich progress display
with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    console=console,
) as progress:
    task = progress.add_task("Processing documents...", total=None)
    
    for document in documents:
        process_document(document)
        progress.advance(task)

# Rich table for structured output
table = Table(title="Processing Results")
table.add_column("Status", style="cyan", no_wrap=True)
table.add_column("File", style="magenta")
table.add_column("Size", justify="right", style="green")
table.add_column("Time", justify="right", style="yellow")

table.add_row("✓", "doc1.pdf", "2.4 MB", "1.2s")
table.add_row("✓", "doc2.pdf", "1.8 MB", "0.8s")
table.add_row("✗", "doc3.pdf", "3.1 MB", "2.1s")

console.print(table)
```

### Temporary Log Level Changes

```python
from core.logging import set_temporary_log_level, restore_original_log_level
import logging

logger = logging.getLogger(__name__)

# Temporarily enable debug logging
original_level = set_temporary_log_level(logger, logging.DEBUG)
try:
    # Debug operations here
    complex_operation()
finally:
    # Restore original level
    restore_original_log_level(logger, original_level)
```

---

## 6. Error Logging

### Standard Error Logging

```python
from core.logging import log_error

# Log exception with automatic context capture
try:
    database_operation()
except Exception as e:
    log_error(e, severity='ERROR')
```

### Error with Custom Context

```python
try:
    api_client.call_external_service()
except ConnectionError as e:
    log_error(
        e,
        context={
            'service': 'external_api',
            'endpoint': '/api/data',
            'retry_count': 3,
            'timeout_seconds': 30
        },
        severity='ERROR'
    )
```

### Error Severity Levels

```python
try:
    validate_input(data)
except ValueError as e:
    log_error(e, severity='WARNING')  # Not critical, user can fix

try:
    critical_system_operation()
except SystemError as e:
    log_error(e, severity='CRITICAL')  # Requires immediate attention
```

### Retrieving Recent Errors

```python
# Note: The current CoderDojo implementation writes errors to JSONL files
# You can read and parse these files for recent errors

import json
from pathlib import Path
from src.core.config import get_settings
from rich.console import Console
from rich.table import Table

def get_recent_errors(max_count: int = 50, severity: str = None) -> list:
    """Read recent errors from JSONL error log."""
    settings = get_settings()
    error_file = settings.log_path / settings.LOG_ERROR_FILE_NAME
    
    if not error_file.exists():
        return []
    
    errors = []
    with open(error_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                error_entry = json.loads(line.strip())
                if severity is None or error_entry.get('severity') == severity:
                    errors.append(error_entry)
                    if len(errors) >= max_count:
                        break
            except json.JSONDecodeError:
                continue
    
    return errors[-max_count:]  # Return most recent

# Display recent errors in a Rich table
console = Console()
recent_errors = get_recent_errors(max_count=10)

if recent_errors:
    table = Table(title="Recent Errors")
    table.add_column("Time", style="cyan")
    table.add_column("Type", style="red")
    table.add_column("Message", style="yellow")
    
    for error in recent_errors:
        timestamp = error['timestamp'][:19]  # Remove microseconds
        table.add_row(timestamp, error['error_type'], error['error_message'][:50])
    
    console.print(table)
else:
    console.print("[green]✓[/green] No recent errors found")
```

---

## 7. Log Rotation & Management

### Automatic Rotation

Logs automatically rotate when they exceed `LOG_MAX_SIZE_MB`:

```python
# When app.log reaches 2MB:
# app.log -> app.log.1
# New app.log created
# Old app.log.1 -> app.log.2 (if backup_count > 1)
```

### Manual Log Cleanup

```python
from core.logging import cleanup_old_logs

# Remove logs older than 7 days
cleanup_old_logs(days=7)

# Remove logs older than 30 days
cleanup_old_logs(days=30)
```

### Log File Monitoring

```python
from pathlib import Path
from src.core.config import get_settings
from rich.console import Console
from rich.table import Table

def monitor_log_files():
    """Display log file information using Rich formatting."""
    settings = get_settings()
    log_dir = settings.log_path
    console = Console()
    
    if not log_dir.exists():
        console.print(f"[red]✗[/red] Log directory not found: {log_dir}")
        return
    
    # Create Rich table for log file info
    table = Table(title="Log File Status")
    table.add_column("File", style="cyan")
    table.add_column("Size", justify="right", style="green")
    table.add_column("Modified", style="yellow")
    
    # Check log file sizes
    for log_file in sorted(log_dir.glob("*.log*")):
        size_mb = log_file.stat().st_size / (1024 * 1024)
        modified = log_file.stat().st_mtime
        import datetime
        modified_time = datetime.datetime.fromtimestamp(modified).strftime("%Y-%m-%d %H:%M")
        
        # Color code based on size
        size_str = f"{size_mb:.2f} MB"
        if size_mb > 5:  # Large file
            size_str = f"[red]{size_str}[/red]"
        elif size_mb > 2:  # Medium file
            size_str = f"[yellow]{size_str}[/yellow]"
        else:  # Small file
            size_str = f"[green]{size_str}[/green]"
        
        table.add_row(log_file.name, size_str, modified_time)
    
    console.print(table)

# Usage
monitor_log_files()
```

---

## 8. Integration Patterns

### FastAPI Integration

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.logging import setup_logging, log_error

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup logging on startup
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("FastAPI application starting")
    
    yield
    
    logger.info("FastAPI application shutting down")

app = FastAPI(lifespan=lifespan)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    log_error(exc, context={'path': str(request.url)})
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

### CLI Application Integration

```python
import argparse
import logging
from src.core.logging import setup_logging
from rich.console import Console

def main():
    """CLI application with Rich logging integration."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-id', help='Project ID for context')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    # Setup Rich logging with optional debug level
    log_level = 'DEBUG' if args.debug else None
    setup_logging(level=log_level)
    
    logger = logging.getLogger(__name__)
    console = Console()
    
    # Rich startup message
    console.print("[bold green]✓[/bold green] CLI Application Started")
    if args.project_id:
        console.print(f"[dim]Project ID:[/dim] [cyan]{args.project_id}[/cyan]")
    if args.debug:
        console.print("[yellow]⚠[/yellow] Debug mode enabled")
    
    logger.info(f"CLI started with project: {args.project_id}")
    
    # Application logic here
    try:
        process_cli_command(args)
        console.print("[bold green]✓[/bold green] Command completed successfully")
    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Command failed: {e}")
        logger.error(f"Command failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
```

### Background Job Integration

```python
import asyncio
import logging
from src.core.logging import setup_logging
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

async def background_worker():
    """Background worker with Rich logging and progress."""
    setup_logging()
    logger = logging.getLogger(__name__)
    console = Console()
    
    console.print("[bold blue]ℹ[/bold blue] Background worker started")
    
    while True:
        try:
            # Show progress while waiting for jobs
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Waiting for jobs...", total=None)
                
                job = await get_next_job()
                progress.update(task, description=f"Processing job {job.id}...")
                
                logger.info(f"[green]✓[/green] Processing job {job.id}")
                
                result = await process_job(job)
                progress.update(task, description=f"[green]✓[/green] Job {job.id} completed")
                
                logger.info(f"[green]✓[/green] Job {job.id} completed successfully")
                console.print(f"[green]✓[/green] Job {job.id} completed: {result}")
                
        except Exception as e:
            console.print(f"[bold red]✗[/bold red] Job processing error: {e}")
            logger.error(f"[red]✗[/red] Job error: {e}")
            await asyncio.sleep(5)  # Brief pause on error

# Start background worker
asyncio.create_task(background_worker())
```

---
## 9. Testing Logging

### 9.1. Unit Testing with Log Capture

```python
import logging
import pytest
from unittest.mock import patch, MagicMock
from src.core.logging import log_error, setup_logging

def test_log_error_creates_entry():
    """Test that log_error creates proper log entry"""
    with patch('src.core.logging.settings') as mock_settings:
        mock_settings.LOG_DIR = Path('/tmp/test_logs')
        mock_settings.LOG_DIR.mkdir(exist_ok=True)
        
        # Capture log output
        with patch('src.core.logging.logger') as mock_logger:
            log_error(Exception("Test error"), context={'test': True})
            
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Exception: Test error" in call_args[0][0]
            assert call_args[1]['extra']['context']['test'] is True

def test_ui_notification_callback():
    """Test UI notification integration"""
    callback = MagicMock()
    set_ui_notification_callback(callback)
    
    log_error("Test error", severity='ERROR')
    
    callback.assert_called_once()
    call_args = callback.call_args[0]
    assert "Test error" in call_args[0]
    assert call_args[1] == 'ERROR'
    assert 'Vlaamse Vergunning Advisor' in call_args[2]
```

### 9.2. Integration Testing with Real Files

```python
import tempfile
import json
from pathlib import Path
from src.core.logging import setup_logging, log_error, get_recent_errors

def test_end_to_end_logging():
    """Test complete logging flow with real files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Override settings for test
        with patch('src.core.logging.settings') as mock_settings:
            mock_settings.LOG_DIR = Path(temp_dir)
            mock_settings.LOG_DIR_PATH = Path(temp_dir)
            mock_settings.LOG_FILE_NAME = 'test.log'
            mock_settings.LOG_ERROR_FILE_NAME = 'test_errors.jsonl'
            mock_settings.LOG_LEVEL = 'INFO'
            mock_settings.LOG_FORMAT = '%(message)s'
            mock_settings.LOG_MAX_SIZE_MB = 1
            mock_settings.LOG_BACKUP_COUNT = 3
            
            # Setup logging
            setup_logging()
            
            # Log an error
            test_error = ValueError("Test validation error")
            log_error(test_error, context={'user_id': 123})
            
            # Verify error file was created and contains entry
            error_file = Path(temp_dir) / 'test_errors.jsonl'
            assert error_file.exists()
            
            # Read and verify error entry
            with open(error_file, 'r') as f:
                error_line = f.readline().strip()
                error_entry = json.loads(error_line)
                
                assert error_entry['error_type'] == 'ValueError'
                assert error_entry['error_message'] == 'Test validation error'
                assert error_entry['context']['user_id'] == 123
                assert error_entry['severity'] == 'ERROR'
```

### 9.3. Log Level Testing

```python
import logging
from core.logging import set_temporary_log_level, restore_original_log_level

def test_temporary_log_level():
    """Test temporary log level changes"""
    logger = logging.getLogger('test_logger')
    original_level = logger.level
    
    # Test temporary change
    temp_level = set_temporary_log_level(logger, logging.DEBUG)
    assert temp_level == original_level
    assert logger.level == logging.DEBUG
    
    # Test restoration
    restore_original_log_level(logger, temp_level)
    assert logger.level == original_level
```

---

## 10. Best Practices

### Rich Logging Best Practices

#### DO ✅

- **Initialize Rich logging early** - Call `setup_logging()` at application startup
- **Use Rich markup in log messages** - `[green]✓[/green]`, `[red]✗[/red]`, `[yellow]⚠[/yellow]`
- **Leverage Rich Console** - Use `Console.print()` for important user messages
- **Use Rich progress bars** - Show progress for long-running operations
- **Display structured data** - Use Rich tables for structured output
- **Use appropriate colors** - Green for success, red for errors, yellow for warnings
- **Include Rich tracebacks** - Enable `rich_tracebacks=True` for better error display

#### DON'T ❌

- **Don't overuse colors** - Too much color can reduce readability
- **Don't mix Rich and plain logging** - Stick to Rich formatting consistently
- **Don't ignore performance** - Rich formatting has overhead, use appropriately
- **Don't forget console output** - Some users may not see log files
- **Don't use complex markup** - Keep Rich markup simple and readable

#### Rich Performance Considerations

```python
# Good: Lazy Rich formatting
logger.info("Processing [cyan]%s[/cyan]", user.name)  # Only formats if level is INFO

# Avoid: String concatenation (always happens)
logger.info("Processing [cyan]" + user.name + "[/cyan]")

# For complex objects, use Rich panels
from rich.panel import Panel
from rich.text import Text

message = Panel(
    Text.from_markup(f"Processing: [cyan]{preview_display(large_object)}[/cyan]"),
    title="Info",
    border_style="blue"
)
console.print(message)
```

### Security Considerations

```python
import re

def sanitize_for_logging(data):
    """Remove sensitive information before logging"""
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if any(pattern in key.lower() for pattern in ['password', 'token', 'secret', 'key']):
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = sanitize_for_logging(value)
        return sanitized
    elif isinstance(data, str):
        # Redact potential sensitive patterns
        return re.sub(r'(password|token|secret)[=:]\s*[^\s]+', r'\1=[REDACTED]', data, flags=re.IGNORECASE)
    return data

# Usage
context = {
    'username': 'john_doe',
    'password': 'secret123',  # This will be redacted
    'action': 'login'
}

log_error(error, context=sanitize_for_logging(context))
```

---

## Troubleshooting

### Common Issues

**Logs not appearing:**
```python
# Ensure logging is initialized
setup_logging()

# Check log level
logger = logging.getLogger(__name__)
print(f"Current log level: {logger.level}")
```

**Log rotation not working:**
```python
# Check file permissions and disk space
import os
log_dir = settings.LOG_DIR
print(f"Log directory writable: {os.access(log_dir, os.W_OK)}")
print(f"Disk space: {os.statvfs(log_dir).f_bavail * os.statvfs(log_dir).f_frsize / (1024**3):.2f} GB")
```

**Unicode/encoding issues:**
```python
# Ensure UTF-8 encoding is used
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
```

### Debug Mode

```python
# Enable verbose debugging
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use temporary level change
from core.logging import set_temporary_log_level, restore_original_log_level

logger = logging.getLogger(__name__)
original = set_temporary_log_level(logger, logging.DEBUG)
try:
    # Debug operations
    debug_complex_flow()
finally:
    restore_original_log_level(logger, original)
```

---

## Resources

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Logging Best Practices](https://docs.python.org/3/howto/logging.html#logging-best-practices)
- [Log Rotation Documentation](https://docs.python.org/3/library/logging.handlers.html#rotatingfilehandler)
- [FastAPI Logging Integration](https://fastapi.tiangolo.com/tutorial/behind-a-proxy/)

---

## Quick Reference Commands

```python
# Initialize Rich logging
from src.core.logging import setup_logging
setup_logging()

# Log errors with Rich formatting
from src.core.logging import log_error
log_error(exception, context={'key': 'value'})

# Rich console operations
from rich.console import Console
console = Console()
console.print("[bold green]✓[/bold green] Operation completed successfully")
console.print("[bold red]✗[/bold red] Error occurred")

# Rich progress and tables
from rich.progress import Progress
from rich.table import Table

# Progress display
with Progress(console=console) as progress:
    task = progress.add_task("Processing...", total=100)
    # ... processing logic

# Data tables
table = Table(title="Results")
table.add_column("Status", style="green")
table.add_column("Message", style="blue")
table.add_row("✓", "Success")
console.print(table)
```

## Complete .env Template

Copy this complete template into your `.env` file for immediate setup:

```bash
# Logging Configuration - Recommended Defaults
ROOT_OUTPUT_DIR=output
LOG_DIR=logs
LOG_LEVEL=INFO
LOG_MAX_SIZE_MB=2
LOG_BACKUP_COUNT=5
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(funcName)s:%(lineno)d]
LOG_FILE_NAME=app.log
LOG_ERROR_FILE_NAME=errors.log

# Add your other application settings below...
```

This setup provides a robust, production-ready logging solution with structured error tracking, automatic rotation, and flexible configuration options.
