"""Roboflow hosted inference detector — no weight download required.

Uses the Roboflow inference API (free tier: 1000 calls/month).
Drop-in replacement for RoboflowDetector: same detect() interface.
"""

import base64
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

logger = logging.getLogger(__name__)


class RoboflowAPIDetector:
    """
    Calls Roboflow's hosted inference API instead of running locally.
    No .pt download needed — works on the free plan.
    """

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.ROBOFLOW_API_KEY
        self.workspace = settings.ROBOFLOW_WORKSPACE
        self.project = settings.ROBOFLOW_PROJECT
        self.version = settings.ROBOFLOW_VERSION
        self.confidence_threshold = settings.ROBOFLOW_CONFIDENCE_THRESHOLD
        self.iou_threshold = settings.DETECTION_NMS_IOU_THRESHOLD
        self.inspection_dir = settings.inspection_path
        self.inspection_dir.mkdir(parents=True, exist_ok=True)
        self._client = None

    def _ensure_client(self):
        if self._client is not None:
            return
        try:
            from inference_sdk import InferenceHTTPClient
            self._client = InferenceHTTPClient(
                api_url="https://detect.roboflow.com",
                api_key=self.api_key,
            )
            logger.info("Roboflow InferenceHTTPClient ready")
        except ImportError:
            raise ImportError(
                "Run: pip install inference-sdk"
            )

    def detect(
        self,
        image: np.ndarray,
        preprocessing_strategy=None,
        inspection_id: Optional[str] = None,
    ) -> DetectionResult:
        settings = get_settings()
        result = DetectionResult(timestamp=datetime.now())

        if inspection_id is None:
            inspection_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        self._ensure_client()

        start = time.time()
        try:
            # Encode image to base64 string for the API
            _, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 90])
            img_base64 = base64.b64encode(buf.tobytes()).decode("utf-8")

            model_id = f"{self.project}/{self.version}"
            logger.info(f"Roboflow API call: model_id={model_id}, workspace={self.workspace}, confidence={self.confidence_threshold}")
            logger.debug(f"Image size: {image.shape}, base64 length: {len(img_base64)}")

            response = self._client.infer(
                img_base64,
                model_id=model_id,
            )

            logger.debug(f"Roboflow raw response: {response}")

            h, w = image.shape[:2]
            detections: list[VisionDetection] = []

            for pred in response.get("predictions", []):
                if pred["confidence"] < self.confidence_threshold:
                    continue

                # Roboflow returns center x/y + width/height in pixels
                cx, cy = pred["x"], pred["y"]
                bw, bh = pred["width"], pred["height"]

                x1, y1 = cx - bw / 2, cy - bh / 2
                x2, y2 = cx + bw / 2, cy + bh / 2

                # Percentage box for NMS
                pct = (x1/w*100, y1/h*100, x2/w*100, y2/h*100)
                px_box = (int(x1), int(y1), int(bw), int(bh))

                conf = pred["confidence"]
                conf_label = "high" if conf >= 0.80 else "medium" if conf >= 0.50 else "low"

                detections.append(VisionDetection(
                    box_percent=pct,
                    box_pixels=px_box,
                    shape="rectangle",
                    confidence=conf_label,
                ))

            result.primary_latency_ms = int((time.time() - start) * 1000)
            result.primary_response = f"{len(detections)} detections (Roboflow API)"

            if settings.DETECTION_NMS_ENABLED and detections:
                detections = apply_nms(detections, iou_threshold=self.iou_threshold)

            for i, det in enumerate(detections):
                det.detection_id = f"{inspection_id}_{i+1:03d}"

            result.detections = detections
            result.provider_used = "roboflow_api"
            result.success = True

            logger.info(f"RoboflowAPIDetector: {len(detections)} stamps in {result.primary_latency_ms}ms")

        except Exception as e:
            result.success = False
            result.primary_error = str(e)
            logger.error(f"Roboflow API inference failed: {e}")

        if settings.INSPECTION_SAVE_INTERMEDIATES:
            self._save_inspection(image, result, inspection_id)

        return result

    def _save_inspection(self, image, result, inspection_id):
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

        # Save in annotated subfolder (matching pipeline structure)
        annotated_dir = session_dir / "annotated"
        annotated_dir.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(annotated_dir / "roboflow_detection.jpg"), annotated)

        # Save result JSON in session folder
        with open(session_dir / "roboflow_result.json", "w") as f:
            json.dump(result.to_dict(), f, indent=2)


if __name__ == "__main__":
    """Test the Roboflow API detector with hardcoded input."""
    import logging
    from pathlib import Path
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("=== Roboflow API Detector Test ===")
    print("Testing Roboflow API-based stamp detection with hardcoded input...")
    
    try:
        # Create detector
        detector = RoboflowAPIDetector()
        print(f"✓ API Detector created")
        print(f"   Workspace: {detector.workspace}")
        print(f"   Project: {detector.project}")
        print(f"   Version: {detector.version}")
        
        # Create test images with various stamp-like sizes (inspired by _check_size thresholds)
        test_cases = [
            {
                "name": "Small Stamp",
                "size": (80, 100),  # Small but valid stamp size
                "position": (150, 200)
            },
            {
                "name": "Ideal Stamp", 
                "size": (150, 180),  # Ideal stamp size from _check_size
                "position": (400, 200)
            },
            {
                "name": "Large Stamp",
                "size": (300, 350),  # Large stamp
                "position": (250, 400)
            }
        ]
        
        # Create test image with multiple stamp-like objects
        import numpy as np
        test_image = np.zeros((600, 800, 3), dtype=np.uint8)
        
        # Add stamp-like rectangles with some texture
        for i, case in enumerate(test_cases):
            x, y = case["position"]
            w, h = case["size"]
            
            # Create rectangle with some texture/gradient
            roi = test_image[y:y+h, x:x+w]
            if roi.size > 0:
                # Add gradient and some noise to simulate stamp content
                gradient = np.linspace(50, 200, w, dtype=np.uint8)
                roi[:, :] = gradient[np.newaxis, :]
                # Add some noise for texture
                noise = np.random.randint(-30, 30, roi.shape, dtype=np.int16)
                roi[:] = np.clip(roi.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # Save test image
        test_path = Path("test_roboflow_api_input.jpg")
        cv2.imwrite(str(test_path), test_image)
        print(f"✓ Created test image: {test_path}")
        print(f"   Image size: {test_image.shape}")
        print(f"   Test cases: {len(test_cases)} stamps")
        
        # Run detection
        print("\n🔍 Running API-based stamp detection...")
        start_time = time.time()
        
        result = detector.detect(test_image)
        
        end_time = time.time()
        print(f"✓ Detection completed in {end_time - start_time:.2f} seconds")
        
        # Display results
        print(f"\n📊 API Detection Results:")
        print(f"   Total detections: {len(result.detections)}")
        print(f"   Processing time: {result.processing_time_ms}ms")
        
        if result.detections:
            print("\n🎯 Detected stamps:")
            for i, det in enumerate(result.detections, 1):
                print(f"   {i}. Confidence: {det.confidence:.2f}")
                print(f"      Box: {det.box_pixels}")
                print(f"      Center: {det.center}")
                print(f"      Class: {det.class_name}")
        else:
            print("   No stamps detected")
        
        # Check if we detected the expected number of stamps
        expected_detections = len(test_cases)
        actual_detections = len(result.detections)
        
        print(f"\n📈 Detection Summary:")
        print(f"   Expected: {expected_detections} stamps")
        print(f"   Detected: {actual_detections} stamps")
        print(f"   Success rate: {(actual_detections/expected_detections)*100:.1f}%")
        
        # Save inspection results
        inspection_id = f"roboflow_api_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        detector._save_inspection(test_image, result, inspection_id)
        print(f"\n💾 Inspection saved to: {detector.inspection_dir / inspection_id}")
        
        # Clean up test image
        if test_path.exists():
            test_path.unlink()
            print(f"🧹 Cleaned up test image: {test_path}")
        
        if actual_detections > 0:
            print("\n✅ API test completed successfully!")
        else:
            print("\n⚠️  API test completed but no stamps detected")
            print("   This could indicate:")
            print("   - API key not configured")
            print("   - Model not trained for stamp detection")
            print("   - Network connectivity issues")
        
    except Exception as e:
        print(f"\n❌ API test failed: {e}")
        logger.exception("Roboflow API detector test failed")
        import sys
        sys.exit(1)
