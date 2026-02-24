"""YOLOv8 stamp detection for identifying stamps in images.

Uses Ultralytics YOLOv8 for object detection. Initially uses the
pre-trained model which can detect general objects. Can be fine-tuned
for stamp-specific detection with labeled training data.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image

from src.core.config import get_settings
from src.core.errors import DetectionError
from src.vision.camera import CapturedImage

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """Bounding box for a detected object."""

    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    class_id: int
    class_name: str

    @property
    def width(self) -> int:
        """Width of bounding box."""
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        """Height of bounding box."""
        return self.y2 - self.y1

    @property
    def area(self) -> int:
        """Area of bounding box in pixels."""
        return self.width * self.height

    @property
    def center(self) -> tuple[int, int]:
        """Center point (x, y) of bounding box."""
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    @property
    def aspect_ratio(self) -> float:
        """Aspect ratio (width/height)."""
        return self.width / self.height if self.height > 0 else 0


@dataclass
class DetectedStamp:
    """A detected stamp with its cropped image."""

    bbox: BoundingBox
    cropped_frame: np.ndarray
    index: int

    @property
    def pil_image(self) -> Image.Image:
        """Convert cropped stamp to PIL Image (RGB)."""
        rgb_frame = cv2.cvtColor(self.cropped_frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_frame)

    def save(self, path: Path) -> None:
        """Save cropped stamp image to file.

        Args:
            path: Output file path
        """
        cv2.imwrite(str(path), self.cropped_frame)
        logger.debug(f"Saved stamp {self.index} to {path}")

    def to_bytes(self, format: str = "JPEG") -> bytes:
        """Convert to bytes for API upload.

        Args:
            format: Image format (JPEG, PNG)

        Returns:
            Image bytes
        """
        from io import BytesIO

        pil_img = self.pil_image
        buffer = BytesIO()
        pil_img.save(buffer, format=format)
        return buffer.getvalue()


@dataclass
class DetectionResult:
    """Result of stamp detection on an image."""

    stamps: list[DetectedStamp]
    source_image: CapturedImage
    model_name: str

    @property
    def count(self) -> int:
        """Number of stamps detected."""
        return len(self.stamps)

    def get_annotated_image(self) -> np.ndarray:
        """Get source image with detection boxes drawn.

        Returns:
            Annotated image with bounding boxes
        """
        annotated = self.source_image.frame.copy()

        for stamp in self.stamps:
            bbox = stamp.bbox
            # Draw rectangle
            cv2.rectangle(
                annotated,
                (bbox.x1, bbox.y1),
                (bbox.x2, bbox.y2),
                (0, 255, 0),
                2,
            )
            # Draw label
            label = f"Stamp {stamp.index} ({bbox.confidence:.0%})"
            cv2.putText(
                annotated,
                label,
                (bbox.x1, bbox.y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

        return annotated

    def save_annotated(self, path: Path) -> None:
        """Save annotated image with detection boxes.

        Args:
            path: Output file path
        """
        annotated = self.get_annotated_image()
        cv2.imwrite(str(path), annotated)
        logger.debug(f"Saved annotated image to {path}")


class StampDetector:
    """Detects stamps in images using YOLOv8.

    Note: The pre-trained YOLOv8 model detects general objects.
    For stamp-specific detection, the model should be fine-tuned
    with labeled stamp images. Currently, we detect all objects
    and filter by size/aspect ratio to approximate stamp detection.
    """

    # Common aspect ratios for stamps (width/height)
    STAMP_ASPECT_RATIOS = (0.5, 2.0)  # Min and max
    # Minimum stamp size relative to image
    MIN_STAMP_SIZE_RATIO = 0.01
    MAX_STAMP_SIZE_RATIO = 0.5

    def __init__(
        self,
        model_path: Optional[Path] = None,
        confidence_threshold: Optional[float] = None,
        use_stamp_heuristics: bool = True,
    ):
        """Initialize the stamp detector.

        Args:
            model_path: Path to YOLOv8 model weights (defaults to settings)
            confidence_threshold: Minimum detection confidence (defaults to settings)
            use_stamp_heuristics: Apply size/aspect ratio filters for stamp detection
        """
        settings = get_settings()
        self.model_path = model_path or Path(settings.YOLO_MODEL_PATH)
        self.confidence_threshold = confidence_threshold or settings.YOLO_CONFIDENCE_THRESHOLD
        self.use_stamp_heuristics = use_stamp_heuristics
        self._model = None

    def _ensure_model_loaded(self) -> None:
        """Lazy load the YOLO model."""
        if self._model is not None:
            return

        logger.debug(f" * StampDetector._ensure_model_loaded > Loading from {self.model_path}")

        try:
            from ultralytics import YOLO

            # Check if model exists, otherwise it will auto-download
            if not self.model_path.exists():
                logger.info(f"YOLO model not found at {self.model_path}, downloading...")
                # Use the model name which triggers auto-download
                model_name = self.model_path.stem  # e.g., "yolov8n"
                self._model = YOLO(f"{model_name}.pt")
                # Save to expected location
                self.model_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                self._model = YOLO(str(self.model_path))

            logger.debug("    -> Model loaded successfully")

        except Exception as e:
            raise DetectionError(f"Failed to load YOLO model: {e}") from e

    def detect(
        self,
        image: CapturedImage,
        fallback_to_full_image: bool = True,
    ) -> DetectionResult:
        """Detect stamps in an image.

        Args:
            image: CapturedImage to analyze
            fallback_to_full_image: If no stamps detected, treat entire image as one stamp

        Returns:
            DetectionResult with detected stamps

        Raises:
            DetectionError: If detection fails
        """
        self._ensure_model_loaded()

        logger.debug(f" * StampDetector.detect > Analyzing {image.source}")

        try:
            # Run inference
            results = self._model(
                image.frame,
                conf=self.confidence_threshold,
                verbose=False,
            )

            stamps = []
            stamp_index = 0

            # Process detections
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

                    bbox = BoundingBox(
                        x1=x1,
                        y1=y1,
                        x2=x2,
                        y2=y2,
                        confidence=confidence,
                        class_id=class_id,
                        class_name=class_name,
                    )

                    # Apply stamp heuristics if enabled
                    if self.use_stamp_heuristics:
                        if not self._is_likely_stamp(bbox, image):
                            logger.debug(f"    -> Filtered out: {class_name} at {bbox.center}")
                            continue

                    # Crop the stamp region
                    cropped = image.frame[y1:y2, x1:x2].copy()

                    stamp = DetectedStamp(
                        bbox=bbox,
                        cropped_frame=cropped,
                        index=stamp_index,
                    )
                    stamps.append(stamp)
                    stamp_index += 1

                    logger.debug(
                        f"    -> Detected: {class_name} ({confidence:.0%}) "
                        f"at ({x1}, {y1}) - ({x2}, {y2})"
                    )

            # Fallback: if no stamps detected, treat entire image as one stamp
            # This handles the common case where the image IS the stamp
            if not stamps and fallback_to_full_image:
                logger.info("No objects detected - treating entire image as stamp")
                bbox = BoundingBox(
                    x1=0,
                    y1=0,
                    x2=image.width,
                    y2=image.height,
                    confidence=1.0,
                    class_id=-1,
                    class_name="full_image",
                )
                stamp = DetectedStamp(
                    bbox=bbox,
                    cropped_frame=image.frame.copy(),
                    index=0,
                )
                stamps.append(stamp)

            logger.info(f"Detected {len(stamps)} potential stamps")

            return DetectionResult(
                stamps=stamps,
                source_image=image,
                model_name=str(self.model_path),
            )

        except Exception as e:
            raise DetectionError(f"Detection failed: {e}") from e

    def _is_likely_stamp(self, bbox: BoundingBox, image: CapturedImage) -> bool:
        """Apply heuristics to filter likely stamp detections.

        Args:
            bbox: Bounding box to evaluate
            image: Source image for size reference

        Returns:
            True if detection is likely a stamp
        """
        image_area = image.width * image.height
        box_area_ratio = bbox.area / image_area

        # Check size constraints
        if box_area_ratio < self.MIN_STAMP_SIZE_RATIO:
            return False  # Too small
        if box_area_ratio > self.MAX_STAMP_SIZE_RATIO:
            return False  # Too large (probably the whole page)

        # Check aspect ratio (stamps are typically rectangular, not too elongated)
        min_ratio, max_ratio = self.STAMP_ASPECT_RATIOS
        if not (min_ratio <= bbox.aspect_ratio <= max_ratio):
            return False  # Wrong aspect ratio

        return True

    def detect_all(self, image: CapturedImage) -> DetectionResult:
        """Detect all objects without stamp heuristics.

        Useful for debugging or when the image is known
        to contain only stamps.

        Args:
            image: CapturedImage to analyze

        Returns:
            DetectionResult with all detections
        """
        original_heuristics = self.use_stamp_heuristics
        self.use_stamp_heuristics = False
        try:
            return self.detect(image)
        finally:
            self.use_stamp_heuristics = original_heuristics


class SimpleStampDetector:
    """Simple stamp detector using contour detection.

    An alternative to YOLO that uses classical computer vision
    techniques. Useful when stamps are well-separated on a
    contrasting background.
    """

    def __init__(
        self,
        min_area: int = 5000,
        max_area: Optional[int] = None,
        aspect_ratio_range: tuple[float, float] = (0.5, 2.0),
    ):
        """Initialize simple detector.

        Args:
            min_area: Minimum contour area in pixels
            max_area: Maximum contour area (None for no limit)
            aspect_ratio_range: Valid (min, max) aspect ratios
        """
        self.min_area = min_area
        self.max_area = max_area
        self.aspect_ratio_range = aspect_ratio_range

    def detect(self, image: CapturedImage) -> DetectionResult:
        """Detect stamps using contour detection.

        Args:
            image: CapturedImage to analyze

        Returns:
            DetectionResult with detected stamps
        """
        logger.debug(f" * SimpleStampDetector.detect > Analyzing {image.source}")

        # Convert to grayscale
        gray = cv2.cvtColor(image.frame, cv2.COLOR_BGR2GRAY)

        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        stamps = []
        stamp_index = 0

        for contour in contours:
            area = cv2.contourArea(contour)

            # Filter by area
            if area < self.min_area:
                continue
            if self.max_area and area > self.max_area:
                continue

            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)

            # Check aspect ratio
            aspect_ratio = w / h if h > 0 else 0
            min_ratio, max_ratio = self.aspect_ratio_range
            if not (min_ratio <= aspect_ratio <= max_ratio):
                continue

            bbox = BoundingBox(
                x1=x,
                y1=y,
                x2=x + w,
                y2=y + h,
                confidence=0.8,  # Arbitrary confidence for contour detection
                class_id=0,
                class_name="stamp",
            )

            # Crop the stamp region
            cropped = image.frame[y:y + h, x:x + w].copy()

            stamp = DetectedStamp(
                bbox=bbox,
                cropped_frame=cropped,
                index=stamp_index,
            )
            stamps.append(stamp)
            stamp_index += 1

            logger.debug(f"    -> Found contour: {w}x{h} at ({x}, {y})")

        logger.info(f"Detected {len(stamps)} potential stamps via contours")

        return DetectionResult(
            stamps=stamps,
            source_image=image,
            model_name="contour_detection",
        )
