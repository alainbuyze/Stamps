"""Stamp identification module for end-to-end identification workflow.

This module orchestrates the complete identification pipeline from camera/image
input through detection, RAG search, and result presentation.

Modules
-------
identifier.py
    StampIdentifier: Main pipeline orchestrator. Coordinates image capture,
    vision detection (via vision module), description generation, RAG search,
    and result aggregation. Supports auto, single, and multi-stamp modes.

results.py
    IdentificationSession: Container for a complete identification session
    with source image, detected stamps, and match results.
    display_results(): Rich console output for presenting match candidates
    with similarity scores, allowing user selection from top matches.

Key Exports
-----------
- StampIdentifier: Main identification pipeline
- IdentificationSession: Session data container
- display_results(): Result presentation helper
"""

from src.identification.identifier import StampIdentifier
from src.identification.results import IdentificationSession, display_results

__all__ = ["StampIdentifier", "IdentificationSession", "display_results"]
