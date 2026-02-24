"""Vision module for stamp image analysis.

Components:
- describer: Groq vision API integration for generating stamp descriptions
- camera: OpenCV camera capture (Phase 4)
- detector: YOLOv8 stamp detection (Phase 4)
"""

from src.vision.describer import StampDescriber

__all__ = ["StampDescriber"]
