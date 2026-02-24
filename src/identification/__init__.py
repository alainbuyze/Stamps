"""Stamp identification module.

Components:
- identifier: Pipeline orchestration for stamp identification
- results: Result display and user selection interface
"""

from src.identification.identifier import StampIdentifier
from src.identification.results import IdentificationSession, display_results

__all__ = ["StampIdentifier", "IdentificationSession", "display_results"]
