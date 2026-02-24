"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
import tempfile
import os

from src.core.config import reset_settings


@pytest.fixture(autouse=True)
def reset_config():
    """Reset settings singleton between tests."""
    reset_settings()
    yield
    reset_settings()


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db(temp_dir):
    """Provide a temporary database path."""
    db_path = temp_dir / "test_stamps.db"
    os.environ["DATABASE_PATH"] = str(db_path)
    yield db_path
    if "DATABASE_PATH" in os.environ:
        del os.environ["DATABASE_PATH"]


@pytest.fixture
def temp_checkpoint(temp_dir):
    """Provide a temporary checkpoint file path."""
    return temp_dir / "test_checkpoint.json"
