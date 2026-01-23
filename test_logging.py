"""Test script for the logging module."""

from src.core.logging import setup_logging, get_logger

# Initialize logging
print("Setting up logging...")
setup_logging()

# Get a logger
logger = get_logger("test_module")

# Test different log levels
print("\nTesting log levels:")
logger.debug("This is a DEBUG message")
logger.info("This is an INFO message")
logger.warning("This is a WARNING message")
logger.error("This is an ERROR message")
logger.critical("This is a CRITICAL message")

print("\n--- Logging test complete ---")
print("Check logs/ directory for app.log and errors.log")
