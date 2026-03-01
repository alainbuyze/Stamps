"""Data models for detection feedback and scan sessions."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import numpy as np
import uuid


@dataclass
class DetectionFeedback:
    """Complete feedback for one detected shape."""

    detection_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    shape_type: str = ""                    # "triangle" | "quadrilateral"
    bounding_box: tuple = (0, 0, 0, 0)      # (x, y, w, h)
    vertices: np.ndarray = field(default_factory=lambda: np.array([]))

    # Stage 1B results
    stage_1b_passed: bool = False
    stage_1b_confidence: float = 0.0
    stage_1b_reason: str = ""               # Why rejected, if applicable
    stage_1b_details: dict = field(default_factory=dict)

    # Stage 2 results (only if stage_1b_passed)
    stage_2_searched: bool = False
    rag_match_found: bool = False
    rag_top_match: Optional[str] = None     # Colnect ID
    rag_confidence: float = 0.0
    rag_top_3: list = field(default_factory=list)

    # User action (if any)
    user_confirmed: Optional[bool] = None
    user_selected_match: Optional[str] = None
    added_to_colnect: bool = False

    # Crops for review
    cropped_image: Optional[np.ndarray] = None

    @property
    def status(self) -> str:
        """Return status for color coding."""
        if not self.stage_1b_passed:
            return "rejected"
        if not self.stage_2_searched:
            return "pending"
        if self.rag_match_found:
            return "identified"
        return "no_match"

    @property
    def color_bgr(self) -> tuple:
        """BGR color for OpenCV drawing."""
        colors = {
            "rejected": (0, 0, 255),      # Red
            "pending": (0, 255, 255),     # Yellow
            "identified": (0, 255, 0),    # Green
            "no_match": (0, 165, 255),    # Orange
        }
        return colors.get(self.status, (255, 0, 0))

    @property
    def color_name(self) -> str:
        """Color name for Rich console output."""
        colors = {
            "rejected": "red",
            "pending": "yellow",
            "identified": "green",
            "no_match": "orange1",
        }
        return colors.get(self.status, "white")

    @property
    def status_emoji(self) -> str:
        """Emoji for status display."""
        emojis = {
            "rejected": "X",
            "pending": "...",
            "identified": "OK",
            "no_match": "??",
        }
        return emojis.get(self.status, "?")

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "detection_id": self.detection_id,
            "shape_type": self.shape_type,
            "bounding_box": list(self.bounding_box),
            "status": self.status,
            "stage_1b_passed": self.stage_1b_passed,
            "stage_1b_confidence": self.stage_1b_confidence,
            "stage_1b_reason": self.stage_1b_reason,
            "stage_1b_details": self.stage_1b_details,
            "stage_2_searched": self.stage_2_searched,
            "rag_match_found": self.rag_match_found,
            "rag_top_match": self.rag_top_match,
            "rag_confidence": self.rag_confidence,
            "rag_top_3": self.rag_top_3,
            "user_confirmed": self.user_confirmed,
            "user_selected_match": self.user_selected_match,
            "added_to_colnect": self.added_to_colnect,
        }


@dataclass
class ScanSession:
    """Complete record of one scanning session."""

    session_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:6])
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "camera"                  # "camera" | "file"
    source_path: Optional[str] = None       # If from file

    # Original image
    original_image: Optional[np.ndarray] = None

    # All detections
    detections: list = field(default_factory=list)

    @property
    def summary(self) -> dict:
        """Get summary statistics."""
        statuses = [d.status for d in self.detections]
        return {
            "total_shapes": len(self.detections),
            "rejected": statuses.count("rejected"),
            "identified": statuses.count("identified"),
            "no_match": statuses.count("no_match"),
            "pending": statuses.count("pending"),
        }

    @property
    def identified_stamps(self) -> list:
        """Get only identified stamps."""
        return [d for d in self.detections if d.status == "identified"]

    @property
    def missed_stamps(self) -> list:
        """Get stamps that were detected but not matched."""
        return [d for d in self.detections if d.status == "no_match"]

    @property
    def rejected_shapes(self) -> list:
        """Get shapes that were rejected as non-stamps."""
        return [d for d in self.detections if d.status == "rejected"]

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "source_path": self.source_path,
            "summary": self.summary,
            "detections": [d.to_dict() for d in self.detections],
        }
