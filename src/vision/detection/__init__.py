"""OpenCV-based detection pipeline for stamp identification.

.. deprecated::
    This module is DEPRECATED. The OpenCV polygon detection approach was
    tested but rejected as unreliable for stamp detection on album pages.
    See git commit 3454cd2 for details. Use src/vision/vision_detector.py
    (Vision LLM approach) instead.

    This module may be removed in a future version. Do not add new dependencies
    on these components.

Modules (deprecated)
--------------------
polygon_detector.py
    PolygonDetector: Uses adaptive thresholding and contour detection to find
    rectangular regions. Works well on high-contrast images but fails on
    complex album backgrounds.

stamp_classifier.py
    StampClassifier: Heuristic filter for polygon candidates based on size,
    aspect ratio, and color distribution. High false positive rate.

yolo_detector.py
    YOLODetector: Pre-trained YOLOv8 fallback. Detects general objects but
    lacks stamp-specific training.

pipeline.py
    DetectionPipeline: Orchestrates the three-stage detection. Returns
    DetectedStamp objects with bounding boxes and crops.

Historical Context
------------------
This classical CV approach was the first attempt at stamp detection. While
fast and offline-capable, it proved unreliable due to:
- Variable album page backgrounds (colored, patterned, textured)
- Inconsistent lighting in camera captures
- Stamps with perforations that break contour detection
- Non-rectangular stamp shapes (triangular, circular)

The Vision LLM approach in vision_detector.py provides much better accuracy
by leveraging semantic understanding of stamp imagery.
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
