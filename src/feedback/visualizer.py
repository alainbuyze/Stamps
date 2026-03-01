"""Generate annotated images with detection overlays."""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional

from .models import DetectionFeedback, ScanSession


class FeedbackVisualizer:
    """Generate annotated images with detection overlays."""

    # Default colors (BGR format)
    COLORS = {
        "identified": (0, 255, 0),      # Green
        "no_match": (0, 165, 255),      # Orange
        "rejected": (0, 0, 255),        # Red
        "pending": (0, 255, 255),       # Yellow
        "yolo_fallback": (255, 0, 255), # Purple
    }

    def __init__(
        self,
        font_scale: float = 0.5,
        thickness: int = 2,
        show_confidence: bool = True,
        show_legend: bool = True,
    ):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = font_scale
        self.thickness = thickness
        self.show_confidence = show_confidence
        self.show_legend = show_legend

    def annotate_image(
        self,
        image: np.ndarray,
        detections: list[DetectionFeedback],
    ) -> np.ndarray:
        """
        Draw overlays on image for all detections.

        Args:
            image: Original image (BGR format)
            detections: List of detection feedback objects

        Returns:
            Annotated image copy (original unchanged)
        """
        annotated = image.copy()

        for det in detections:
            self._draw_detection(annotated, det)

        if self.show_legend:
            self._draw_legend(annotated, detections)

        return annotated

    def annotate_session(self, session: ScanSession) -> np.ndarray:
        """Annotate a complete scan session."""
        if session.original_image is None:
            raise ValueError("Session has no original image")
        return self.annotate_image(session.original_image, session.detections)

    def _draw_detection(
        self,
        image: np.ndarray,
        detection: DetectionFeedback,
    ) -> None:
        """Draw a single detection overlay."""
        color = detection.color_bgr

        # Draw polygon outline
        if detection.vertices is not None and len(detection.vertices) > 0:
            pts = detection.vertices.reshape((-1, 1, 2)).astype(np.int32)
            cv2.polylines(image, [pts], True, color, self.thickness)
        else:
            # Fallback to bounding box
            x, y, w, h = detection.bounding_box
            cv2.rectangle(image, (x, y), (x + w, y + h), color, self.thickness)

        # Draw label
        label = self._make_label(detection)
        self._draw_label(image, label, detection.bounding_box, color)

        # Draw confidence bar for identified stamps
        if detection.status == "identified" and self.show_confidence:
            self._draw_confidence_bar(image, detection)

    def _make_label(self, detection: DetectionFeedback) -> str:
        """Create label text for detection."""
        if detection.status == "rejected":
            reason = detection.stage_1b_reason or "rejected"
            return f"X {reason[:12]}"
        elif detection.status == "identified":
            if self.show_confidence:
                return f"{detection.rag_confidence:.0%}"
            return "OK"
        elif detection.status == "no_match":
            return "NO MATCH"
        elif detection.status == "pending":
            return "..."
        return "?"

    def _draw_label(
        self,
        image: np.ndarray,
        label: str,
        bbox: tuple,
        color: tuple,
    ) -> None:
        """Draw label with background."""
        x, y, w, h = bbox

        # Get text size
        (text_w, text_h), baseline = cv2.getTextSize(
            label, self.font, self.font_scale, 1
        )

        # Position label above bounding box
        label_x = x
        label_y = y - 10

        # Ensure label is within image bounds
        if label_y - text_h - 4 < 0:
            label_y = y + h + text_h + 10  # Place below instead

        # Draw background rectangle
        cv2.rectangle(
            image,
            (label_x, label_y - text_h - 4),
            (label_x + text_w + 6, label_y + 4),
            color,
            -1  # Filled
        )

        # Draw text
        cv2.putText(
            image,
            label,
            (label_x + 3, label_y),
            self.font,
            self.font_scale,
            (255, 255, 255),  # White text
            1
        )

    def _draw_confidence_bar(
        self,
        image: np.ndarray,
        detection: DetectionFeedback,
    ) -> None:
        """Draw a small confidence bar below the detection."""
        x, y, w, h = detection.bounding_box

        bar_width = min(w, 50)
        bar_height = 5
        bar_x = x
        bar_y = y + h + 5

        # Background (gray)
        cv2.rectangle(
            image,
            (bar_x, bar_y),
            (bar_x + bar_width, bar_y + bar_height),
            (100, 100, 100),
            -1
        )

        # Filled portion (green gradient based on confidence)
        filled_width = int(bar_width * detection.rag_confidence)
        cv2.rectangle(
            image,
            (bar_x, bar_y),
            (bar_x + filled_width, bar_y + bar_height),
            detection.color_bgr,
            -1
        )

    def _draw_legend(
        self,
        image: np.ndarray,
        detections: list[DetectionFeedback],
    ) -> None:
        """Draw summary legend at bottom of image."""
        h, w = image.shape[:2]

        # Semi-transparent background for legend
        legend_height = 40
        overlay = image.copy()
        cv2.rectangle(
            overlay,
            (0, h - legend_height),
            (w, h),
            (0, 0, 0),
            -1
        )
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)

        # Count by status
        status_counts = {}
        for det in detections:
            status = det.status
            status_counts[status] = status_counts.get(status, 0) + 1

        # Draw legend items
        legend_items = [
            ("identified", "Identified", (0, 255, 0)),
            ("no_match", "No Match", (0, 165, 255)),
            ("rejected", "Rejected", (0, 0, 255)),
        ]

        x = 10
        y = h - 12

        for status, label, color in legend_items:
            count = status_counts.get(status, 0)
            if count > 0:
                # Color square
                cv2.rectangle(image, (x, y - 12), (x + 12, y), color, -1)

                # Text
                text = f"{label}: {count}"
                cv2.putText(
                    image,
                    text,
                    (x + 18, y),
                    self.font,
                    0.4,
                    (255, 255, 255),
                    1
                )

                # Move to next item
                x += 110

        # Total count on right side
        total_text = f"Total: {len(detections)}"
        text_size = cv2.getTextSize(total_text, self.font, 0.4, 1)[0]
        cv2.putText(
            image,
            total_text,
            (w - text_size[0] - 10, y),
            self.font,
            0.4,
            (255, 255, 255),
            1
        )

    def save_annotated(
        self,
        session: ScanSession,
        output_path: Path,
    ) -> Path:
        """Generate and save annotated image."""
        annotated = self.annotate_session(session)
        cv2.imwrite(str(output_path), annotated)
        return output_path
