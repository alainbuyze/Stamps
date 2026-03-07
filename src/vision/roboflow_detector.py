"""Local stamp detection using a Roboflow-trained YOLOv8 model.

Downloads the trained .pt weights from Roboflow once, then runs fully
offline. Returns the same DetectionResult / VisionDetection types as
VisionDetector so the IdentificationPipeline needs no changes.

Usage
-----
    # One-time: download model from Roboflow
    detector = RoboflowDetector()
    detector.ensure_model_downloaded()   # saves to ROBOFLOW_MODEL_PATH

    # Every-day: local inference
    result = detector.detect(image)      # same API as VisionDetector.detect()
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from src.core.config import get_settings
from src.vision.vision_detector import DetectionResult, VisionDetection, apply_nms
from src.vision.preprocessing import create_preprocessor_from_env, PreprocessingStrategy

logger = logging.getLogger(__name__)


class RoboflowDetector:
    """
    Local YOLOv8 detector backed by a Roboflow-trained stamp model.

    Drop-in replacement for VisionDetector inside IdentificationPipeline —
    both expose the same detect(image) -> DetectionResult interface.

    Model lifecycle
    ---------------
    1. On first use, call ensure_model_downloaded() — downloads the .pt
       file from the Roboflow REST API and caches it at ROBOFLOW_MODEL_PATH.
    2. On every subsequent run the cached .pt is loaded locally (no internet).
    """

    def __init__(self, model_path: Optional[Path] = None):
        settings = get_settings()
        self.model_path = model_path or Path(settings.ROBOFLOW_MODEL_PATH)
        self.confidence_threshold = settings.ROBOFLOW_CONFIDENCE_THRESHOLD
        self.iou_threshold = settings.DETECTION_NMS_IOU_THRESHOLD
        self.inspection_dir = settings.inspection_path
        self.inspection_dir.mkdir(parents=True, exist_ok=True)
        self.preprocessor = create_preprocessor_from_env()
        self._model = None  # lazy-loaded

    # ── Public API (same shape as VisionDetector) ─────────────────────────────

    def detect(
        self,
        image: np.ndarray,
        preprocessing_strategy: Optional[PreprocessingStrategy] = None,
        inspection_id: Optional[str] = None,
    ) -> DetectionResult:
        """Detect stamps using the local Roboflow model."""
        settings = get_settings()
        result = DetectionResult(timestamp=datetime.now())

        if inspection_id is None:
            inspection_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info(f"RoboflowDetector.detect: inspection_id={inspection_id}")

        try:
            self._ensure_model_loaded()
        except Exception as e:
            result.success = False
            result.primary_error = str(e)
            logger.error(f"Model load failed: {e}")
            return result

        start = time.time()

        try:
            # YOLOv8 handles its own resizing — pass full-res image
            yolo_results = self._model(
                image,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                verbose=False,
            )

            h, w = image.shape[:2]
            detections: list[VisionDetection] = []

            for r in yolo_results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(float, box.xyxy[0].tolist())
                    conf = float(box.conf[0])

                    # Percentage box (stored in VisionDetection)
                    pct = (x1/w*100, y1/h*100, x2/w*100, y2/h*100)

                    # Pixel box as (x, y, width, height) — used by pipeline
                    px_box = (int(x1), int(y1), int(x2-x1), int(y2-y1))

                    conf_label = (
                        "high" if conf >= 0.80
                        else "medium" if conf >= 0.50
                        else "low"
                    )

                    det = VisionDetection(
                        box_percent=pct,
                        box_pixels=px_box,
                        shape="rectangle",
                        confidence=conf_label,
                    )
                    detections.append(det)

            result.primary_latency_ms = int((time.time() - start) * 1000)
            result.primary_response = f"{len(detections)} detections (local YOLOv8)"

            if settings.DETECTION_NMS_ENABLED and detections:
                detections = apply_nms(detections, iou_threshold=self.iou_threshold)

            for i, det in enumerate(detections):
                det.detection_id = f"{inspection_id}_{i+1:03d}"

            result.detections = detections
            result.provider_used = "roboflow_local"
            result.success = True

            logger.info(
                f"RoboflowDetector: {len(detections)} stamps in "
                f"{result.primary_latency_ms}ms"
            )

        except Exception as e:
            result.success = False
            result.primary_error = str(e)
            logger.error(f"Inference failed: {e}")

        if settings.INSPECTION_SAVE_INTERMEDIATES:
            self._save_inspection(image, result, inspection_id)

        return result


    # ── Model management ──────────────────────────────────────────────────────

    def ensure_model_downloaded(self) -> Path:
        """
        Download the Roboflow-trained model weights to disk (one-time).

        Reads ROBOFLOW_API_KEY, ROBOFLOW_WORKSPACE, ROBOFLOW_PROJECT,
        ROBOFLOW_VERSION from settings.
        """
        if self.model_path.exists():
            logger.info(f"Model already cached at {self.model_path}")
            return self.model_path

        settings = get_settings()

        if not settings.ROBOFLOW_API_KEY:
            raise ValueError("ROBOFLOW_API_KEY not set — add it to .env.keys")
        if not settings.ROBOFLOW_WORKSPACE or not settings.ROBOFLOW_PROJECT:
            raise ValueError(
                "ROBOFLOW_WORKSPACE and ROBOFLOW_PROJECT must be set in .env.app"
            )

        ws = settings.ROBOFLOW_WORKSPACE
        proj = settings.ROBOFLOW_PROJECT
        ver = settings.ROBOFLOW_VERSION
        key = settings.ROBOFLOW_API_KEY

        logger.info(f"Downloading Roboflow model {ws}/{proj} v{ver} → {self.model_path}")

        import requests
        url = (
            f"https://api.roboflow.com/{ws}/{proj}/{ver}"
            f"/yolov8/model.pt?api_key={key}"
        )

        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(url, timeout=120, stream=True)

        if response.status_code != 200:
            raise RuntimeError(
                f"Download failed: HTTP {response.status_code} — "
                f"check workspace/project/version in .env.app"
            )

        total = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(self.model_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    print(f"\r  Downloading: {downloaded/total*100:.0f}%",
                          end="", flush=True)

        print()
        logger.info(f"Model saved to {self.model_path}")
        return self.model_path

    def is_model_available(self) -> bool:
        """True if the .pt file exists locally."""
        return self.model_path.exists()

    # ── Private ───────────────────────────────────────────────────────────────

    def _ensure_model_loaded(self) -> None:
        if self._model is not None:
            return
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model not found at {self.model_path}. "
                "Run: detector.ensure_model_downloaded()"
            )
        from ultralytics import YOLO
        logger.debug(f"Loading model from {self.model_path}")
        self._model = YOLO(str(self.model_path))
        logger.info(f"Model loaded: {self.model_path.name}")

    def _save_inspection(
        self,
        image: np.ndarray,
        result: DetectionResult,
        inspection_id: str,
    ) -> None:
        """Save inspection data inside session folder structure."""
        # Create session folder
        session_dir = self.inspection_dir / inspection_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Save annotated detection image
        annotated = image.copy()
        colors = {"high": (0, 255, 0), "medium": (0, 255, 255), "low": (0, 165, 255)}
        for det in result.detections:
            if det.box_pixels is None:
                continue
            x, y, w, h = det.box_pixels
            color = colors.get(det.confidence, (255, 255, 255))
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
            cv2.putText(annotated, det.confidence, (x, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Save in annotated subfolder (matching pipeline structure)
        annotated_dir = session_dir / "annotated"
        annotated_dir.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(annotated_dir / "roboflow_detection.jpg"), annotated)

        # Save result JSON in session folder
        with open(session_dir / "roboflow_result.json", "w") as f:
            json.dump(result.to_dict(), f, indent=2)


def create_roboflow_detector() -> "RoboflowDetector":
    """Factory: create detector and auto-download model if missing."""
    detector = RoboflowDetector()
    if not detector.is_model_available():
        logger.info("Roboflow model not found locally — downloading now...")
        detector.ensure_model_downloaded()
    return detector


if __name__ == "__main__":
    """Test the Roboflow detector with hardcoded input."""
    import logging
    from pathlib import Path
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("=== Roboflow Detector Test ===")
    print("Testing Roboflow-based stamp detection with hardcoded input...")
    
    try:
        # Create detector
        detector = create_roboflow_detector()
        print(f"✓ Detector created with model: {detector.model_path}")
        
        # Create a test image (black rectangle with white circles to simulate stamps)
        import numpy as np
        test_image = np.zeros((600, 800, 3), dtype=np.uint8)
        
        # Add some circular "stamp-like" objects
        cv2.circle(test_image, (200, 150), 50, (255, 255, 255), -1)
        cv2.circle(test_image, (600, 150), 40, (200, 200, 200), -1)
        cv2.circle(test_image, (400, 400), 45, (180, 180, 180), -1)
        
        # Save test image
        test_path = Path("test_roboflow_input.jpg")
        cv2.imwrite(str(test_path), test_image)
        print(f"✓ Created test image: {test_path}")
        
        # Run detection
        print("🔍 Running stamp detection...")
        start_time = time.time()
        
        result = detector.detect(test_image)
        
        end_time = time.time()
        print(f"✓ Detection completed in {end_time - start_time:.2f} seconds")
        
        # Display results
        print(f"\n📊 Detection Results:")
        print(f"   Total detections: {len(result.detections)}")
        print(f"   Processing time: {result.processing_time_ms}ms")
        
        if result.detections:
            print("\n🎯 Detected stamps:")
            for i, det in enumerate(result.detections, 1):
                print(f"   {i}. Confidence: {det.confidence:.2f}")
                print(f"      Box: {det.box_pixels}")
                print(f"      Center: {det.center}")
        else:
            print("   No stamps detected")
        
        # Save inspection results
        inspection_id = f"roboflow_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        detector._save_inspection(test_image, result, inspection_id)
        print(f"\n💾 Inspection saved to: {detector.inspection_dir / inspection_id}")
        
        # Clean up test image
        if test_path.exists():
            test_path.unlink()
            print(f"🧹 Cleaned up test image: {test_path}")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.exception("Roboflow detector test failed")
        import sys
        sys.exit(1)
