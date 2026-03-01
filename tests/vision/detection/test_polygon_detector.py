"""Tests for PolygonDetector (Stage 1A)."""

import pytest
import numpy as np
import cv2
from src.vision.detection import PolygonDetector, DetectionConfig


class TestPolygonDetector:
    """Test cases for polygon detection."""

    @pytest.fixture
    def detector(self):
        """Create default detector."""
        return PolygonDetector()

    @pytest.fixture
    def detector_quads_only(self):
        """Create detector that only accepts quadrilaterals."""
        config = DetectionConfig(min_vertices=4, max_vertices=4)
        return PolygonDetector(config)

    @pytest.fixture
    def sample_image_with_rectangles(self):
        """Create test image with 3 rectangles on white background."""
        img = np.ones((800, 600, 3), dtype=np.uint8) * 255
        # Draw filled rectangles with borders
        cv2.rectangle(img, (50, 50), (150, 200), (100, 150, 200), -1)
        cv2.rectangle(img, (50, 50), (150, 200), (0, 0, 0), 2)

        cv2.rectangle(img, (200, 100), (350, 280), (200, 100, 50), -1)
        cv2.rectangle(img, (200, 100), (350, 280), (0, 0, 0), 2)

        cv2.rectangle(img, (400, 50), (550, 250), (50, 200, 150), -1)
        cv2.rectangle(img, (400, 50), (550, 250), (0, 0, 0), 2)
        return img

    @pytest.fixture
    def sample_image_with_triangle(self):
        """Create test image with a triangle."""
        img = np.ones((400, 400, 3), dtype=np.uint8) * 255
        pts = np.array([[200, 50], [100, 300], [300, 300]], np.int32)
        cv2.fillPoly(img, [pts], (150, 100, 200))
        cv2.polylines(img, [pts], True, (0, 0, 0), 2)
        return img

    @pytest.fixture
    def blank_image(self):
        """Create blank white image."""
        return np.ones((400, 400, 3), dtype=np.uint8) * 255

    # =========================================================================
    # Basic Detection Tests
    # =========================================================================

    def test_detect_rectangles(self, detector, sample_image_with_rectangles):
        """PD-01: Detect quadrilateral stamps."""
        polygons = detector.detect(sample_image_with_rectangles)
        assert len(polygons) >= 2  # At least 2 of 3 should be detected
        for p in polygons:
            assert p.shape_type == "quadrilateral"

    def test_detect_triangle(self, detector, sample_image_with_triangle):
        """PD-02: Detect triangular stamps."""
        polygons = detector.detect(sample_image_with_triangle)
        assert len(polygons) >= 1
        triangle_found = any(p.shape_type == "triangle" for p in polygons)
        assert triangle_found

    def test_empty_image_returns_empty(self, detector, blank_image):
        """PD-06: Empty image returns no detections."""
        polygons = detector.detect(blank_image)
        assert len(polygons) == 0

    # =========================================================================
    # Filtering Tests
    # =========================================================================

    def test_filter_by_vertex_count(self, detector_quads_only, sample_image_with_triangle):
        """PD-07: Config min_vertices=4 excludes triangles."""
        polygons = detector_quads_only.detect(sample_image_with_triangle)
        for p in polygons:
            assert p.shape_type == "quadrilateral"

    def test_filter_small_contours(self, detector):
        """PD-03: Small contours are filtered out."""
        img = np.ones((800, 600, 3), dtype=np.uint8) * 255
        # Add small dots (should be filtered)
        for i in range(10):
            cv2.circle(img, (50 + i * 50, 50), 3, (0, 0, 0), -1)
        # Add normal rectangle (should be detected)
        cv2.rectangle(img, (100, 200), (300, 400), (100, 100, 100), -1)
        cv2.rectangle(img, (100, 200), (300, 400), (0, 0, 0), 2)

        polygons = detector.detect(img)
        # Should detect the rectangle but not the dots
        assert len(polygons) <= 2  # Rectangle only (maybe with some edge cases)

    # =========================================================================
    # Output Tests
    # =========================================================================

    def test_cropped_image_not_none(self, detector, sample_image_with_rectangles):
        """Verify cropped images are generated."""
        polygons = detector.detect(sample_image_with_rectangles)
        assert len(polygons) > 0
        for p in polygons:
            assert p.cropped_image is not None
            assert p.cropped_image.shape[0] > 0
            assert p.cropped_image.shape[1] > 0

    def test_bounding_box_format(self, detector, sample_image_with_rectangles):
        """Verify bounding box is (x, y, w, h) tuple."""
        polygons = detector.detect(sample_image_with_rectangles)
        for p in polygons:
            assert len(p.bounding_box) == 4
            x, y, w, h = p.bounding_box
            assert w > 0
            assert h > 0

    def test_vertices_array(self, detector, sample_image_with_rectangles):
        """Verify vertices is numpy array with correct shape."""
        polygons = detector.detect(sample_image_with_rectangles)
        for p in polygons:
            assert isinstance(p.vertices, np.ndarray)
            # Should be Nx2 array
            assert p.vertices.ndim == 2
            assert p.vertices.shape[1] == 2

    def test_confidence_default(self, detector, sample_image_with_rectangles):
        """Verify default confidence is 1.0."""
        polygons = detector.detect(sample_image_with_rectangles)
        for p in polygons:
            assert p.confidence == 1.0

    # =========================================================================
    # Visualization Tests
    # =========================================================================

    def test_visualize_detections(self, detector, sample_image_with_rectangles):
        """Verify visualization produces valid image."""
        polygons = detector.detect(sample_image_with_rectangles)
        if len(polygons) > 0:
            viz = detector.visualize_detections(sample_image_with_rectangles, polygons)
            assert viz.shape == sample_image_with_rectangles.shape
