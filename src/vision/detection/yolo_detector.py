"""Stage 1C: YOLO fallback detector for stamp detection.

Used when Stage 1A (polygon detection) finds no candidates.
Provides a ML-based fallback using YOLOv8.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class YOLOConfig:
    """Configuration for YOLO detector."""

    model_path: str = "models/yolov8n.pt"
    confidence_threshold: float = 0.5
    auto_download: bool = True

    # Stamp-specific filtering
    min_size_ratio: float = 0.01    # Min size as ratio of image
    max_size_ratio: float = 0.5     # Max size as ratio of image
    aspect_ratio_min: float = 0.3
    aspect_ratio_max: float = 3.0


@dataclass
class YOLODetection:
    """A detection from YOLO."""

    bounding_box: tuple             # (x, y, w, h)
    confidence: float               # Detection confidence
    cropped_image: Optional[np.ndarray] = None  # Cropped region
    class_name: str = "stamp"       # YOLO class name


class YOLODetector:
    """
    Stage 1C: YOLO-based stamp detection as fallback.

    Uses YOLOv8 for object detection when classical CV methods fail.
    Lazy loads the model only when needed.
    """

    def __init__(self, config: Optional[YOLOConfig] = None):
        self.config = config or YOLOConfig()
        self._model = None
        self._available = None  # Cached availability check
        logger.debug(f"YOLODetector initialized with model_path={self.config.model_path}")

    def is_available(self) -> bool:
        """Check if YOLO is available (ultralytics installed)."""
        if self._available is not None:
            return self._available

        try:
            import ultralytics  # noqa: F401
            self._available = True
        except ImportError:
            logger.warning("ultralytics not installed, YOLO fallback unavailable")
            self._available = False

        return self._available

    def _ensure_model_loaded(self) -> bool:
        """Lazy load the YOLO model."""
        if self._model is not None:
            return True

        if not self.is_available():
            return False

        try:
            from ultralytics import YOLO

            model_path = Path(self.config.model_path)

            if not model_path.exists() and self.config.auto_download:
                logger.info(f"YOLO model not found at {model_path}, downloading...")
                # Use the model name which triggers auto-download
                model_name = model_path.stem  # e.g., "yolov8n"
                self._model = YOLO(f"{model_name}.pt")
                # Save to expected location
                model_path.parent.mkdir(parents=True, exist_ok=True)
            elif model_path.exists():
                self._model = YOLO(str(model_path))
            else:
                logger.error(f"YOLO model not found at {model_path} and auto_download disabled")
                return False

            logger.debug("YOLO model loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            return False

    def detect(self, image: np.ndarray) -> list[YOLODetection]:
        """
        Detect stamps in image using YOLO.

        Args:
            image: BGR image from camera or file

        Returns:
            List of YOLODetection objects
        """
        if not self._ensure_model_loaded():
            logger.warning("YOLO model not available, returning empty results")
            return []

        logger.debug(f"YOLO detecting stamps in image {image.shape}")

        try:
            # Run inference
            results = self._model(
                image,
                conf=self.config.confidence_threshold,
                verbose=False,
            )

            detections = []
            image_area = image.shape[0] * image.shape[1]

            for result in results:
                boxes = result.boxes

                if boxes is None or len(boxes) == 0:
                    continue

                for box in boxes:
                    # Extract box data
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = result.names.get(class_id, "unknown")

                    # Convert to (x, y, w, h) format
                    w = x2 - x1
                    h = y2 - y1

                    # Apply stamp heuristics
                    box_area = w * h
                    area_ratio = box_area / image_area

                    # Filter by size
                    if area_ratio < self.config.min_size_ratio:
                        continue
                    if area_ratio > self.config.max_size_ratio:
                        continue

                    # Filter by aspect ratio
                    aspect = w / h if h > 0 else 0
                    if aspect < self.config.aspect_ratio_min or aspect > self.config.aspect_ratio_max:
                        continue

                    # Crop the region
                    cropped = image[y1:y2, x1:x2].copy()

                    detection = YOLODetection(
                        bounding_box=(x1, y1, w, h),
                        confidence=confidence,
                        cropped_image=cropped,
                        class_name=class_name,
                    )
                    detections.append(detection)

                    logger.debug(
                        f"    -> YOLO detected: {class_name} ({confidence:.0%}) "
                        f"at ({x1}, {y1}) size {w}x{h}"
                    )

            logger.info(f"YOLO detected {len(detections)} potential stamps")
            return detections

        except Exception as e:
            logger.error(f"YOLO detection failed: {e}")
            return []

    def detect_raw(self, image: np.ndarray) -> list[YOLODetection]:
        """
        Detect all objects without stamp filtering.

        Useful for debugging or when working with a stamp-specific model.

        Args:
            image: BGR image from camera or file

        Returns:
            List of YOLODetection objects (unfiltered)
        """
        if not self._ensure_model_loaded():
            return []

        try:
            results = self._model(
                image,
                conf=self.config.confidence_threshold,
                verbose=False,
            )

            detections = []

            for result in results:
                boxes = result.boxes

                if boxes is None or len(boxes) == 0:
                    continue

                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = result.names.get(class_id, "unknown")

                    w = x2 - x1
                    h = y2 - y1

                    cropped = image[y1:y2, x1:x2].copy()

                    detection = YOLODetection(
                        bounding_box=(x1, y1, w, h),
                        confidence=confidence,
                        cropped_image=cropped,
                        class_name=class_name,
                    )
                    detections.append(detection)

            return detections

        except Exception as e:
            logger.error(f"YOLO raw detection failed: {e}")
            return []
