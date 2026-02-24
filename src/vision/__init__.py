"""Vision module for stamp image analysis.

Components:
- describer: Groq vision API integration for generating stamp descriptions
- camera: OpenCV camera capture
- detector: YOLOv8 stamp detection
"""

from src.vision.camera import CameraCapture, CapturedImage, load_image_file, list_cameras
from src.vision.describer import StampDescriber
from src.vision.detector import (
    BoundingBox,
    DetectedStamp,
    DetectionResult,
    SimpleStampDetector,
    StampDetector,
)

__all__ = [
    "CameraCapture",
    "CapturedImage",
    "load_image_file",
    "list_cameras",
    "StampDescriber",
    "BoundingBox",
    "DetectedStamp",
    "DetectionResult",
    "StampDetector",
    "SimpleStampDetector",
]
