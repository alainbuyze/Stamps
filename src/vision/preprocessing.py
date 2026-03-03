"""Image preprocessing strategies for vision LLM detection.

Provides configurable preprocessing to optimize token cost vs detection quality.
Includes test framework to compare strategies.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
import base64
import io

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class PreprocessingStrategy(Enum):
    """Available preprocessing strategies."""
    ORIGINAL = "original"           # No preprocessing (baseline)
    DOWNSCALE = "downscale"         # Resolution reduction only
    COMPRESS = "compress"           # Downscale + JPEG compression
    POSTERIZE = "posterize"         # Color quantization
    HIGH_CONTRAST = "high_contrast" # Enhanced contrast
    EDGE_ENHANCED = "edge_enhanced" # Edges overlaid on simplified
    MINIMAL = "minimal"             # Most aggressive reduction


@dataclass
class PreprocessingConfig:
    """Configuration for preprocessing.

    All values must be provided - no hardcoded defaults.
    Use create_preprocessor_from_env() to create from central config.
    """

    strategy: PreprocessingStrategy

    # Resolution settings
    max_dimension: int

    # JPEG compression
    jpeg_quality: int

    # Posterization
    color_levels: int

    # Contrast enhancement
    clahe_clip_limit: float
    clahe_grid_size: int

    # Edge enhancement
    edge_weight: float


@dataclass
class PreprocessedImage:
    """Result of preprocessing with metadata."""
    
    image: np.ndarray               # Processed image (BGR)
    original_shape: tuple           # (height, width, channels)
    processed_shape: tuple          # After preprocessing
    strategy: PreprocessingStrategy
    config: PreprocessingConfig
    
    # For inspection
    scale_factor: float = 1.0       # Scaling applied
    estimated_tokens: int = 0       # Rough token estimate
    file_size_bytes: int = 0        # Encoded size
    
    def to_base64_jpeg(self, quality: Optional[int] = None) -> str:
        """Encode as base64 JPEG for API calls."""
        q = quality or self.config.jpeg_quality
        _, buffer = cv2.imencode('.jpg', self.image, [cv2.IMWRITE_JPEG_QUALITY, q])
        self.file_size_bytes = len(buffer)
        return base64.b64encode(buffer).decode('utf-8')
    
    def to_base64_png(self) -> str:
        """Encode as base64 PNG (lossless)."""
        _, buffer = cv2.imencode('.png', self.image)
        self.file_size_bytes = len(buffer)
        return base64.b64encode(buffer).decode('utf-8')
    
    def estimate_tokens(self) -> int:
        """Estimate token count for vision API."""
        # Rough estimate based on image dimensions
        # Claude: ~1500 tokens for 1024x1024, scales with pixels
        h, w = self.processed_shape[:2]
        pixels = h * w
        base_pixels = 1024 * 1024
        base_tokens = 1500
        
        self.estimated_tokens = int(base_tokens * (pixels / base_pixels))
        return self.estimated_tokens


class ImagePreprocessor:
    """Preprocess images for vision LLM detection."""
    
    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()
    
    def preprocess(
        self, 
        image: np.ndarray,
        strategy: Optional[PreprocessingStrategy] = None,
    ) -> PreprocessedImage:
        """
        Preprocess image using specified strategy.
        
        Args:
            image: Original BGR image
            strategy: Override default strategy
            
        Returns:
            PreprocessedImage with metadata
        """
        strategy = strategy or self.config.strategy
        original_shape = image.shape
        
        logger.debug(f" * preprocess > Strategy: {strategy.value}, input: {original_shape}")
        
        # Apply strategy
        if strategy == PreprocessingStrategy.ORIGINAL:
            processed = self._original(image)
        elif strategy == PreprocessingStrategy.DOWNSCALE:
            processed = self._downscale(image)
        elif strategy == PreprocessingStrategy.COMPRESS:
            processed = self._compress(image)
        elif strategy == PreprocessingStrategy.POSTERIZE:
            processed = self._posterize(image)
        elif strategy == PreprocessingStrategy.HIGH_CONTRAST:
            processed = self._high_contrast(image)
        elif strategy == PreprocessingStrategy.EDGE_ENHANCED:
            processed = self._edge_enhanced(image)
        elif strategy == PreprocessingStrategy.MINIMAL:
            processed = self._minimal(image)
        else:
            processed = self._compress(image)  # Default
        
        # Calculate scale factor
        scale = processed.shape[0] / original_shape[0]
        
        result = PreprocessedImage(
            image=processed,
            original_shape=original_shape,
            processed_shape=processed.shape,
            strategy=strategy,
            config=self.config,
            scale_factor=scale,
        )
        
        result.estimate_tokens()
        logger.debug(f"    -> Output: {result.processed_shape}, ~{result.estimated_tokens} tokens")
        
        return result
    
    def _original(self, image: np.ndarray) -> np.ndarray:
        """No preprocessing - return as-is."""
        return image.copy()
    
    def _downscale(self, image: np.ndarray) -> np.ndarray:
        """Downscale to max dimension."""
        h, w = image.shape[:2]
        max_dim = self.config.max_dimension
        
        if max(h, w) <= max_dim:
            return image.copy()
        
        scale = max_dim / max(h, w)
        new_size = (int(w * scale), int(h * scale))
        return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
    
    def _compress(self, image: np.ndarray) -> np.ndarray:
        """Downscale + JPEG compression (re-decode for consistent quality)."""
        downscaled = self._downscale(image)
        
        # Encode and decode to apply compression artifacts
        _, buffer = cv2.imencode(
            '.jpg', 
            downscaled, 
            [cv2.IMWRITE_JPEG_QUALITY, self.config.jpeg_quality]
        )
        return cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    
    def _posterize(self, image: np.ndarray) -> np.ndarray:
        """Downscale + color quantization."""
        downscaled = self._downscale(image)
        
        # Reduce color levels
        levels = self.config.color_levels
        factor = 256 // levels
        posterized = (downscaled // factor) * factor
        
        return posterized
    
    def _high_contrast(self, image: np.ndarray) -> np.ndarray:
        """Downscale + CLAHE contrast enhancement."""
        downscaled = self._downscale(image)
        
        # Apply CLAHE to L channel in LAB
        lab = cv2.cvtColor(downscaled, cv2.COLOR_BGR2LAB)
        clahe = cv2.createCLAHE(
            clipLimit=self.config.clahe_clip_limit,
            tileGridSize=(self.config.clahe_grid_size, self.config.clahe_grid_size)
        )
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    def _edge_enhanced(self, image: np.ndarray) -> np.ndarray:
        """Edges overlaid on posterized background."""
        downscaled = self._downscale(image)
        
        # Get edges
        gray = cv2.cvtColor(downscaled, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        # Posterize background
        posterized = self._posterize(image)
        
        # Blend
        weight = self.config.edge_weight
        blended = cv2.addWeighted(posterized, 1 - weight, edges_bgr, weight, 0)
        
        return blended
    
    def _minimal(self, image: np.ndarray) -> np.ndarray:
        """Most aggressive: small, posterized, compressed."""
        # Smaller max dimension
        original_max = self.config.max_dimension
        self.config.max_dimension = 480
        
        # Fewer colors
        original_levels = self.config.color_levels
        self.config.color_levels = 4
        
        result = self._posterize(image)
        
        # Restore config
        self.config.max_dimension = original_max
        self.config.color_levels = original_levels
        
        # Heavy JPEG compression
        _, buffer = cv2.imencode('.jpg', result, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return cv2.imdecode(buffer, cv2.IMREAD_COLOR)


class PreprocessingTester:
    """Test framework for comparing preprocessing strategies."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.preprocessor = ImagePreprocessor()
    
    def generate_all_variants(
        self, 
        image: np.ndarray,
        save_images: bool = True,
    ) -> dict[str, PreprocessedImage]:
        """
        Generate all preprocessing variants for comparison.
        
        Args:
            image: Original image
            save_images: Whether to save variants to disk
            
        Returns:
            Dict mapping strategy name to PreprocessedImage
        """
        variants = {}
        
        for strategy in PreprocessingStrategy:
            result = self.preprocessor.preprocess(image, strategy)
            variants[strategy.value] = result
            
            if save_images:
                # Save as JPEG (what we'd send to API)
                path = self.output_dir / f"variant_{strategy.value}.jpg"
                result.to_base64_jpeg()  # Calculate file size
                cv2.imwrite(str(path), result.image)
        
        return variants
    
    def create_comparison_report(
        self,
        variants: dict[str, PreprocessedImage],
    ) -> dict:
        """
        Create comparison report for variants.
        
        Returns dict with metrics for each strategy.
        """
        report = {}
        
        for name, variant in variants.items():
            variant.to_base64_jpeg()  # Ensure file size calculated
            
            report[name] = {
                "original_resolution": f"{variant.original_shape[1]}x{variant.original_shape[0]}",
                "processed_resolution": f"{variant.processed_shape[1]}x{variant.processed_shape[0]}",
                "scale_factor": round(variant.scale_factor, 3),
                "estimated_tokens": variant.estimated_tokens,
                "file_size_kb": round(variant.file_size_bytes / 1024, 1),
                "strategy": variant.strategy.value,
            }
        
        return report
    
    def create_visual_comparison(
        self,
        variants: dict[str, PreprocessedImage],
        output_path: Optional[Path] = None,
    ) -> np.ndarray:
        """
        Create side-by-side visual comparison of all variants.
        
        Returns combined image.
        """
        # Normalize all to same size for comparison
        target_h, target_w = 300, 400
        
        images = []
        labels = []
        
        for name, variant in variants.items():
            # Resize for display
            display = cv2.resize(variant.image, (target_w, target_h))
            
            # Add label
            label = f"{name}: {variant.file_size_bytes//1024}KB"
            cv2.putText(display, label, (10, 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            images.append(display)
            labels.append(name)
        
        # Arrange in grid (2 rows)
        n = len(images)
        cols = (n + 1) // 2
        rows = 2
        
        # Create canvas
        canvas = np.zeros((rows * target_h, cols * target_w, 3), dtype=np.uint8)
        
        for i, img in enumerate(images):
            row = i // cols
            col = i % cols
            y = row * target_h
            x = col * target_w
            canvas[y:y+target_h, x:x+target_w] = img
        
        if output_path:
            cv2.imwrite(str(output_path), canvas)
        
        return canvas


def create_preprocessor_from_env() -> ImagePreprocessor:
    """Create preprocessor from central configuration."""
    from src.core.config import get_settings

    settings = get_settings()

    try:
        strategy = PreprocessingStrategy(settings.PREPROCESSING_STRATEGY)
    except ValueError:
        strategy = PreprocessingStrategy.COMPRESS

    config = PreprocessingConfig(
        strategy=strategy,
        max_dimension=settings.PREPROCESSING_MAX_DIM,
        jpeg_quality=settings.PREPROCESSING_JPEG_QUALITY,
        color_levels=settings.PREPROCESSING_COLOR_LEVELS,
        clahe_clip_limit=settings.PREPROCESSING_CLAHE_CLIP_LIMIT,
        clahe_grid_size=settings.PREPROCESSING_CLAHE_GRID_SIZE,
        edge_weight=settings.PREPROCESSING_EDGE_WEIGHT,
    )

    return ImagePreprocessor(config)
