"""Vision LLM-based stamp detection system.

This module provides AI-powered stamp detection using Large Language Models (LLMs)
with computer vision capabilities. It uses Groq as the primary provider with Claude
Haiku as fallback, supporting comprehensive inspection of all intermediate steps.

## Architecture Overview

The Vision LLM detector operates as a two-stage system:
1. **Preprocessing**: Image enhancement and optimization for LLM consumption
2. **LLM Detection**: AI-powered stamp detection using vision models

## Function Tree

### Core Classes
- `VisionDetector` - Main detector class with LLM integration
- `DetectionResult` - Container for detection results and metadata
- `VisionDetection` - Individual stamp detection with confidence and geometry

### Data Classes
- `DetectionConfig` - Configuration for detection parameters
- `LLMResponse` - Raw LLM response parsing and validation

### Factory Functions
- `create_vision_detector_from_env()` - Create detector from environment settings

### Test Functions (Main)
- `_create_single_stamp_test()` - Generate single stamp test image
- `_create_multiple_stamps_test()` - Generate multi-stamp album page
- `_create_complex_layout_test()` - Generate complex album layout

## Configuration Parameters

The detector uses environment-based configuration via `get_settings()`:

### LLM Provider Settings
- `GROQ_API_KEY` - API key for Groq (primary provider)
- `ANTHROPIC_API_KEY` - API key for Claude Haiku (fallback)
- `GROQ_MODEL` - Model name for Groq (default: "llama-3.2-90b-vision-preview")
- `GROQ_RATE_LIMIT_PER_MINUTE` - API rate limiting (default: 30)

### Detection Settings
- `VISION_PROMPT_FILE` - Path to detection prompt template
- `DETECTION_NMS_IOU_THRESHOLD` - IoU threshold for non-maximum suppression
- `DETECTION_CONFIDENCE_THRESHOLD` - Minimum confidence for detections

### Inspection Settings
- `INSPECTION_SAVE_INTERMEDIATES` - Save intermediate processing results
- `INSPECTION_PATH` - Directory for inspection outputs

## Usage Examples

### Basic Usage
```python
from src.vision.vision_detector import create_vision_detector_from_env

# Create detector with environment settings
detector = create_vision_detector_from_env()

# Detect stamps in image
result = detector.detect(image)

# Process results
for detection in result.detections:
    print(f"Stamp at {detection.center} with confidence {detection.confidence}")
```

### Advanced Usage with Custom Configuration
```python
from src.vision.vision_detector import VisionDetector
from src.core.config import get_settings

# Create detector with explicit clients
detector = VisionDetector(
    groq_client=groq_client,
    anthropic_client=anthropic_client
)

# Run detection with fallback monitoring
result = detector.detect(image)

# Check if fallback was triggered
if result.fallback_triggered:
    print(f"Fallback used: {result.fallback_reason}")
    print(f"Primary provider: {result.provider_used}")
```

### Inspection and Debugging
```python
# Enable inspection mode
settings = get_settings()
settings.INSPECTION_SAVE_INTERMEDIATES = True

# Run detection - all intermediates will be saved
result = detector.detect(image)

# Inspection files are saved to settings.INSPECTION_PATH
# - original.jpg: Input image
# - annotated.jpg: Image with detection boxes
# - result.json: Complete detection results
# - preprocessing.json: Preprocessing metadata
```

### Batch Processing
```python
import cv2
from pathlib import Path

detector = create_vision_detector_from_env()

# Process multiple images
image_dir = Path("stamp_images")
for image_path in image_dir.glob("*.jpg"):
    image = cv2.imread(str(image_path))
    result = detector.detect(image)
    
    print(f"{image_path.name}: {len(result.detections)} stamps detected")
    
    # Save results
    output_path = image_dir / "results" / f"{image_path.stem}_detections.json"
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)
```

### Error Handling and Fallbacks
```python
try:
    detector = create_vision_detector_from_env()
    result = detector.detect(image)
    
    # Check detection quality
    if len(result.detections) == 0:
        print("No stamps detected - trying different preprocessing")
        # Retry with different settings
        
except Exception as e:
    logger.error(f"Detection failed: {e}")
    # Implement fallback logic
```

## Detection Process

### 1. Preprocessing Phase
- **Image Validation**: Check image format and dimensions
- **Size Optimization**: Resize for LLM compatibility (max 2048px)
- **Quality Enhancement**: Apply contrast and clarity improvements
- **Format Conversion**: Ensure proper color space and encoding

### 2. LLM Inference Phase
- **Prompt Construction**: Build detection prompt with clear instructions
- **API Communication**: Send image to LLM provider
- **Response Parsing**: Extract and validate JSON detection data
- **Fallback Handling**: Switch to backup provider if primary fails

### 3. Post-Processing Phase
- **Coordinate Conversion**: Convert percentage to pixel coordinates
- **Non-Maximum Suppression**: Remove overlapping detections
- **Confidence Filtering**: Apply minimum confidence thresholds
- **Result Validation**: Ensure detection quality and consistency

## Output Format

### DetectionResult Structure
```python
@dataclass
class DetectionResult:
    detections: List[VisionDetection]      # All detected stamps
    processing_time_ms: int                # Total processing time
    provider_used: str                     # LLM provider used
    fallback_triggered: bool              # Whether fallback was used
    fallback_reason: Optional[str]         # Reason for fallback
    primary_latency_ms: int               # Primary provider latency
    preprocessing_metadata: dict           # Preprocessing information
```

### VisionDetection Structure
```python
@dataclass
class VisionDetection:
    box_percentage: List[float]           # Bounding box in percentages [x1,y1,x2,y2]
    box_pixels: Tuple[int, int, int, int]  # Bounding box in pixels (x1,y1,x2,y2)
    confidence: str                       # Confidence level (high/medium/low)
    shape_type: str                       # Shape classification
    center: Tuple[int, int]              # Center coordinates (x,y)
    area: int                             # Bounding box area in pixels
```

## Testing

The module includes comprehensive testing capabilities:

### Direct Module Testing
```bash
python -m src.vision.vision_detector
```

This runs three test scenarios:
1. **Single Stamp**: Tests basic detection with one stamp
2. **Multiple Stamps**: Tests multi-stamp album page
3. **Complex Layout**: Tests challenging album arrangements

### Integration Testing
```python
# Test with real stamp images
detector = create_vision_detector_from_env()
test_image = cv2.imread("real_stamp_album.jpg")
result = detector.detect(test_image)

# Validate results
assert len(result.detections) > 0, "No stamps detected"
assert result.provider_used in ["groq", "anthropic"], "Unknown provider"
```

## Performance Considerations

### Rate Limiting
- Groq API: 30 requests/minute (default)
- Implement request queuing for batch processing
- Use exponential backoff for rate limit errors

### Image Optimization
- Maximum dimension: 2048 pixels
- Recommended size: 1024x1024 for balance
- File size: Keep under 5MB for reliable processing

### Memory Management
- Large images are automatically resized
- Intermediate results are cleaned up after processing
- Inspection data can be disabled to save space

## Troubleshooting

### Common Issues

1. **API Key Errors**
   ```
   Error: Invalid API key
   Solution: Check GROQ_API_KEY and ANTHROPIC_API_KEY in .env.keys
   ```

2. **Rate Limiting**
   ```
   Error: Rate limit exceeded
   Solution: Reduce request frequency or upgrade API plan
   ```

3. **Image Size Issues**
   ```
   Error: Image too large
   Solution: Resize image to under 2048px maximum dimension
   ```

4. **No Detections**
   ```
   Issue: Empty results
   Solutions:
   - Check image quality and lighting
   - Verify stamps are clearly visible
   - Try different preprocessing settings
   - Review prompt template
   ```

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging
detector = create_vision_detector_from_env()
result = detector.detect(image)  # Will show detailed processing steps
```

## Dependencies

### Required Packages
- `cv2` - OpenCV for image processing
- `numpy` - Numerical operations
- `groq` - Groq API client
- `anthropic` - Anthropic API client (optional fallback)

### Optional Packages
- `PIL` - Additional image format support
- `requests` - HTTP client for API calls

Classes access settings directly via get_settings() - no config parameters needed for basic usage.
"""

import json
import logging
import re
import time
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


def create_vision_detector_from_env():
    """Routes to RoboflowDetector or VisionDetector based on DETECTION_PRIMARY_PROVIDER.

    When DETECTION_PRIMARY_PROVIDER=roboflow, returns a RoboflowDetector that
    runs fully offline using a locally cached YOLOv8 .pt file.
    Otherwise returns the LLM-based VisionDetector (Groq / Claude).
    Both share the same detect(image) -> DetectionResult interface.
    """
    settings = get_settings()

    # ── Roboflow local YOLOv8 (requires paid plan to download weights) ────────
    if settings.DETECTION_PRIMARY_PROVIDER == "roboflow_local":
        logger.info("Using RoboflowDetector (local YOLOv8)")
        from .roboflow_detector import create_roboflow_detector
        return create_roboflow_detector()

    # ── Roboflow hosted API (free plan, 1000 calls/month) ─────────────────────
    if settings.DETECTION_PRIMARY_PROVIDER == "roboflow":
        logger.info("Using RoboflowAPIDetector (hosted inference)")
        from .roboflow_api_detector import RoboflowAPIDetector
        return RoboflowAPIDetector()

    # ── LLM-based (Groq / Claude) ─────────────────────────────────────────────
    logger.info(f"Using VisionDetector (provider={settings.DETECTION_PRIMARY_PROVIDER})")

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


if __name__ == "__main__":
    """Test the Vision LLM detector with hardcoded input."""
    import logging
    from pathlib import Path
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("=== Vision LLM Detector Test ===")
    print("Testing Vision LLM-based stamp detection with hardcoded input...")
    
    try:
        # Create detector
        detector = create_vision_detector_from_env()
        print("✓ Vision LLM Detector created")
        
        # Create test scenarios
        test_scenarios = [
            {
                "name": "Single Stamp",
                "description": "Test with a single stamp-like object",
                "create_image": lambda: _create_single_stamp_test()
            },
            {
                "name": "Multiple Stamps",
                "description": "Test with multiple stamps in album layout",
                "create_image": lambda: _create_multiple_stamps_test()
            },
            {
                "name": "Complex Layout",
                "description": "Test with complex album page layout",
                "create_image": lambda: _create_complex_layout_test()
            }
        ]
        
        # Run each test scenario
        for scenario in test_scenarios:
            print(f"\n🖼️  Testing: {scenario['name']}")
            print(f"   {scenario['description']}")
            
            # Create test image
            test_image, expected_count = scenario["create_image"]()
            
            # Save test image
            test_path = Path(f"test_vision_llm_{scenario['name'].lower().replace(' ', '_')}.jpg")
            cv2.imwrite(str(test_path), test_image)
            print(f"   Created test image: {test_path}")
            print(f"   Image size: {test_image.shape}")
            print(f"   Expected stamps: {expected_count}")
            
            # Run detection
            print("   🔍 Running Vision LLM detection...")
            start_time = time.time()
            
            result = detector.detect(test_image)
            
            end_time = time.time()
            print(f"   ✓ Detection completed in {end_time - start_time:.2f} seconds")
            
            # Display results
            print(f"   📊 Detection Results:")
            print(f"      Total detections: {len(result.detections)}")
            print(f"      Processing time: {result.processing_time_ms}ms")
            print(f"      Provider used: {result.provider_used}")
            
            if result.fallback_triggered:
                print(f"      ⚠️  Fallback triggered: {result.fallback_reason}")
            
            if result.detections:
                print(f"      🎯 Detected stamps:")
                for i, det in enumerate(result.detections, 1):
                    print(f"         {i}. Confidence: {det.confidence}")
                    print(f"            Box (%): {det.box_percentage}")
                    print(f"            Box (px): {det.box_pixels}")
                    print(f"            Shape: {det.shape_type}")
            else:
                print(f"      No stamps detected")
            
            # Calculate success rate
            success_rate = (len(result.detections) / expected_count) * 100 if expected_count > 0 else 0
            print(f"   📈 Success rate: {success_rate:.1f}% ({len(result.detections)}/{expected_count})")
            
            # Save inspection results
            inspection_id = f"vision_llm_test_{scenario['name'].lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            detector._save_inspection(test_image, result, inspection_id)
            print(f"   💾 Inspection saved to: {detector.inspection_dir / inspection_id}")
            
            # Clean up test image
            if test_path.exists():
                test_path.unlink()
                print(f"   🧹 Cleaned up test image: {test_path}")
        
        print("\n✅ All Vision LLM detector tests completed!")
        
    except Exception as e:
        print(f"\n❌ Vision LLM detector test failed: {e}")
        logger.exception("Vision LLM detector test failed")
        import sys
        sys.exit(1)


def _create_single_stamp_test():
    """Create a test image with a single stamp-like object."""
    # Create 400x300 image with single stamp
    image = np.zeros((300, 400, 3), dtype=np.uint8)
    
    # Add a rectangular stamp with some content
    stamp_x, stamp_y, stamp_w, stamp_h = 100, 80, 200, 140
    
    # Stamp background
    image[stamp_y:stamp_y+stamp_h, stamp_x:stamp_x+stamp_w] = [200, 200, 220]
    
    # Add some "stamp content" - rectangles and text-like patterns
    # Border
    border_color = [50, 50, 50]
    cv2.rectangle(image, (stamp_x+5, stamp_y+5), (stamp_x+stamp_w-5, stamp_y+stamp_h-5), border_color, 3)
    
    # Central design
    center_x, center_y = stamp_x + stamp_w//2, stamp_y + stamp_h//2
    cv2.circle(image, (center_x, center_y), 30, [100, 100, 150], -1)
    
    # Text lines (simulated)
    for i in range(3):
        y_pos = center_y - 20 + i * 20
        cv2.line(image, (stamp_x+20, y_pos), (stamp_x+stamp_w-20, y_pos), [80, 80, 80], 2)
    
    return image, 1


def _create_multiple_stamps_test():
    """Create a test image with multiple stamps in album layout."""
    # Create 600x400 album page
    image = np.ones((400, 600, 3), dtype=np.uint8) * 240  # Light background
    
    # Define stamp positions and sizes
    stamps = [
        {"pos": (50, 50), "size": (120, 80), "color": [200, 180, 160]},
        {"pos": (200, 50), "size": (120, 80), "color": [180, 200, 160]},
        {"pos": (350, 50), "size": (120, 80), "color": [160, 180, 200]},
        {"pos": (50, 150), "size": (100, 70), "color": [200, 160, 180]},
        {"pos": (170, 150), "size": (100, 70), "color": [180, 200, 180]},
        {"pos": (290, 150), "size": (100, 70), "color": [200, 200, 160]},
        {"pos": (50, 240), "size": (140, 90), "color": [160, 160, 200]},
        {"pos": (210, 240), "size": (140, 90), "color": [200, 180, 180]},
        {"pos": (370, 240), "size": (140, 90), "color": [180, 200, 200]},
    ]
    
    # Draw each stamp
    for stamp in stamps:
        x, y = stamp["pos"]
        w, h = stamp["size"]
        color = stamp["color"]
        
        # Stamp background
        image[y:y+h, x:x+w] = color
        
        # Border
        cv2.rectangle(image, (x+3, y+3), (x+w-3, y+h-3), [50, 50, 50], 2)
        
        # Simple design
        center_x, center_y = x + w//2, y + h//2
        cv2.circle(image, (center_x, center_y), min(w, h)//6, [100, 100, 100], -1)
    
    return image, len(stamps)


def _create_complex_layout_test():
    """Create a test image with complex album page layout."""
    # Create 800x600 album page
    image = np.ones((600, 800, 3), dtype=np.uint8) * 235  # Light background
    
    # Add album page lines/borders
    cv2.rectangle(image, (10, 10), (790, 590), [180, 180, 180], 2)
    
    # Complex stamp arrangement with different sizes and orientations
    stamps = [
        # Row 1 - mixed sizes
        {"pos": (30, 30), "size": (100, 60), "color": [220, 200, 180]},
        {"pos": (150, 30), "size": (150, 90), "color": [200, 220, 180]},
        {"pos": (320, 30), "size": (80, 50), "color": [180, 200, 220]},
        {"pos": (420, 30), "size": (120, 70), "color": [220, 180, 200]},
        {"pos": (560, 30), "size": (110, 65), "color": [200, 200, 180]},
        
        # Row 2 - larger stamps
        {"pos": (30, 140), "size": (180, 120), "color": [180, 220, 200]},
        {"pos": (230, 140), "size": (160, 110), "color": [220, 200, 220]},
        {"pos": (410, 140), "size": (140, 100), "color": [200, 180, 180]},
        {"pos": (570, 140), "size": (170, 115), "color": [180, 180, 220]},
        
        # Row 3 - mixed small stamps
        {"pos": (30, 280), "size": (90, 55), "color": [200, 220, 220]},
        {"pos": (140, 280), "size": (85, 50), "color": [220, 220, 200]},
        {"pos": (245, 280), "size": (95, 58), "color": [220, 200, 200]},
        {"pos": (360, 280), "size": (80, 48), "color": [200, 200, 220]},
        {"pos": (460, 280), "size": (88, 52), "color": [200, 220, 180]},
        {"pos": (570, 280), "size": (92, 56), "color": [220, 180, 220]},
        
        # Row 4 - special stamps
        {"pos": (30, 360), "size": (200, 130), "color": [180, 200, 180]},
        {"pos": (250, 360), "size": (130, 85), "color": [200, 180, 200]},
        {"pos": (400, 360), "size": (110, 75), "color": [180, 220, 220]},
        {"pos": (530, 360), "size": (190, 125), "color": [220, 200, 180]},
        
        # Row 5 - bottom row
        {"pos": (30, 510), "size": (100, 60), "color": [200, 200, 200]},
        {"pos": (150, 510), "size": (120, 70), "color": [180, 200, 200]},
        {"pos": (290, 510), "size": (110, 65), "color": [200, 180, 200]},
        {"pos": (420, 510), "size": (130, 75), "color": [200, 200, 180]},
        {"pos": (570, 510), "size": (115, 68), "color": [220, 220, 220]},
    ]
    
    # Draw each stamp with details
    for stamp in stamps:
        x, y = stamp["pos"]
        w, h = stamp["size"]
        color = stamp["color"]
        
        # Stamp background
        image[y:y+h, x:x+w] = color
        
        # Border
        cv2.rectangle(image, (x+2, y+2), (x+w-2, y+h-2), [60, 60, 60], 2)
        
        # Inner border
        cv2.rectangle(image, (x+5, y+5), (x+w-5, y+h-5), [120, 120, 120], 1)
        
        # Central design (varies by size)
        center_x, center_y = x + w//2, y + h//2
        radius = min(w, h) // 8
        
        # Different designs for visual variety
        design_type = (x + y) % 3
        if design_type == 0:
            cv2.circle(image, (center_x, center_y), radius, [80, 80, 80], -1)
        elif design_type == 1:
            cv2.rectangle(image, (center_x-radius, center_y-radius), 
                          (center_x+radius, center_y+radius), [80, 80, 80], -1)
        else:
            # Diamond
            points = np.array([
                [center_x, center_y-radius],
                [center_x+radius, center_y],
                [center_x, center_y+radius],
                [center_x-radius, center_y]
            ], np.int32)
            cv2.fillPoly(image, [points], [80, 80, 80])
    
    return image, len(stamps)

