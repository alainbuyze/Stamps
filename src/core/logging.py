"""Logging configuration for the Stamps Guide Generator.

This module provides robust, centralized logging for the application, supporting:

- Console output with Rich formatting and tracebacks
- File logging with rotation for all log levels
- Separate error log file for ERROR+ messages only
- Configurable log levels, formats, and rotation settings

Function Tree:
--------------
```
logging
├── AppLogger                              # Application-wide logger configuration class
│   ├── __init__()                        # Initialize logger using application settings
│   ├── _setup_file_handler()             # Setup rotating file handler for all logs
│   ├── _setup_console_handler()          # Setup Rich console handler
│   └── _setup_error_handler()            # Setup separate handler for error logs
├── setup_logging()                        # Initialize application-wide logging configuration
└── get_logger()                          # Get a logger instance for a module
```

Environment Configuration:
--------------------------
The following settings control logging behavior (configured in .env.app):

- **LOG_LEVEL**: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) - default: "INFO"
- **LOG_MAX_SIZE_MB**: Maximum log file size in MB before rotation - default: 2
- **LOG_BACKUP_COUNT**: Number of backup log files to keep during rotation - default: 5
- **LOG_FORMAT**: Log message format string for file output
- **LOG_FILE_NAME**: Main application log filename - default: "app.log"
- **LOG_ERROR_FILE_NAME**: Error log filename - default: "errors.log"
- **LOG_DIR**: Log directory (relative to OUTPUT_ROOT_DIR) - default: "logs"

Usage Example:
--------------
    from src.core.logging import setup_logging, get_logger

    # Initialize logging (call once at application startup)
    setup_logging()

    # Get a logger for your module
    logger = get_logger(__name__)

    # Use the logger
    logger.info("Processing started")
    logger.debug("Debug details: %s", some_data)
    logger.error("Something went wrong", exc_info=True)
"""

import logging
import logging.handlers
import sys

from rich.console import Console
from rich.logging import RichHandler

from src.core.config import get_settings


# Module-level logger
logger = logging.getLogger(__name__)

# Track if logging has been initialized
_logging_initialized = False


class AppLogger:
    """Application-wide logger configuration.

    Sets up three logging destinations:
    1. Console - Rich-formatted output with tracebacks
    2. Main log file - Rotating file with all log levels
    3. Error log file - Rotating file filtered to ERROR+ only
    """

    def __init__(self) -> None:
        """Initialize logger using application settings."""
        self.settings = get_settings()

        # Create log directory
        self.log_dir = self.settings.log_path
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Get root logger
        self.logger = logging.getLogger()

        # Set log level from settings
        log_level = getattr(logging, self.settings.LOG_LEVEL.upper(), logging.INFO)
        self.logger.setLevel(log_level)

        # Remove existing handlers to prevent duplicates
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

        # Suppress noisy third-party loggers
        noisy_loggers = [
            "httpx",
            "httpcore",
            "httpcore.http11",
            "httpcore.connection",
            "urllib3",
            "playwright",
            "charset_normalizer",
            "PIL",
        ]
        for logger_name in noisy_loggers:
            logging.getLogger(logger_name).setLevel(logging.WARNING)

        # Set up handlers
        self._setup_console_handler()
        self._setup_file_handler()
        self._setup_error_handler()

        # Log startup message
        display_path = str(self.log_dir)
        if len(display_path) > 50:
            display_path = f"...{display_path[-50:]}"
        logging.getLogger(__name__).debug(f"Logging initialized to: {display_path}")

    def _setup_console_handler(self) -> None:
        """Setup Rich console handler for formatted output."""
        # Reconfigure stdout to use UTF-8 encoding for emoji support
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass  # Ignore if reconfigure fails

        console = Console(stderr=True, force_terminal=True)

        handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            show_path=True,
            markup=True,
            show_time=True,
            show_level=True,
        )
        handler.setLevel(getattr(logging, self.settings.LOG_LEVEL.upper(), logging.INFO))

        self.logger.addHandler(handler)

    def _setup_file_handler(self) -> None:
        """Setup rotating file handler for all logs."""
        log_file = self.log_dir / self.settings.LOG_FILE_NAME

        # Ensure log file exists
        log_file.touch(exist_ok=True)

        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.settings.LOG_MAX_SIZE_MB * 1024 * 1024,
            backupCount=self.settings.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )

        formatter = logging.Formatter(self.settings.LOG_FORMAT)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _setup_error_handler(self) -> None:
        """Setup separate rotating handler for error logs only."""
        error_file = self.log_dir / self.settings.LOG_ERROR_FILE_NAME

        # Ensure error log file exists
        error_file.touch(exist_ok=True)

        handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=self.settings.LOG_MAX_SIZE_MB * 1024 * 1024,
            backupCount=self.settings.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setLevel(logging.ERROR)  # Only ERROR and above

        formatter = logging.Formatter(self.settings.LOG_FORMAT)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)


def setup_logging(level: str | None = None) -> None:
    """Initialize application-wide logging configuration.

    This sets up console output with Rich formatting, plus two log files:
    - app.log: All log messages
    - errors.log: ERROR and CRITICAL messages only

    Args:
        level: Optional log level override. Uses settings if not provided.
    """
    global _logging_initialized

    # Override log level if provided
    if level:
        settings = get_settings()
        # Temporarily override the setting (note: this doesn't persist)
        original_level = settings.LOG_LEVEL
        object.__setattr__(settings, "LOG_LEVEL", level.upper())
        AppLogger()
        object.__setattr__(settings, "LOG_LEVEL", original_level)
    else:
        AppLogger()

    _logging_initialized = True


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: The module name (typically __name__)

    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)
