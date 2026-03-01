"""Vision module for stamp image analysis.

Components:
- camera: OpenCV camera capture
- describer: Groq vision API integration for generating stamp descriptions
- detection: Two-stage detection pipeline (polygon + classifier + YOLO fallback)
- detector: Legacy YOLOv8 stamp detection (kept for backwards compatibility)
"""

from src.vision.camera import CameraCapture, CapturedImage, load_image_file, list_cameras
from src.vision.describer import StampDescriber

# Legacy detector imports (for backwards compatibility)
from src.vision.detector import (
    BoundingBox,
    DetectedStamp as LegacyDetectedStamp,
    DetectionResult,
    SimpleStampDetector,
    StampDetector,
)

# New detection pipeline imports
from src.vision.detection import (
    DetectionPipeline,
    PipelineConfig,
    DetectedStamp,
    create_pipeline_from_env,
    PolygonDetector,
    DetectionConfig,
    StampClassifier,
    ClassifierConfig,
    YOLODetector,
    YOLOConfig,
)

__all__ = [
    # Camera
    "CameraCapture",
    "CapturedImage",
    "load_image_file",
    "list_cameras",
    # Describer
    "StampDescriber",
    # New detection pipeline
    "DetectionPipeline",
    "PipelineConfig",
    "DetectedStamp",
    "create_pipeline_from_env",
    "PolygonDetector",
    "DetectionConfig",
    "StampClassifier",
    "ClassifierConfig",
    "YOLODetector",
    "YOLOConfig",
    # Legacy detector (backwards compatibility)
    "BoundingBox",
    "LegacyDetectedStamp",
    "DetectionResult",
    "StampDetector",
    "SimpleStampDetector",
]
