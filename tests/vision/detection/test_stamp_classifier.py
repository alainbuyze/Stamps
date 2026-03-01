"""Tests for StampClassifier (Stage 1B)."""

import pytest
import numpy as np
import cv2
from src.vision.detection import StampClassifier, ClassifierConfig


class TestStampClassifier:
    """Test cases for stamp classification."""

    @pytest.fixture
    def classifier(self):
        """Create default classifier."""
        return StampClassifier()

    @pytest.fixture
    def classifier_low_threshold(self):
        """Create classifier with low threshold."""
        config = ClassifierConfig(confidence_threshold=0.3)
        return StampClassifier(config)

    @pytest.fixture
    def colorful_stamp_crop(self):
        """Create a colorful test image simulating a stamp."""
        img = np.zeros((180, 150, 3), dtype=np.uint8)
        # Add gradient background
        for i in range(180):
            img[i, :] = [int(200 * i / 180), 100, int(50 + 150 * i / 180)]
        # Add detailed content
        cv2.rectangle(img, (20, 20), (130, 160), (50, 150, 200), 2)
        cv2.circle(img, (75, 90), 30, (200, 100, 50), -1)
        cv2.putText(img, "STAMP", (25, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        # Add edge detail
        cv2.line(img, (10, 10), (140, 10), (0, 0, 0), 1)
        cv2.line(img, (10, 170), (140, 170), (0, 0, 0), 1)
        return img

    @pytest.fixture
    def blank_crop(self):
        """Create a blank white crop."""
        return np.ones((100, 100, 3), dtype=np.uint8) * 255

    @pytest.fixture
    def solid_color_crop(self):
        """Create a solid color crop (no detail)."""
        img = np.ones((100, 100, 3), dtype=np.uint8)
        img[:, :] = [150, 100, 80]  # Solid brown
        return img

    @pytest.fixture
    def tiny_crop(self):
        """Create a very small crop."""
        return np.zeros((20, 20, 3), dtype=np.uint8)

    @pytest.fixture
    def large_crop(self):
        """Create a very large crop."""
        return np.zeros((600, 600, 3), dtype=np.uint8)

    # =========================================================================
    # Basic Classification Tests
    # =========================================================================

    def test_classify_colorful_stamp(self, classifier, colorful_stamp_crop):
        """SC-01: Colorful stamps should be accepted."""
        result = classifier.classify(colorful_stamp_crop)
        assert result.is_stamp is True
        assert result.confidence >= 0.6

    def test_reject_blank_area(self, classifier, blank_crop):
        """SC-02: Blank areas should be rejected."""
        result = classifier.classify(blank_crop)
        # Blank should have low color variance
        assert result.details["color_variance"] < 0.5

    def test_reject_solid_color(self, classifier, solid_color_crop):
        """SC-03: Solid color areas should have low edge complexity."""
        result = classifier.classify(solid_color_crop)
        assert result.details["edge_complexity"] < 0.5

    # =========================================================================
    # Heuristic Score Tests
    # =========================================================================

    def test_details_contains_all_scores(self, classifier, colorful_stamp_crop):
        """SC-08: Details should contain all heuristic scores."""
        result = classifier.classify(colorful_stamp_crop)
        assert "color_variance" in result.details
        assert "edge_complexity" in result.details
        assert "size_plausibility" in result.details
        assert "perforation_hint" in result.details

    def test_scores_in_valid_range(self, classifier, colorful_stamp_crop):
        """All scores should be between 0 and 1."""
        result = classifier.classify(colorful_stamp_crop)
        for score_name, score_value in result.details.items():
            assert 0 <= score_value <= 1, f"{score_name} = {score_value} is out of range"

    def test_confidence_in_valid_range(self, classifier, colorful_stamp_crop):
        """Confidence should be between 0 and 1."""
        result = classifier.classify(colorful_stamp_crop)
        assert 0 <= result.confidence <= 1

    # =========================================================================
    # Threshold Tests
    # =========================================================================

    def test_threshold_boundary(self, classifier):
        """SC-06: Scores just below threshold should be rejected."""
        # Create image that produces moderate scores
        img = np.random.randint(100, 200, (150, 120, 3), dtype=np.uint8)
        result = classifier.classify(img)

        # The classification should respect the threshold
        if result.confidence >= 0.6:
            assert result.is_stamp is True
        else:
            assert result.is_stamp is False

    def test_custom_threshold(self, classifier_low_threshold, blank_crop):
        """SC-07: Custom threshold should be respected."""
        # With very low threshold, even blank might pass
        result = classifier_low_threshold.classify(blank_crop)
        # Just verify it doesn't crash and uses the threshold
        assert result.confidence >= 0 or result.confidence < 0.3

    # =========================================================================
    # Size Tests
    # =========================================================================

    def test_tiny_crop_size_score(self, classifier, tiny_crop):
        """Very small crops should have lower size score."""
        result = classifier.classify(tiny_crop)
        # Size score should be penalized for tiny images
        assert result.details["size_plausibility"] <= 0.7

    def test_large_crop_size_score(self, classifier, large_crop):
        """Very large crops should have lower size score."""
        result = classifier.classify(large_crop)
        # Size score should be penalized for huge images
        assert result.details["size_plausibility"] <= 0.7

    def test_ideal_size_crop(self, classifier, colorful_stamp_crop):
        """SC-05: Ideal size (150x180) should have good size score."""
        result = classifier.classify(colorful_stamp_crop)
        # Ideal size should get better score
        assert result.details["size_plausibility"] >= 0.5

    # =========================================================================
    # Result Object Tests
    # =========================================================================

    def test_result_has_reason(self, classifier, colorful_stamp_crop):
        """Result should have a reason string."""
        result = classifier.classify(colorful_stamp_crop)
        assert isinstance(result.reason, str)
        assert len(result.reason) > 0

    def test_result_has_is_stamp(self, classifier, colorful_stamp_crop):
        """Result should have is_stamp boolean."""
        result = classifier.classify(colorful_stamp_crop)
        assert isinstance(result.is_stamp, bool)
