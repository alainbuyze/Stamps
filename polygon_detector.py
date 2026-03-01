"""Stage 1A: Classical CV polygon detection using OpenCV."""

import logging
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DetectionConfig:
    """Configuration for polygon detection."""
    
    # Detection mode
    mode: str = "album"  # album | loose | mixed
    
    # Polygon filtering
    min_vertices: int = 3           # Include triangles
    max_vertices: int = 4           # Up to quadrilaterals
    
    # Area constraints (as ratio of image area)
    min_area_ratio: float = 0.001   # Min 0.1% of image
    max_area_ratio: float = 0.15    # Max 15% of image
    
    # Shape constraints
    aspect_ratio_min: float = 0.3   # Not too elongated
    aspect_ratio_max: float = 3.0
    
    # Polygon approximation
    approx_epsilon: float = 0.02    # Approximation precision
    
    # Preprocessing
    blur_kernel: tuple = (3, 3)
    threshold_block_size: int = 15
    threshold_c: int = 5
    
    # Convexity
    require_convex: bool = True


@dataclass
class DetectedPolygon:
    """A polygon detected by Stage 1A."""
    
    vertices: np.ndarray            # Original polygon vertices
    bounding_box: tuple             # (x, y, w, h)
    shape_type: str                 # "triangle" | "quadrilateral"
    area: float                     # Polygon area in pixels
    aspect_ratio: float             # Width / height
    cropped_image: Optional[np.ndarray] = None  # Perspective-corrected crop
    confidence: float = 1.0         # Detection confidence


class PolygonDetector:
    """
    Stage 1A: Detect stamp-like polygons using classical computer vision.
    
    Optimized for album pages with controlled backgrounds.
    Detects triangles (3 vertices) and quadrilaterals (4 vertices).
    """
    
    def __init__(self, config: Optional[DetectionConfig] = None):
        self.config = config or DetectionConfig()
        logger.debug(f"PolygonDetector initialized with mode={self.config.mode}")
    
    def detect(self, image: np.ndarray) -> list[DetectedPolygon]:
        """
        Detect all stamp-like polygons in the image.
        
        Args:
            image: BGR image from camera or file
            
        Returns:
            List of detected polygons with crops
        """
        logger.debug(f" * detect > Processing image {image.shape}")
        
        # Preprocessing
        preprocessed = self._preprocess(image)
        
        # Find contours
        contours = self._find_contours(preprocessed)
        logger.debug(f"    -> Found {len(contours)} contours")
        
        # Process each contour
        polygons = []
        image_area = image.shape[0] * image.shape[1]
        
        for contour in contours:
            polygon = self._process_contour(contour, image, image_area)
            if polygon is not None:
                polygons.append(polygon)
        
        logger.info(f"Detected {len(polygons)} stamp-like polygons")
        return polygons
    
    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for contour detection."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, self.config.blur_kernel, 0)
        
        # Adaptive thresholding (handles lighting variations)
        thresh = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            self.config.threshold_block_size,
            self.config.threshold_c
        )
        
        # Morphological operations to clean up
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        return thresh
    
    def _find_contours(self, preprocessed: np.ndarray) -> list:
        """Find contours in preprocessed image."""
        contours, _ = cv2.findContours(
            preprocessed,
            cv2.RETR_EXTERNAL,  # Only external contours
            cv2.CHAIN_APPROX_SIMPLE
        )
        return contours
    
    def _process_contour(
        self, 
        contour: np.ndarray, 
        original_image: np.ndarray,
        image_area: float,
    ) -> Optional[DetectedPolygon]:
        """Process a single contour into a detected polygon."""
        
        # Calculate contour area
        area = cv2.contourArea(contour)
        
        # Filter by area
        min_area = image_area * self.config.min_area_ratio
        max_area = image_area * self.config.max_area_ratio
        if area < min_area or area > max_area:
            return None
        
        # Approximate polygon
        epsilon = self.config.approx_epsilon * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Filter by vertex count
        num_vertices = len(approx)
        if num_vertices < self.config.min_vertices or num_vertices > self.config.max_vertices:
            return None
        
        # Check convexity if required
        if self.config.require_convex and not cv2.isContourConvex(approx):
            return None
        
        # Get bounding box and aspect ratio
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = w / h if h > 0 else 0
        
        # Filter by aspect ratio
        if aspect_ratio < self.config.aspect_ratio_min or aspect_ratio > self.config.aspect_ratio_max:
            return None
        
        # Classify shape
        shape_type = "triangle" if num_vertices == 3 else "quadrilateral"
        
        # Extract perspective-corrected crop
        cropped = self._extract_crop(approx, original_image, shape_type)
        
        return DetectedPolygon(
            vertices=approx.reshape(-1, 2),
            bounding_box=(x, y, w, h),
            shape_type=shape_type,
            area=area,
            aspect_ratio=aspect_ratio,
            cropped_image=cropped,
            confidence=1.0
        )
    
    def _extract_crop(
        self, 
        vertices: np.ndarray, 
        image: np.ndarray,
        shape_type: str,
    ) -> np.ndarray:
        """
        Extract a perspective-corrected crop of the polygon.
        
        For triangles: returns bounding rectangle with white padding.
        For quadrilaterals: applies perspective transform to normalize.
        """
        if shape_type == "triangle":
            return self._extract_triangle_crop(vertices, image)
        else:
            return self._extract_quad_crop(vertices, image)
    
    def _extract_triangle_crop(
        self, 
        vertices: np.ndarray, 
        image: np.ndarray,
    ) -> np.ndarray:
        """Extract triangle with bounding box and white background."""
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(vertices)
        
        # Add padding
        padding = 5
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(image.shape[1] - x, w + 2 * padding)
        h = min(image.shape[0] - y, h + 2 * padding)
        
        # Create white background
        crop = np.ones((h, w, 3), dtype=np.uint8) * 255
        
        # Create mask for triangle
        mask = np.zeros((h, w), dtype=np.uint8)
        shifted_vertices = vertices.reshape(-1, 2) - np.array([x, y])
        cv2.fillPoly(mask, [shifted_vertices.astype(np.int32)], 255)
        
        # Copy triangle region
        roi = image[y:y+h, x:x+w]
        crop[mask > 0] = roi[mask > 0]
        
        return crop
    
    def _extract_quad_crop(
        self, 
        vertices: np.ndarray, 
        image: np.ndarray,
    ) -> np.ndarray:
        """Extract quadrilateral with perspective correction."""
        pts = vertices.reshape(4, 2).astype(np.float32)
        
        # Order points: top-left, top-right, bottom-right, bottom-left
        pts = self._order_points(pts)
        
        # Calculate output dimensions
        width_top = np.linalg.norm(pts[0] - pts[1])
        width_bottom = np.linalg.norm(pts[2] - pts[3])
        width = int(max(width_top, width_bottom))
        
        height_left = np.linalg.norm(pts[0] - pts[3])
        height_right = np.linalg.norm(pts[1] - pts[2])
        height = int(max(height_left, height_right))
        
        # Ensure minimum size
        width = max(width, 50)
        height = max(height, 50)
        
        # Destination points
        dst = np.array([
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1]
        ], dtype=np.float32)
        
        # Perspective transform
        matrix = cv2.getPerspectiveTransform(pts, dst)
        crop = cv2.warpPerspective(image, matrix, (width, height))
        
        return crop
    
    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """Order points: top-left, top-right, bottom-right, bottom-left."""
        # Sort by y-coordinate
        sorted_by_y = pts[np.argsort(pts[:, 1])]
        
        # Top two points
        top = sorted_by_y[:2]
        top = top[np.argsort(top[:, 0])]  # Sort by x
        
        # Bottom two points
        bottom = sorted_by_y[2:]
        bottom = bottom[np.argsort(bottom[:, 0])[::-1]]  # Sort by x, reversed
        
        return np.array([top[0], top[1], bottom[0], bottom[1]], dtype=np.float32)
    
    def visualize_detections(
        self, 
        image: np.ndarray, 
        polygons: list[DetectedPolygon],
    ) -> np.ndarray:
        """Draw detected polygons on image for debugging."""
        output = image.copy()
        
        for i, poly in enumerate(polygons):
            # Draw polygon
            pts = poly.vertices.reshape((-1, 1, 2)).astype(np.int32)
            color = (0, 255, 0) if poly.shape_type == "quadrilateral" else (255, 0, 0)
            cv2.polylines(output, [pts], True, color, 2)
            
            # Draw label
            x, y, w, h = poly.bounding_box
            label = f"{i+1}: {poly.shape_type[:4]}"
            cv2.putText(output, label, (x, y - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return output
