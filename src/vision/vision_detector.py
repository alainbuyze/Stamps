"""Vision LLM-based stamp detection.

Uses Groq as primary detector with Claude Haiku fallback.
Supports inspection of all intermediate steps.

Classes access settings directly via get_settings() - no config parameters.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
from pathlib import Path

import cv2
import numpy as np

from src.core.config import get_settings
from .preprocessing import (
    ImagePreprocessor,
    PreprocessingStrategy,
    PreprocessedImage,
    create_preprocessor_from_env,
)

logger = logging.getLogger(__name__)


# Detection prompt optimized for JSON output
DETECTION_PROMPT = """Analyze this stamp album page. Detect each UNIQUE postage stamp.

Rules:
1. Output bounding box as [x_min, y_min, x_max, y_max] in PERCENTAGE (0-100)
2. ONE box per stamp - do NOT create multiple/overlapping boxes for the same stamp
3. Include the full stamp within the box, including any perforations
4. x_min=left, x_max=right, y_min=top, y_max=bottom

Return ONLY a JSON array (no markdown, no explanation):
[
  {"box": [10, 5, 25, 20], "shape": "rectangle", "confidence": "high"},
  {"box": [30, 5, 42, 18], "shape": "rectangle", "confidence": "high"}
]

Shape: "rectangle" (most stamps), "triangle", or "diamond"
Confidence: "high", "medium", or "low"

If no stamps found, return: []"""


# Detection provider constants
GROQ = "groq"
CLAUDE_HAIKU = "claude_haiku"
CLAUDE_SONNET = "claude_sonnet"




@dataclass
class VisionDetection:
    """A single stamp detection from vision LLM."""
    
    # Bounding box (percentage 0-100)
    box_percent: tuple  # (x_min, y_min, x_max, y_max)
    
    # Bounding box (pixels, calculated)
    box_pixels: Optional[tuple] = None  # (x, y, width, height)
    
    shape: str = "rectangle"  # rectangle, triangle, diamond
    confidence: str = "medium"  # high, medium, low
    
    # For inspection
    detection_id: str = ""
    
    def to_dict(self) -> dict:
        return {
            "detection_id": self.detection_id,
            "box_percent": self.box_percent,
            "box_pixels": self.box_pixels,
            "shape": self.shape,
            "confidence": self.confidence,
        }


@dataclass
class DetectionResult:
    """Complete result from detection including inspection data."""
    
    # Core results
    detections: list[VisionDetection] = field(default_factory=list)
    success: bool = False
    
    # Provider info
    provider_used: Optional[str] = None
    fallback_triggered: bool = False
    fallback_reason: Optional[str] = None
    
    # Raw responses (for inspection)
    primary_response: Optional[str] = None
    fallback_response: Optional[str] = None
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.now)
    primary_latency_ms: int = 0
    fallback_latency_ms: int = 0
    
    # Preprocessing info
    preprocessed_image: Optional[PreprocessedImage] = None
    
    # Errors
    primary_error: Optional[str] = None
    fallback_error: Optional[str] = None
    parse_errors: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "detection_count": len(self.detections),
            "detections": [d.to_dict() for d in self.detections],
            "provider_used": self.provider_used if self.provider_used else None,
            "fallback_triggered": self.fallback_triggered,
            "fallback_reason": self.fallback_reason,
            "primary_response": self.primary_response,
            "fallback_response": self.fallback_response,
            "primary_latency_ms": self.primary_latency_ms,
            "fallback_latency_ms": self.fallback_latency_ms,
            "primary_error": self.primary_error,
            "fallback_error": self.fallback_error,
            "parse_errors": self.parse_errors,
            "timestamp": self.timestamp.isoformat(),
        }


def _calculate_iou(box1: tuple, box2: tuple) -> float:
    """
    Calculate Intersection over Union (IoU) for two boxes.

    Boxes are in format (x_min, y_min, x_max, y_max) as percentages.
    """
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2

    # Calculate intersection
    inter_x_min = max(x1_min, x2_min)
    inter_y_min = max(y1_min, y2_min)
    inter_x_max = min(x1_max, x2_max)
    inter_y_max = min(y1_max, y2_max)

    if inter_x_max <= inter_x_min or inter_y_max <= inter_y_min:
        return 0.0

    inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)

    # Calculate union
    box1_area = (x1_max - x1_min) * (y1_max - y1_min)
    box2_area = (x2_max - x2_min) * (y2_max - y2_min)
    union_area = box1_area + box2_area - inter_area

    if union_area <= 0:
        return 0.0

    return inter_area / union_area


def apply_nms(
    detections: list[VisionDetection],
    iou_threshold: float = 0.3,
) -> list[VisionDetection]:
    """
    Apply Non-Maximum Suppression to filter overlapping detections.

    When boxes overlap significantly (IoU > threshold), keep the one with
    higher confidence or larger area.

    Args:
        detections: List of detections to filter
        iou_threshold: IoU threshold above which boxes are considered duplicates

    Returns:
        Filtered list of detections
    """
    if not detections:
        return []

    # Sort by confidence (high > medium > low) and then by area (larger first)
    confidence_order = {"high": 2, "medium": 1, "low": 0}

    def sort_key(det):
        box = det.box_percent
        area = (box[2] - box[0]) * (box[3] - box[1])
        conf = confidence_order.get(det.confidence, 0)
        return (conf, area)

    sorted_dets = sorted(detections, key=sort_key, reverse=True)

    keep = []
    suppressed = set()

    for i, det in enumerate(sorted_dets):
        if i in suppressed:
            continue

        keep.append(det)

        # Suppress all boxes that overlap significantly with this one
        for j in range(i + 1, len(sorted_dets)):
            if j in suppressed:
                continue

            iou = _calculate_iou(det.box_percent, sorted_dets[j].box_percent)
            if iou > iou_threshold:
                suppressed.add(j)
                logger.debug(f"NMS: suppressing detection {j} (IoU={iou:.2f} with {i})")

    logger.info(f"NMS: {len(detections)} -> {len(keep)} detections (removed {len(detections) - len(keep)} duplicates)")
    return keep


class VisionDetector:
    """
    Detect stamps using vision LLM with hybrid provider support.

    Primary: Groq (fast, cheap)
    Fallback: Claude Haiku (reliable)

    Accesses all configuration directly via get_settings().
    """

    def __init__(
        self,
        groq_client: Optional[Any] = None,
        anthropic_client: Optional[Any] = None,
    ):
        self.groq_client = groq_client
        self.anthropic_client = anthropic_client

        # Access settings directly
        settings = get_settings()
        self.inspection_dir = settings.inspection_path
        self.inspection_dir.mkdir(parents=True, exist_ok=True)

        # Create preprocessor from settings
        self.preprocessor = create_preprocessor_from_env()

        logger.debug(f"VisionDetector initialized: primary={settings.DETECTION_PRIMARY_PROVIDER}")
    
    def detect(
        self,
        image: np.ndarray,
        preprocessing_strategy: Optional[PreprocessingStrategy] = None,
        inspection_id: Optional[str] = None,
    ) -> DetectionResult:
        """
        Detect stamps in image using vision LLM.

        Args:
            image: Original BGR image
            preprocessing_strategy: Override default preprocessing
            inspection_id: ID for saving inspection artifacts

        Returns:
            DetectionResult with detections and inspection data
        """
        settings = get_settings()
        result = DetectionResult(timestamp=datetime.now())

        # Generate inspection ID if needed
        if inspection_id is None:
            inspection_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info(f"Starting vision detection, inspection_id={inspection_id}")

        # Preprocess image
        preprocessed = self.preprocessor.preprocess(image, preprocessing_strategy)
        result.preprocessed_image = preprocessed

        # Save preprocessed image for inspection
        if settings.INSPECTION_SAVE_INTERMEDIATES:
            self._save_intermediate(preprocessed.image, inspection_id, "preprocessed")

        # Get base64 encoded image
        b64_image = preprocessed.to_base64_jpeg()

        # Try primary provider
        import time
        start = time.time()

        primary_detections, primary_response, primary_error = self._call_provider(
            settings.DETECTION_PRIMARY_PROVIDER,
            b64_image,
        )

        result.primary_latency_ms = int((time.time() - start) * 1000)
        result.primary_response = primary_response
        result.primary_error = primary_error

        # Check if fallback needed
        need_fallback = False
        fallback_reason = None

        if primary_error and settings.DETECTION_FALLBACK_ON_API_ERROR:
            need_fallback = True
            fallback_reason = f"API error: {primary_error}"
        elif primary_detections is None and settings.DETECTION_FALLBACK_ON_PARSE_ERROR:
            need_fallback = True
            fallback_reason = "Parse error"
        elif primary_detections is not None and len(primary_detections) < settings.DETECTION_MIN_DETECTIONS:
            need_fallback = True
            fallback_reason = f"Only {len(primary_detections)} detections (min: {settings.DETECTION_MIN_DETECTIONS})"

        # Use primary results if good
        if not need_fallback and primary_detections is not None:
            result.detections = primary_detections
            result.provider_used = settings.DETECTION_PRIMARY_PROVIDER
            result.success = True
            logger.info(f"Primary detection success: {len(result.detections)} stamps")

        # Try fallback if needed
        elif need_fallback and settings.DETECTION_ENABLE_FALLBACK and settings.DETECTION_FALLBACK_PROVIDER:
            result.fallback_triggered = True
            result.fallback_reason = fallback_reason
            logger.info(f"Triggering fallback: {fallback_reason}")

            start = time.time()
            fallback_detections, fallback_response, fallback_error = self._call_provider(
                settings.DETECTION_FALLBACK_PROVIDER,
                b64_image,
            )

            result.fallback_latency_ms = int((time.time() - start) * 1000)
            result.fallback_response = fallback_response
            result.fallback_error = fallback_error

            if fallback_detections is not None:
                result.detections = fallback_detections
                result.provider_used = settings.DETECTION_FALLBACK_PROVIDER
                result.success = True
                logger.info(f"Fallback detection success: {len(result.detections)} stamps")
            else:
                # Both failed
                result.success = False
                logger.warning("Both primary and fallback detection failed")
        else:
            # No fallback, use whatever we got
            result.detections = primary_detections or []
            result.provider_used = settings.DETECTION_PRIMARY_PROVIDER
            result.success = len(result.detections) > 0

        # Apply Non-Maximum Suppression to filter duplicate/overlapping detections
        if settings.DETECTION_NMS_ENABLED and result.detections:
            result.detections = apply_nms(
                result.detections,
                iou_threshold=settings.DETECTION_NMS_IOU_THRESHOLD,
            )

        # Convert percentage boxes to pixel coordinates
        self._convert_boxes_to_pixels(result.detections, image.shape)

        # Assign detection IDs
        for i, det in enumerate(result.detections):
            det.detection_id = f"{inspection_id}_{i+1:03d}"

        # Save inspection data
        if settings.INSPECTION_SAVE_INTERMEDIATES:
            self._save_inspection_data(result, image, inspection_id)

        return result
    
    def _call_provider(
        self,
        provider: str,
        b64_image: str,
    ) -> tuple[Optional[list[VisionDetection]], Optional[str], Optional[str]]:
        """
        Call detection provider.
        
        Returns:
            (detections, raw_response, error)
        """
        try:
            if provider == GROQ:
                response = self._call_groq(b64_image)
            elif provider in (CLAUDE_HAIKU, CLAUDE_SONNET):
                response = self._call_claude(b64_image, provider)
            else:
                return None, None, f"Unknown provider: {provider}"
            
            # Parse response
            detections = self._parse_response(response)
            return detections, response, None
            
        except Exception as e:
            logger.error(f"Provider {provider} error: {e}")
            return None, None, str(e)
    
    def _call_groq(self, b64_image: str) -> str:
        """Call Groq vision API."""
        if self.groq_client is None:
            raise ValueError("Groq client not configured")

        settings = get_settings()
        response = self.groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": DETECTION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
                    }
                ]
            }],
            max_tokens=settings.DETECTION_GROQ_MAX_TOKENS,
            temperature=settings.DETECTION_GROQ_TEMPERATURE,
        )

        return response.choices[0].message.content

    def _call_claude(self, b64_image: str, provider: str) -> str:
        """Call Claude vision API."""
        if self.anthropic_client is None:
            raise ValueError("Anthropic client not configured")

        settings = get_settings()
        model = (
            settings.DETECTION_CLAUDE_MODEL_HAIKU
            if provider == CLAUDE_HAIKU
            else settings.DETECTION_CLAUDE_MODEL_SONNET
        )

        response = self.anthropic_client.messages.create(
            model=model,
            max_tokens=settings.DETECTION_CLAUDE_MAX_TOKENS,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64_image,
                        }
                    },
                    {"type": "text", "text": DETECTION_PROMPT}
                ]
            }]
        )

        return response.content[0].text
    
    def _parse_response(self, response: str) -> Optional[list[VisionDetection]]:
        """Parse JSON response into detections."""
        if not response:
            return None
        
        # Extract JSON array from response
        # Handle markdown code blocks
        response = response.strip()
        if response.startswith("```"):
            # Remove markdown
            response = re.sub(r'^```(?:json)?\n?', '', response)
            response = re.sub(r'\n?```$', '', response)
        
        # Find JSON array
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if not json_match:
            logger.warning(f"No JSON array found in response: {response[:100]}")
            return None
        
        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            return None
        
        if not isinstance(data, list):
            logger.warning("Response is not a list")
            return None
        
        detections = []
        for item in data:
            if not isinstance(item, dict) or 'box' not in item:
                continue
            
            box = item['box']
            if not isinstance(box, list) or len(box) != 4:
                continue
            
            detections.append(VisionDetection(
                box_percent=tuple(box),
                shape=item.get('shape', 'rectangle'),
                confidence=item.get('confidence', 'medium'),
            ))
        
        return detections
    
    def _convert_boxes_to_pixels(
        self, 
        detections: list[VisionDetection],
        original_shape: tuple,
    ) -> None:
        """Convert percentage boxes to pixel coordinates."""
        h, w = original_shape[:2]
        
        for det in detections:
            x_min, y_min, x_max, y_max = det.box_percent
            
            # Convert percentages to pixels
            px_x = int(x_min * w / 100)
            px_y = int(y_min * h / 100)
            px_w = int((x_max - x_min) * w / 100)
            px_h = int((y_max - y_min) * h / 100)
            
            det.box_pixels = (px_x, px_y, px_w, px_h)
    
    def _save_intermediate(
        self,
        image: np.ndarray,
        inspection_id: str,
        name: str,
    ) -> Path:
        """Save intermediate image for inspection."""
        path = self.inspection_dir / f"{inspection_id}_{name}.jpg"
        cv2.imwrite(str(path), image)
        return path
    
    def _save_inspection_data(
        self,
        result: DetectionResult,
        original_image: np.ndarray,
        inspection_id: str,
    ) -> None:
        """Save full inspection data."""
        # Save original
        self._save_intermediate(original_image, inspection_id, "original")
        
        # Save annotated image
        annotated = self._annotate_detections(original_image, result.detections)
        self._save_intermediate(annotated, inspection_id, "annotated")
        
        # Save JSON data
        json_path = self.inspection_dir / f"{inspection_id}_result.json"
        with open(json_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        logger.debug(f"Inspection data saved to {self.inspection_dir}")
    
    def _annotate_detections(
        self,
        image: np.ndarray,
        detections: list[VisionDetection],
    ) -> np.ndarray:
        """Draw detection boxes on image."""
        annotated = image.copy()
        
        colors = {
            "high": (0, 255, 0),      # Green
            "medium": (0, 255, 255),  # Yellow
            "low": (0, 165, 255),     # Orange
        }
        
        for det in detections:
            if det.box_pixels is None:
                continue
            
            x, y, w, h = det.box_pixels
            color = colors.get(det.confidence, (255, 255, 255))
            
            # Draw box
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
            
            # Draw label
            label = f"{det.shape} ({det.confidence})"
            cv2.putText(annotated, label, (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return annotated


def create_vision_detector_from_env() -> VisionDetector:
    """Create vision detector with API clients.

    All configuration is accessed directly via get_settings() inside VisionDetector.
    This factory only initializes the API clients.
    """
    settings = get_settings()

    # Initialize API clients
    groq_client = None
    anthropic_client = None

    if settings.GROQ_API_KEY:
        try:
            from groq import Groq
            groq_client = Groq(api_key=settings.GROQ_API_KEY)
            logger.debug("Groq client initialized")
        except ImportError:
            logger.warning("groq package not installed")

    if settings.ANTHROPIC_API_KEY:
        try:
            from anthropic import Anthropic
            anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            logger.debug("Anthropic client initialized")
        except ImportError:
            logger.warning("anthropic package not installed")

    return VisionDetector(
        groq_client=groq_client,
        anthropic_client=anthropic_client,
    )
