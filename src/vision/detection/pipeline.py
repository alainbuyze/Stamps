"""Detection pipeline orchestrating Stage 1A, 1B, and 1C."""

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

from .polygon_detector import PolygonDetector, DetectionConfig, DetectedPolygon
from .stamp_classifier import StampClassifier, ClassifierConfig, StampClassification
from .yolo_detector import YOLODetector, YOLOConfig

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the detection pipeline."""

    # Stage 1A: Polygon detection
    polygon_config: DetectionConfig = None

    # Stage 1B: Stamp classification
    classifier_config: ClassifierConfig = None

    # Stage 1C: YOLO fallback
    yolo_config: YOLOConfig = None
    enable_yolo_fallback: bool = True

    def __post_init__(self):
        if self.polygon_config is None:
            self.polygon_config = DetectionConfig()
        if self.classifier_config is None:
            self.classifier_config = ClassifierConfig()
        if self.yolo_config is None:
            self.yolo_config = YOLOConfig()


@dataclass
class DetectedStamp:
    """Final output from detection pipeline."""

    detection_id: str               # Unique ID
    shape_type: str                 # "triangle" | "quadrilateral"
    bounding_box: tuple             # (x, y, w, h)
    vertices: Optional[np.ndarray]  # Polygon vertices (if from CV)
    cropped_image: np.ndarray       # Clean crop for identification

    # Stage 1B results
    classifier_passed: bool
    classifier_confidence: float
    classifier_reason: str
    classifier_details: dict

    # Source info
    source: str                     # "polygon_cv" | "yolo_fallback"
    detection_confidence: float     # From detector (CV or YOLO)

    def to_feedback_data(self) -> dict:
        """Convert to data suitable for DetectionFeedback."""
        return {
            "detection_id": self.detection_id,
            "shape_type": self.shape_type,
            "bounding_box": self.bounding_box,
            "stage_1b_passed": self.classifier_passed,
            "stage_1b_confidence": self.classifier_confidence,
            "stage_1b_reason": self.classifier_reason,
            "stage_1b_details": self.classifier_details,
        }


class DetectionPipeline:
    """
    Orchestrates the two-stage detection pipeline.

    Stage 1A: Classical CV polygon detection (fast, no ML)
    Stage 1B: Heuristic stamp classifier (filters false positives)
    Stage 1C: YOLO fallback (if Stage 1A returns nothing)

    The pipeline returns DetectedStamp objects ready for Stage 2 (RAG identification).
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()

        # Initialize components
        self.polygon_detector = PolygonDetector(self.config.polygon_config)
        self.classifier = StampClassifier(self.config.classifier_config)
        self.yolo_detector = None  # Lazy loaded

        logger.debug("DetectionPipeline initialized")

    def _get_yolo_detector(self) -> Optional[YOLODetector]:
        """Lazy load YOLO detector."""
        if self.yolo_detector is None and self.config.enable_yolo_fallback:
            self.yolo_detector = YOLODetector(self.config.yolo_config)
        return self.yolo_detector

    def detect_stamps(
        self,
        image: np.ndarray,
        use_yolo_fallback: bool = True,
    ) -> tuple[list[DetectedStamp], list[DetectedStamp]]:
        """
        Run full detection pipeline on image.

        Args:
            image: BGR image from camera or file
            use_yolo_fallback: Whether to use YOLO if CV finds nothing

        Returns:
            Tuple of (accepted_stamps, rejected_shapes)
            - accepted_stamps: Passed classifier, ready for RAG
            - rejected_shapes: Failed classifier, for feedback
        """
        logger.info(f"Starting detection pipeline on image {image.shape}")

        accepted = []
        rejected = []

        # Stage 1A: Polygon detection
        polygons = self.polygon_detector.detect(image)
        logger.debug(f"Stage 1A: Found {len(polygons)} polygons")

        # Stage 1B: Classify each polygon
        for i, polygon in enumerate(polygons):
            classification = self.classifier.classify(polygon.cropped_image)

            stamp = DetectedStamp(
                detection_id=f"cv_{i+1:03d}",
                shape_type=polygon.shape_type,
                bounding_box=polygon.bounding_box,
                vertices=polygon.vertices,
                cropped_image=polygon.cropped_image,
                classifier_passed=classification.is_stamp,
                classifier_confidence=classification.confidence,
                classifier_reason=classification.reason,
                classifier_details=classification.details,
                source="polygon_cv",
                detection_confidence=polygon.confidence,
            )

            if classification.is_stamp:
                accepted.append(stamp)
                logger.debug(f"    -> Polygon {i+1}: ACCEPTED ({classification.confidence:.2f})")
            else:
                rejected.append(stamp)
                logger.debug(f"    -> Polygon {i+1}: REJECTED ({classification.reason})")

        logger.info(f"Stage 1B: {len(accepted)} accepted, {len(rejected)} rejected")

        # Stage 1C: YOLO fallback if no stamps found
        if len(accepted) == 0 and use_yolo_fallback and self.config.enable_yolo_fallback:
            logger.info("Stage 1C: No stamps found, trying YOLO fallback")
            yolo_stamps = self._run_yolo_fallback(image)
            accepted.extend(yolo_stamps)
            logger.info(f"Stage 1C: YOLO found {len(yolo_stamps)} stamps")

        return accepted, rejected

    def _run_yolo_fallback(self, image: np.ndarray) -> list[DetectedStamp]:
        """Run YOLO detection as fallback."""
        yolo = self._get_yolo_detector()

        if yolo is None or not yolo.is_available():
            logger.warning("YOLO fallback not available")
            return []

        detections = yolo.detect(image)
        stamps = []

        for i, det in enumerate(detections):
            # Run classifier on YOLO detections too
            if det.cropped_image is not None:
                classification = self.classifier.classify(det.cropped_image)
            else:
                classification = StampClassification(
                    is_stamp=True,
                    confidence=det.confidence,
                    reason="yolo_detection",
                    details={"yolo_confidence": det.confidence}
                )

            if classification.is_stamp:
                stamp = DetectedStamp(
                    detection_id=f"yolo_{i+1:03d}",
                    shape_type="quadrilateral",  # YOLO returns rectangles
                    bounding_box=det.bounding_box,
                    vertices=None,
                    cropped_image=det.cropped_image,
                    classifier_passed=True,
                    classifier_confidence=classification.confidence,
                    classifier_reason="yolo_fallback",
                    classifier_details=classification.details,
                    source="yolo_fallback",
                    detection_confidence=det.confidence,
                )
                stamps.append(stamp)

        return stamps

    def visualize_all(
        self,
        image: np.ndarray,
        accepted: list[DetectedStamp],
        rejected: list[DetectedStamp],
    ) -> np.ndarray:
        """
        Create visualization with all detections colored by status.

        Args:
            image: Original image
            accepted: Accepted stamps (green)
            rejected: Rejected shapes (red)

        Returns:
            Annotated image
        """
        import cv2

        output = image.copy()

        # Draw rejected in red
        for stamp in rejected:
            x, y, w, h = stamp.bounding_box
            cv2.rectangle(output, (x, y), (x + w, y + h), (0, 0, 255), 2)
            label = f"X {stamp.classifier_reason[:10]}"
            cv2.putText(output, label, (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        # Draw accepted in green (or purple for YOLO)
        for stamp in accepted:
            x, y, w, h = stamp.bounding_box
            color = (255, 0, 255) if stamp.source == "yolo_fallback" else (0, 255, 0)

            # Draw polygon if available
            if stamp.vertices is not None:
                pts = stamp.vertices.reshape((-1, 1, 2)).astype(np.int32)
                cv2.polylines(output, [pts], True, color, 2)
            else:
                cv2.rectangle(output, (x, y), (x + w, y + h), color, 2)

            label = f"{stamp.classifier_confidence:.0%}"
            cv2.putText(output, label, (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        return output


def create_pipeline_from_env() -> DetectionPipeline:
    """
    Create detection pipeline from environment configuration.

    Reads settings from Pydantic Settings.
    """
    from src.core.config import get_settings

    settings = get_settings()

    polygon_config = DetectionConfig(
        mode=getattr(settings, 'DETECTION_MODE', 'album'),
        min_vertices=getattr(settings, 'DETECTION_MIN_VERTICES', 3),
        max_vertices=getattr(settings, 'DETECTION_MAX_VERTICES', 4),
        min_area_ratio=getattr(settings, 'DETECTION_MIN_AREA_RATIO', 0.001),
        max_area_ratio=getattr(settings, 'DETECTION_MAX_AREA_RATIO', 0.15),
        aspect_ratio_min=getattr(settings, 'DETECTION_ASPECT_RATIO_MIN', 0.3),
        aspect_ratio_max=getattr(settings, 'DETECTION_ASPECT_RATIO_MAX', 3.0),
        approx_epsilon=getattr(settings, 'DETECTION_APPROX_EPSILON', 0.02),
    )

    classifier_config = ClassifierConfig(
        mode=getattr(settings, 'CLASSIFIER_MODE', 'heuristic'),
        confidence_threshold=getattr(settings, 'CLASSIFIER_CONFIDENCE_THRESHOLD', 0.6),
        color_variance_weight=getattr(settings, 'CLASSIFIER_COLOR_VARIANCE_WEIGHT', 0.35),
        edge_complexity_weight=getattr(settings, 'CLASSIFIER_EDGE_COMPLEXITY_WEIGHT', 0.30),
        size_weight=getattr(settings, 'CLASSIFIER_SIZE_WEIGHT', 0.20),
        perforation_weight=getattr(settings, 'CLASSIFIER_PERFORATION_WEIGHT', 0.15),
        model_path=getattr(settings, 'CLASSIFIER_MODEL_PATH', None),
    )

    yolo_config = YOLOConfig(
        model_path=settings.YOLO_MODEL_PATH,
        confidence_threshold=settings.YOLO_CONFIDENCE_THRESHOLD,
        auto_download=getattr(settings, 'YOLO_AUTO_DOWNLOAD', True),
    )

    pipeline_config = PipelineConfig(
        polygon_config=polygon_config,
        classifier_config=classifier_config,
        yolo_config=yolo_config,
        enable_yolo_fallback=getattr(settings, 'DETECTION_FALLBACK_TO_YOLO', True),
    )

    return DetectionPipeline(pipeline_config)
