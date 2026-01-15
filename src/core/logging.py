"""Logging configuration for the CoderDojo Guide Generator."""

import logging

from rich.console import Console
from rich.logging import RichHandler

from src.core.config import get_settings


def setup_logging(level: str | None = None) -> None:
    """Configure logging with Rich formatting.

    Args:
        level: Optional log level override. Uses settings if not provided.
    """
    settings = get_settings()
    log_level = level or settings.LOG_LEVEL

    # Create console for Rich output
    console = Console(stderr=True)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                show_path=True,
                markup=True,
            )
        ],
    )

    # Set level for our package
    logging.getLogger("src").setLevel(log_level)

    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
