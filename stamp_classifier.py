"""Stage 1B: Stamp classifier using heuristics (and optional trained model)."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ClassifierConfig:
    """Configuration for stamp classifier."""
    
    # Mode
    mode: str = "heuristic"  # heuristic | model | both
    
    # Confidence threshold
    confidence_threshold: float = 0.6
    
    # Heuristic weights (must sum to 1.0)
    color_variance_weight: float = 0.35
    edge_complexity_weight: float = 0.30
    size_weight: float = 0.20
    perforation_weight: float = 0.15
    
    # Color variance thresholds
    min_color_variance: float = 500.0   # Reject very uniform areas
    
    # Edge complexity thresholds
    min_edge_density: float = 0.05      # Min edges as ratio of pixels
    
    # Size thresholds (in pixels for typical stamp at 300 DPI)
    min_stamp_width: int = 50
    max_stamp_width: int = 500
    min_stamp_height: int = 50
    max_stamp_height: int = 500
    
    # Perforation detection
    perforation_edge_band: int = 5      # Pixels from edge to analyze
    perforation_variance_high: float = 1000.0
    perforation_variance_low: float = 200.0
    
    # Model path (optional)
    model_path: Optional[str] = None


@dataclass
class StampClassification:
    """Result from stamp classifier."""
    
    is_stamp: bool              # Classifier verdict
    confidence: float           # 0-1 confidence
    reason: str                 # Primary reason for verdict
    details: dict               # Individual check scores


class StampClassifier:
    """
    Stage 1B: Determine if a detected polygon is actually a postage stamp.
    
    Uses weighted heuristic checks:
    - Color variance (stamps are colorful, not blank)
    - Edge complexity (stamps have detailed content)
    - Size plausibility (reasonable stamp dimensions)
    - Perforation hint (characteristic wavy edges)
    
    Can optionally use a trained lightweight classifier.
    """
    
    def __init__(self, config: Optional[ClassifierConfig] = None):
        self.config = config or ClassifierConfig()
        self.model = None
        
        # Load model if specified
        if self.config.mode in ("model", "both") and self.config.model_path:
            self._load_model()
        
        logger.debug(f"StampClassifier initialized with mode={self.config.mode}")
    
    def _load_model(self) -> None:
        """Load trained classifier model."""
        model_path = Path(self.config.model_path)
        if not model_path.exists():
            logger.warning(f"Model not found at {model_path}, using heuristics only")
            self.config.mode = "heuristic"
            return
        
        try:
            # TODO: Load ONNX or other model format
            # self.model = cv2.dnn.readNetFromONNX(str(model_path))
            logger.info(f"Model loaded from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.config.mode = "heuristic"
    
    def classify(self, crop: np.ndarray) -> StampClassification:
        """
        Classify if the cropped image is a postage stamp.
        
        Args:
            crop: Cropped image (perspective-corrected)
            
        Returns:
            StampClassification with verdict and details
        """
        if self.config.mode == "model" and self.model is not None:
            return self._model_predict(crop)
        elif self.config.mode == "both" and self.model is not None:
            heuristic = self._heuristic_check(crop)
            model = self._model_predict(crop)
            # Combine results (average confidence)
            combined_conf = (heuristic.confidence + model.confidence) / 2
            return StampClassification(
                is_stamp=combined_conf >= self.config.confidence_threshold,
                confidence=combined_conf,
                reason=f"combined({heuristic.reason}, {model.reason})",
                details={
                    "heuristic": heuristic.details,
                    "model": model.details,
                }
            )
        else:
            return self._heuristic_check(crop)
    
    def _heuristic_check(self, crop: np.ndarray) -> StampClassification:
        """
        Check if image is stamp-like using heuristics.
        
        Returns weighted average of individual checks.
        """
        scores = {}
        
        # Color variance check
        scores["color_variance"] = self._check_color_variance(crop)
        
        # Edge complexity check
        scores["edge_complexity"] = self._check_edge_complexity(crop)
        
        # Size plausibility check
        scores["size_plausibility"] = self._check_size(crop)
        
        # Perforation hint check
        scores["perforation_hint"] = self._check_perforation_hint(crop)
        
        # Calculate weighted confidence
        confidence = (
            scores["color_variance"] * self.config.color_variance_weight +
            scores["edge_complexity"] * self.config.edge_complexity_weight +
            scores["size_plausibility"] * self.config.size_weight +
            scores["perforation_hint"] * self.config.perforation_weight
        )
        
        is_stamp = confidence >= self.config.confidence_threshold
        
        # Determine primary reason
        if is_stamp:
            reason = max(scores, key=scores.get)
        else:
            reason = min(scores, key=scores.get)
        
        return StampClassification(
            is_stamp=is_stamp,
            confidence=confidence,
            reason=reason,
            details=scores
        )
    
    def _check_color_variance(self, crop: np.ndarray) -> float:
        """
        Check color variance - stamps are colorful, not blank.
        
        Returns:
            Score 0-1 where 1 = highly colorful
        """
        # Convert to LAB for better color analysis
        try:
            lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB)
        except Exception:
            return 0.5  # Neutral if conversion fails
        
        # Calculate variance of each channel
        l_var = np.var(lab[:, :, 0])
        a_var = np.var(lab[:, :, 1])
        b_var = np.var(lab[:, :, 2])
        
        # Combined variance
        total_variance = l_var + a_var + b_var
        
        # Reject very low variance (blank areas)
        if total_variance < self.config.min_color_variance:
            return 0.1
        
        # Normalize to 0-1 (cap at high variance)
        max_expected_variance = 10000.0
        score = min(total_variance / max_expected_variance, 1.0)
        
        return score
    
    def _check_edge_complexity(self, crop: np.ndarray) -> float:
        """
        Check edge complexity - stamps have detailed content.
        
        Returns:
            Score 0-1 where 1 = highly complex edges
        """
        # Convert to grayscale
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        
        # Detect edges
        edges = cv2.Canny(gray, 50, 150)
        
        # Calculate edge density
        total_pixels = edges.shape[0] * edges.shape[1]
        edge_pixels = np.count_nonzero(edges)
        edge_density = edge_pixels / total_pixels
        
        # Check minimum edge density
        if edge_density < self.config.min_edge_density:
            return 0.2
        
        # Normalize (typical stamps have 5-25% edge density)
        score = min(edge_density / 0.25, 1.0)
        
        return score
    
    def _check_size(self, crop: np.ndarray) -> float:
        """
        Check size plausibility - stamps have reasonable dimensions.
        
        Returns:
            Score 0-1 where 1 = perfect stamp size
        """
        h, w = crop.shape[:2]
        
        # Check width
        if w < self.config.min_stamp_width or w > self.config.max_stamp_width:
            width_score = 0.3
        else:
            # Prefer sizes in typical stamp range
            ideal_width = 150  # pixels
            width_score = 1.0 - min(abs(w - ideal_width) / ideal_width, 0.7)
        
        # Check height
        if h < self.config.min_stamp_height or h > self.config.max_stamp_height:
            height_score = 0.3
        else:
            ideal_height = 180  # pixels
            height_score = 1.0 - min(abs(h - ideal_height) / ideal_height, 0.7)
        
        return (width_score + height_score) / 2
    
    def _check_perforation_hint(self, crop: np.ndarray) -> float:
        """
        Look for perforation-like patterns on edges.
        
        Perforations create characteristic wavy/notched edges.
        This is a soft signal - many modern stamps are self-adhesive.
        
        Returns:
            Score 0-1 where:
            - 1.0 = strong perforation pattern
            - 0.5 = neutral (no clear signal)
            - 0.3 = very smooth edges (less likely perforated)
        """
        try:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        except Exception:
            return 0.5
        
        h, w = gray.shape
        band = self.config.perforation_edge_band
        
        # Analyze edge bands
        edges = cv2.Canny(gray, 50, 150)
        
        # Sample edges from all four sides
        edge_variances = []
        
        # Top edge
        if h > band:
            top_band = edges[:band, :]
            edge_variances.append(np.var(top_band.astype(float)))
        
        # Bottom edge
        if h > band:
            bottom_band = edges[-band:, :]
            edge_variances.append(np.var(bottom_band.astype(float)))
        
        # Left edge
        if w > band:
            left_band = edges[:, :band]
            edge_variances.append(np.var(left_band.astype(float)))
        
        # Right edge
        if w > band:
            right_band = edges[:, -band:]
            edge_variances.append(np.var(right_band.astype(float)))
        
        if not edge_variances:
            return 0.5
        
        avg_variance = np.mean(edge_variances)
        
        # High variance = likely perforations
        if avg_variance > self.config.perforation_variance_high:
            return 1.0
        # Very low variance = smooth edges
        elif avg_variance < self.config.perforation_variance_low:
            return 0.3
        # Neutral
        else:
            return 0.5
    
    def _model_predict(self, crop: np.ndarray) -> StampClassification:
        """
        Use trained model for prediction.
        
        TODO: Implement when model is available.
        """
        if self.model is None:
            return StampClassification(
                is_stamp=True,
                confidence=0.5,
                reason="model_unavailable",
                details={"error": "Model not loaded"}
            )
        
        # TODO: Actual model inference
        # - Resize crop to model input size
        # - Normalize
        # - Run inference
        # - Return classification
        
        return StampClassification(
            is_stamp=True,
            confidence=0.5,
            reason="model_placeholder",
            details={"warning": "Model inference not implemented"}
        )
