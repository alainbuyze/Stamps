"""Stage 1A: Classical CV polygon detection using OpenCV."""

import logging
from dataclasses import dataclass
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
    max_vertices: int = 8           # Allow more vertices for stamps with imperfect edges

    # Area constraints (as ratio of image area)
    min_area_ratio: float = 0.0001  # Min 0.01% of image (very permissive, adaptive filtering does the work)
    max_area_ratio: float = 0.50    # Max 50% of image (stamps can be large in close-up photos)

    # Shape constraints
    aspect_ratio_min: float = 0.3   # Not too elongated
    aspect_ratio_max: float = 3.0

    # Polygon approximation
    approx_epsilon: float = 0.04    # Increased for more aggressive simplification

    # Preprocessing
    blur_kernel: tuple = (5, 5)     # Larger blur to reduce noise
    threshold_block_size: int = 11  # Smaller block for finer detail
    threshold_c: int = 3            # Lower constant for better edge detection

    # Convexity
    require_convex: bool = False    # Stamps with perforations may not be convex

    # Use bounding rect fallback when polygon has too many vertices
    use_bounding_rect_fallback: bool = True


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

    def detect(self, image: np.ndarray, debug_dir: str = None) -> list[DetectedPolygon]:
        """
        Detect all stamp-like polygons in the image.

        Args:
            image: BGR image from camera or file
            debug_dir: If provided, save preprocessing debug images to this directory

        Returns:
            List of detected polygons with crops
        """
        logger.debug(f" * detect > Processing image {image.shape}")

        # Preprocessing
        preprocessed = self._preprocess(image, debug_dir=debug_dir)

        # Find contours
        contours = self._find_contours(preprocessed)
        logger.debug(f"    -> Found {len(contours)} contours")

        # Process each contour
        polygons = []
        image_area = image.shape[0] * image.shape[1]
        min_area = image_area * self.config.min_area_ratio
        max_area = image_area * self.config.max_area_ratio

        logger.debug(f"    -> Area filter: {min_area:.0f} - {max_area:.0f} pixels")

        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area > 500:  # Only log significant contours
                logger.debug(f"    -> Contour {i}: area={area:.0f}")
            polygon = self._process_contour(contour, image, image_area)
            if polygon is not None:
                polygons.append(polygon)

        logger.info(f"Detected {len(polygons)} stamp-like polygons")
        return polygons

    def _preprocess(self, image: np.ndarray, debug_dir: str = None) -> np.ndarray:
        """Preprocess image using hybrid approach for different backgrounds.

        Args:
            image: Input BGR image
            debug_dir: If provided, save intermediate steps to this directory
        """
        h, w = image.shape[:2]
        kernel_3 = np.ones((3, 3), np.uint8)
        kernel_5 = np.ones((5, 5), np.uint8)

        def save_debug(name: str, img: np.ndarray):
            """Save debug image if debug_dir is set."""
            if debug_dir:
                import os
                os.makedirs(debug_dir, exist_ok=True)
                path = os.path.join(debug_dir, f"{name}.png")
                cv2.imwrite(path, img)
                logger.debug(f"    Saved debug: {name}.png")

        # === STEP 1: Analyze background ===
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Sample from multiple regions to find the actual background
        # (corners may be binder/border, not the page)
        sample_size = max(20, min(h, w) // 15)

        # Sample from corners
        corners = [
            gray[:sample_size, :sample_size],
            gray[:sample_size, -sample_size:],
            gray[-sample_size:, :sample_size],
            gray[-sample_size:, -sample_size:]
        ]

        # Sample from center region (more likely to be actual page background)
        center_y, center_x = h // 2, w // 2
        center_sample = gray[center_y-sample_size:center_y+sample_size,
                            center_x-sample_size:center_x+sample_size]

        # Sample from edges (middle of each side)
        edge_samples = [
            gray[:sample_size, w//2-sample_size:w//2+sample_size],  # top middle
            gray[-sample_size:, w//2-sample_size:w//2+sample_size],  # bottom middle
            gray[h//2-sample_size:h//2+sample_size, :sample_size],  # left middle
            gray[h//2-sample_size:h//2+sample_size, -sample_size:]   # right middle
        ]

        # Get brightness from all samples
        all_samples = [np.median(c) for c in corners] + \
                      [np.median(center_sample)] + \
                      [np.median(e) for e in edge_samples]

        # Use the MODE (most common) or highest value as background
        # Album pages are usually white/light, so lighter values are more likely background
        # Sort and take the median of the top half (lighter values)
        sorted_samples = sorted(all_samples, reverse=True)
        bg_value = np.median(sorted_samples[:len(sorted_samples)//2 + 1])
        avg_brightness = np.mean(all_samples)
        is_light_background = bg_value > 150  # Based on estimated background, not average

        logger.debug(f"    Background: samples={[int(s) for s in sorted_samples]}, "
                    f"bg_value={bg_value:.0f} ({'light' if is_light_background else 'dark'})")
        save_debug("01_grayscale", gray)

        # === METHOD 1: Saturation-based ===
        # Catches colorful stamps (green, red, blue) on neutral backgrounds
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        saturation = hsv[:, :, 1]
        save_debug("02_saturation_raw", saturation)

        sat_threshold = 20 if is_light_background else 40  # Lower threshold
        sat_mask = (saturation > sat_threshold).astype(np.uint8) * 255
        sat_mask = cv2.morphologyEx(sat_mask, cv2.MORPH_CLOSE, kernel_3, iterations=2)
        sat_mask = cv2.morphologyEx(sat_mask, cv2.MORPH_OPEN, kernel_3, iterations=1)
        save_debug("03_saturation_mask", sat_mask)

        # === METHOD 2: Value/intensity difference ===
        # Catches stamps darker than white background (including gray/low-sat stamps)
        value_diff = np.abs(gray.astype(np.float32) - bg_value)
        value_diff_vis = np.clip(value_diff * 3, 0, 255).astype(np.uint8)
        save_debug("04_value_diff", value_diff_vis)

        # Lower threshold to catch low-contrast stamps
        value_threshold = 12 if is_light_background else 25
        value_mask = (value_diff > value_threshold).astype(np.uint8) * 255
        value_mask = cv2.morphologyEx(value_mask, cv2.MORPH_CLOSE, kernel_3, iterations=2)
        value_mask = cv2.morphologyEx(value_mask, cv2.MORPH_OPEN, kernel_3, iterations=1)
        save_debug("05_value_mask", value_mask)

        # === METHOD 3: Local contrast/texture ===
        # Catches stamps with fine detail (portraits, text) vs uniform background
        blur_small = cv2.GaussianBlur(gray, (3, 3), 0)
        blur_large = cv2.GaussianBlur(gray, (25, 25), 0)
        local_var = np.abs(blur_small.astype(np.float32) - blur_large.astype(np.float32))
        local_var_vis = np.clip(local_var * 5, 0, 255).astype(np.uint8)
        save_debug("06_local_contrast", local_var_vis)

        contrast_threshold = 8
        contrast_mask = (local_var > contrast_threshold).astype(np.uint8) * 255
        contrast_mask = cv2.morphologyEx(contrast_mask, cv2.MORPH_CLOSE, kernel_5, iterations=3)
        contrast_mask = cv2.morphologyEx(contrast_mask, cv2.MORPH_OPEN, kernel_3, iterations=2)
        save_debug("07_contrast_mask", contrast_mask)

        # === METHOD 4: Edge detection ===
        smoothed = cv2.bilateralFilter(image, 9, 75, 75)
        gray_smooth = cv2.cvtColor(smoothed, cv2.COLOR_BGR2GRAY)

        # Multi-scale Canny for robustness
        edges1 = cv2.Canny(gray_smooth, 20, 60)
        edges2 = cv2.Canny(gray_smooth, 40, 120)
        edges = cv2.bitwise_or(edges1, edges2)
        save_debug("08_edges_raw", edges)

        edge_mask = cv2.dilate(edges, kernel_3, iterations=2)
        edge_mask = cv2.morphologyEx(edge_mask, cv2.MORPH_CLOSE, kernel_5, iterations=2)
        save_debug("09_edge_mask", edge_mask)

        # === HYBRID APPROACH: Edge-based + Value-based ===
        # Handles both colorful stamps AND white stamps on white backgrounds

        # --- METHOD A: Edge-based detection (for white stamps with perforations) ---
        # Dilate edges to close gaps in perforation patterns
        edge_dilated = cv2.dilate(edges, kernel_5, iterations=2)
        save_debug("10a_edges_dilated", edge_dilated)

        # Close gaps to form closed rectangular boundaries
        kernel_large = np.ones((15, 15), np.uint8)
        edge_closed = cv2.morphologyEx(edge_dilated, cv2.MORPH_CLOSE, kernel_large, iterations=3)
        save_debug("10b_edges_closed", edge_closed)

        # Find contours and fill them to get solid stamp regions
        contours_edge, _ = cv2.findContours(edge_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        logger.debug(f"    Found {len(contours_edge)} edge contours")

        # Fill significant contours
        binary_edge = np.zeros_like(gray)
        for contour in contours_edge:
            area = cv2.contourArea(contour)
            if area > 1000:  # Only fill significant contours
                cv2.drawContours(binary_edge, [contour], -1, 255, -1)
        save_debug("10c_edge_filled", binary_edge)

        # --- METHOD B: Value-based detection (for colorful stamps) ---
        _, binary_value = cv2.threshold(value_diff_vis, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        save_debug("10d_otsu_value", binary_value)

        # Check polarity for value-based mask
        corner_size = max(10, min(h, w) // 20)
        corners_white = [
            np.mean(binary_value[:corner_size, :corner_size]) > 127,
            np.mean(binary_value[:corner_size, -corner_size:]) > 127,
            np.mean(binary_value[-corner_size:, :corner_size]) > 127,
            np.mean(binary_value[-corner_size:, -corner_size:]) > 127,
        ]
        if sum(corners_white) >= 3:
            binary_value = cv2.bitwise_not(binary_value)
            logger.debug("    Inverted value binary")
            save_debug("10e_value_inverted", binary_value)

        # Clean up value mask
        binary_value = cv2.morphologyEx(binary_value, cv2.MORPH_CLOSE, kernel_5, iterations=2)
        binary_value = cv2.morphologyEx(binary_value, cv2.MORPH_OPEN, kernel_3, iterations=1)
        save_debug("10f_value_cleaned", binary_value)

        # --- COMBINE: Use OR to catch stamps from either method ---
        binary = cv2.bitwise_or(binary_edge, binary_value)
        save_debug("10g_combined", binary)

        # Final cleanup
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_5, iterations=2)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_3, iterations=1)
        save_debug("11_cleaned", binary)

        # Find contours on the thresholded value_diff
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        logger.debug(f"    Found {len(contours)} contours from value_diff")

        # === ADAPTIVE PARAMETER DETECTION ===
        # Analyze all contours to determine stamp-like sizes dynamically

        image_area = h * w
        absolute_min_area = 100  # Absolute minimum (noise)

        # Collect info about all significant contours
        contour_info = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < absolute_min_area:
                continue

            x, y, bw, bh = cv2.boundingRect(contour)
            aspect = bw / bh if bh > 0 else 0

            # Basic aspect ratio filter (stamps are roughly rectangular)
            if aspect < 0.2 or aspect > 5.0:
                continue

            contour_info.append({
                'contour': contour,
                'area': area,
                'bbox': (x, y, bw, bh),
                'aspect': aspect,
                'spans_width': bw > w * 0.9,
                'spans_height': bh > h * 0.9,
            })

        logger.debug(f"    Significant contours: {len(contour_info)}")

        # Debug: log all significant contour areas
        if contour_info:
            all_areas = sorted([c['area'] for c in contour_info], reverse=True)
            logger.debug(f"    Top 10 areas: {all_areas[:10]}")

        if len(contour_info) == 0:
            combined = np.zeros_like(gray)
            save_debug("12_filtered_contours", combined)
            logger.debug("    No valid contours found")
        else:
            # Sort by area
            contour_info.sort(key=lambda x: x['area'], reverse=True)
            areas = [c['area'] for c in contour_info]

            # Detect if largest contour is a page border (much larger than others)
            if len(areas) > 1:
                largest = areas[0]
                second_largest = areas[1]
                spans = contour_info[0]['spans_width'] or contour_info[0]['spans_height']
                logger.debug(f"    Largest: {largest:.0f}, 2nd: {second_largest:.0f}, ratio: {largest/second_largest:.1f}x, spans: {spans}")
                # If largest is >3x the second largest and spans image, it's likely a border
                if largest > second_largest * 3 and spans:
                    logger.debug(f"    Removing page border: area={largest:.0f}")
                    contour_info = contour_info[1:]  # Remove the border
                    areas = areas[1:]
                    # Check again for more borders
                    while len(areas) > 1:
                        if areas[0] > areas[1] * 3 and (contour_info[0]['spans_width'] or contour_info[0]['spans_height']):
                            logger.debug(f"    Removing another border: area={areas[0]:.0f}")
                            contour_info = contour_info[1:]
                            areas = areas[1:]
                        else:
                            break

            # Now analyze remaining contours to find stamp-like sizes
            logger.debug(f"    After border removal: {len(areas)} contours remain")
            if len(areas) > 0:
                median_area = np.median(areas)
                mean_area = np.mean(areas)
                # Stamps are typically within 5x of median size
                min_stamp_area = median_area / 5
                max_stamp_area = median_area * 5

                # But also ensure reasonable bounds
                min_stamp_area = max(min_stamp_area, 200)  # Absolute minimum 200 pixels
                max_stamp_area = min(max_stamp_area, image_area * 0.5)   # At most 50%

                logger.debug(f"    Stats: median={median_area:.0f}, mean={mean_area:.0f}")
                logger.debug(f"    Adaptive range: [{min_stamp_area:.0f}, {max_stamp_area:.0f}]")
            else:
                min_stamp_area = image_area * 0.001
                max_stamp_area = image_area * 0.5
                logger.debug("    No contours after border removal!")

            # Filter contours using adaptive thresholds
            combined = np.zeros_like(gray)
            kept_count = 0

            for info in contour_info:
                area = info['area']
                x, y, bw, bh = info['bbox']
                aspect = info['aspect']

                # Skip if outside adaptive size range
                if area < min_stamp_area or area > max_stamp_area:
                    logger.debug(f"    Skipped: area={area:.0f} outside [{min_stamp_area:.0f}, {max_stamp_area:.0f}]")
                    continue

                # Skip obvious borders (spans full width AND height)
                if info['spans_width'] and info['spans_height']:
                    logger.debug(f"    Skipped: spans full image")
                    continue

                # Tighter aspect ratio for final selection
                if aspect < 0.3 or aspect > 3.5:
                    continue

                cv2.drawContours(combined, [info['contour']], -1, 255, -1)
                kept_count += 1
                logger.debug(f"    Kept: area={area:.0f}, {bw}x{bh}, aspect={aspect:.2f}")

            save_debug("12_filtered_contours", combined)
            logger.debug(f"    Kept {kept_count} stamp contours (adaptive)")

        # === FINAL CLEANUP ===
        result = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel_3, iterations=2)
        save_debug("12_final_result", result)

        logger.debug(f"    Preprocessing: {np.count_nonzero(result)} white pixels")

        return result

    def _find_contours(self, preprocessed: np.ndarray) -> list:
        """Find contours in preprocessed image."""
        h, w = preprocessed.shape[:2]

        # Use RETR_LIST to get ALL contours, not just external
        # This is important when stamps are inside a page border
        contours, _ = cv2.findContours(
            preprocessed,
            cv2.RETR_LIST,  # All contours
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Filter out contours that touch the image edges (likely page borders)
        filtered = []
        edge_margin = 5  # pixels from edge to consider "touching"

        for contour in contours:
            x, y, cw, ch = cv2.boundingRect(contour)

            # Skip contours that touch image edges (page borders, text headers)
            touches_left = x <= edge_margin
            touches_right = (x + cw) >= (w - edge_margin)
            touches_top = y <= edge_margin
            touches_bottom = (y + ch) >= (h - edge_margin)

            # Skip if touches opposite edges (spans full width or height)
            if (touches_left and touches_right) or (touches_top and touches_bottom):
                logger.debug(f"    Skipping border contour: {cw}x{ch}")
                continue

            filtered.append(contour)

        logger.debug(f"    Filtered {len(contours)} -> {len(filtered)} contours (removed borders)")
        return filtered

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
        if area < min_area:
            if area > 500:
                logger.debug(f"       REJECTED: area {area:.0f} < min {min_area:.0f}")
            return None
        if area > max_area:
            logger.debug(f"       REJECTED: area {area:.0f} > max {max_area:.0f}")
            return None

        # Approximate polygon
        epsilon = self.config.approx_epsilon * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # Filter by vertex count
        num_vertices = len(approx)
        logger.debug(f"       Contour: area={area:.0f}, vertices={num_vertices}")

        # Use bounding rect fallback for shapes with too many vertices
        use_bounding_rect = False
        if num_vertices > self.config.max_vertices:
            if self.config.use_bounding_rect_fallback:
                use_bounding_rect = True
                logger.debug(f"       Using bounding rect fallback ({num_vertices} > {self.config.max_vertices} vertices)")
            else:
                logger.debug(f"       REJECTED: vertices {num_vertices} > max {self.config.max_vertices}")
                return None

        if num_vertices < self.config.min_vertices and not use_bounding_rect:
            logger.debug(f"       REJECTED: vertices {num_vertices} < min {self.config.min_vertices}")
            return None

        # Check convexity if required (skip for bounding rect fallback)
        if not use_bounding_rect and self.config.require_convex and not cv2.isContourConvex(approx):
            logger.debug(f"       REJECTED: not convex")
            return None

        # Get bounding box and aspect ratio
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = w / h if h > 0 else 0

        # Filter by aspect ratio
        if aspect_ratio < self.config.aspect_ratio_min or aspect_ratio > self.config.aspect_ratio_max:
            logger.debug(f"       REJECTED: aspect ratio {aspect_ratio:.2f} outside [{self.config.aspect_ratio_min}, {self.config.aspect_ratio_max}]")
            return None

        logger.debug(f"       ACCEPTED: {num_vertices} vertices, aspect={aspect_ratio:.2f}")

        # Classify shape
        if use_bounding_rect:
            shape_type = "rectangle"
            # Convert bounding box to vertices for consistent handling
            approx = np.array([
                [[x, y]],
                [[x + w, y]],
                [[x + w, y + h]],
                [[x, y + h]]
            ], dtype=np.int32)
            num_vertices = 4
        elif num_vertices == 3:
            shape_type = "triangle"
        elif num_vertices == 4:
            shape_type = "quadrilateral"
        else:
            shape_type = f"polygon-{num_vertices}"

        # Extract perspective-corrected crop
        cropped = self._extract_crop(approx, original_image, shape_type)

        # Confidence is slightly lower for bounding rect fallback
        confidence = 0.8 if use_bounding_rect else 1.0

        return DetectedPolygon(
            vertices=approx.reshape(-1, 2),
            bounding_box=(x, y, w, h),
            shape_type=shape_type,
            area=area,
            aspect_ratio=aspect_ratio,
            cropped_image=cropped,
            confidence=confidence
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
        For quadrilaterals/rectangles: applies perspective transform to normalize.
        For other polygons: returns bounding rectangle crop.
        """
        if shape_type == "triangle":
            return self._extract_triangle_crop(vertices, image)
        elif shape_type in ("quadrilateral", "rectangle") or len(vertices.reshape(-1, 2)) == 4:
            return self._extract_quad_crop(vertices, image)
        else:
            # For other polygons, use simple bounding box crop
            return self._extract_bbox_crop(vertices, image)

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

    def _extract_bbox_crop(
        self,
        vertices: np.ndarray,
        image: np.ndarray,
    ) -> np.ndarray:
        """Extract a simple bounding box crop for non-quad polygons."""
        x, y, w, h = cv2.boundingRect(vertices)

        # Add padding
        padding = 5
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(image.shape[1] - x, w + 2 * padding)
        h = min(image.shape[0] - y, h + 2 * padding)

        # Extract crop
        crop = image[y:y+h, x:x+w].copy()
        return crop

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


if __name__ == "__main__":
    import os

    # Setup logging - use DEBUG to see contour filtering details
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    def load_test_image(image_path: str) -> np.ndarray:
        """Load and prepare test image from file."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image file: {image_path}")
        
        print(f"   Loaded image: {image.shape}")
        return image

    def run_detection_test():
        """Run polygon detection test with real image file."""
        print("=" * 60)
        print("POLYGON DETECTOR TEST")
        print("=" * 60)

        # Test image path
        image_path = r"A:\Stamps\s-l1600 (10).webp"
        #r"A:\Stamps\i-completed-my-trans-mississippi-this-month-with-the-last-v0-bfekycfiljgg1.webp" 
        #"A:\Stamps\images (1).jpg"
        #"A:\Stamps\s-l1600 (2).webp"
        #"A:\Stamps\s-l1600 (10).webp"
        
        # Load test image
        print(f"\n1. Loading test image from: {image_path}")
        try:
            test_image = load_test_image(image_path)
        except Exception as e:
            print(f"   ERROR loading image: {e}")
            return

        # Initialize detector with default config (uses new relaxed defaults)
        print("\n2. Initializing PolygonDetector with default config...")
        detector = PolygonDetector()  # Uses default DetectionConfig
        config = detector.config
        print(f"   Config: max_vertices={config.max_vertices}, "
              f"max_area_ratio={config.max_area_ratio}, "
              f"require_convex={config.require_convex}")
        print("   Detector initialized successfully")

        # Run detection with debug output
        print("\n3. Running polygon detection...")
        output_dir = "test_output"
        debug_dir = os.path.join(output_dir, "debug_steps")
        try:
            polygons = detector.detect(test_image, debug_dir=debug_dir)
            print("   Detection completed successfully")
            print(f"   Found {len(polygons)} polygons")
            print(f"   Debug images saved to: {debug_dir}/")
        except Exception as e:
            print(f"   ERROR during detection: {e}")
            import traceback
            traceback.print_exc()
            return

        # Display detailed results
        print("\n4. Detection Results:")
        print("-" * 40)

        if not polygons:
            print("   No polygons detected!")
        else:
            for i, poly in enumerate(polygons):
                print(f"\n   Polygon {i+1}:")
                print(f"     Type: {poly.shape_type}")
                print(f"     Vertices: {len(poly.vertices)}")
                print(f"     Area: {poly.area:.1f} pixels")
                print(f"     Aspect Ratio: {poly.aspect_ratio:.2f}")
                print(f"     Bounding Box: {poly.bounding_box}")
                print(f"     Confidence: {poly.confidence:.2f}")

                # Show vertex coordinates
                vertices_str = ", ".join([f"({x:.0f},{y:.0f})" for x, y in poly.vertices])
                print(f"     Vertices: [{vertices_str}]")

        # Visualize results
        print("\n5. Creating visualization...")
        try:
            visualized = detector.visualize_detections(test_image, polygons)

            # Save visualization
            os.makedirs(output_dir, exist_ok=True)

            # Save original and visualized images
            cv2.imwrite(os.path.join(output_dir, "test_original.png"), test_image)
            cv2.imwrite(os.path.join(output_dir, "test_detected.png"), visualized)

            print(f"   Images saved to '{output_dir}/' directory:")
            print("     - test_original.png: Original test image")
            print("     - test_detected.png: Image with detected polygons")
            print("     - debug_steps/: All preprocessing step images")

            # Save cropped polygons
            for i, poly in enumerate(polygons):
                if poly.cropped_image is not None:
                    crop_path = os.path.join(output_dir, f"crop_{i+1}_{poly.shape_type}.png")
                    cv2.imwrite(crop_path, poly.cropped_image)
                    print(f"     - crop_{i+1}_{poly.shape_type}.png: Cropped polygon {i+1}")

        except Exception as e:
            print(f"   ERROR during visualization: {e}")

        # Performance summary
        print("\n6. Test Summary:")
        print("-" * 40)
        print(f"   Image file: {os.path.basename(image_path)}")
        print(f"   Polygons detected: {len(polygons)}")
        
        if len(polygons) > 0:
            shape_counts = {}
            total_area = 0
            for poly in polygons:
                shape_counts[poly.shape_type] = shape_counts.get(poly.shape_type, 0) + 1
                total_area += poly.area
            
            print("   Shape breakdown:")
            for shape_type, count in shape_counts.items():
                print(f"     - {shape_type}: {count}")
            print(f"   Total polygon area: {total_area:.1f} pixels")
        else:
            print("   No polygons detected in image")

        print("\n" + "=" * 60)
        print("TEST COMPLETED")
        print("=" * 60)

    # Run the test
    run_detection_test()
