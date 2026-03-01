"""Detection pipeline for identifying stamps in images.

This module provides a two-stage detection pipeline:
- Stage 1A: Classical CV polygon detection (PolygonDetector)
- Stage 1B: Heuristic stamp classifier (StampClassifier)
- Stage 1C: YOLO fallback (YOLODetector)
"""

from .polygon_detector import PolygonDetector, DetectionConfig, DetectedPolygon
from .stamp_classifier import StampClassifier, ClassifierConfig, StampClassification
from .yolo_detector import YOLODetector, YOLOConfig, YOLODetection
from .pipeline import DetectionPipeline, PipelineConfig, DetectedStamp, create_pipeline_from_env

__all__ = [
    # Stage 1A
    "PolygonDetector",
    "DetectionConfig",
    "DetectedPolygon",
    # Stage 1B
    "StampClassifier",
    "ClassifierConfig",
    "StampClassification",
    # Stage 1C
    "YOLODetector",
    "YOLOConfig",
    "YOLODetection",
    # Pipeline
    "DetectionPipeline",
    "PipelineConfig",
    "DetectedStamp",
    "create_pipeline_from_env",
]
