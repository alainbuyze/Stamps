"""Feedback system for scan sessions and missed stamps.

Provides visual feedback after scanning:
- Annotated images with color-coded detections
- Session persistence for later review
- Rich console output for results display
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
