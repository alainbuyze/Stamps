"""Feedback system for scan session visualization and review.

This module provides visual feedback and session management for stamp scanning,
enabling review of detection results and re-ingestion of missed stamps.

Modules
-------
models.py
    DetectionFeedback: Represents feedback for a single detection including
    status (identified/needs_review/no_match/rejected), color coding, and
    match metadata.
    ScanSession: Complete session with all detections, source image, and
    timing information.

visualizer.py
    FeedbackVisualizer: Generates annotated images with color-coded detection
    boxes. Green = identified (>=90%), yellow = needs review, orange = no match,
    red = rejected as non-stamp.

session_manager.py
    SessionManager: Handles session persistence (JSON + images) to
    OUTPUT_ROOT_DIR/sessions/. Supports session archival, retrieval, and
    export of missed stamps for later re-ingestion.

console.py
    Rich console output functions for displaying scan results, session lists,
    missed stamp queues, and confirmation prompts for Colnect import.

Key Exports
-----------
- DetectionFeedback, ScanSession: Data models
- FeedbackVisualizer: Annotated image generation
- SessionManager: Session persistence
- Console functions: display_scan_results(), display_session_list(), etc.
"""

from .models import DetectionFeedback, ScanSession
from .visualizer import FeedbackVisualizer
from .session_manager import SessionManager
from .console import (
    display_scan_results,
    display_session_list,
    display_missed_stamps_list,
    prompt_add_to_colnect,
)

__all__ = [
    # Models
    "DetectionFeedback",
    "ScanSession",
    # Visualizer
    "FeedbackVisualizer",
    # Session Manager
    "SessionManager",
    # Console output
    "display_scan_results",
    "display_session_list",
    "display_missed_stamps_list",
    "prompt_add_to_colnect",
]
