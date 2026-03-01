"""Tests for feedback data models."""

import pytest
import numpy as np
from datetime import datetime
from src.feedback.models import DetectionFeedback, ScanSession


class TestDetectionFeedback:
    """Test cases for DetectionFeedback model."""

    # =========================================================================
    # Status Tests
    # =========================================================================

    def test_status_rejected(self):
        """DF-01: stage_1b_passed=False should give status rejected."""
        feedback = DetectionFeedback(stage_1b_passed=False)
        assert feedback.status == "rejected"

    def test_status_pending(self):
        """DF-02: Passed but not searched should be pending."""
        feedback = DetectionFeedback(stage_1b_passed=True, stage_2_searched=False)
        assert feedback.status == "pending"

    def test_status_identified(self):
        """DF-03: RAG match found should be identified."""
        feedback = DetectionFeedback(
            stage_1b_passed=True,
            stage_2_searched=True,
            rag_match_found=True
        )
        assert feedback.status == "identified"

    def test_status_no_match(self):
        """DF-04: Searched but no match should be no_match."""
        feedback = DetectionFeedback(
            stage_1b_passed=True,
            stage_2_searched=True,
            rag_match_found=False
        )
        assert feedback.status == "no_match"

    # =========================================================================
    # Color Tests
    # =========================================================================

    def test_color_bgr_identified(self):
        """DF-05: Identified should be green (0, 255, 0)."""
        feedback = DetectionFeedback(
            stage_1b_passed=True,
            stage_2_searched=True,
            rag_match_found=True
        )
        assert feedback.color_bgr == (0, 255, 0)

    def test_color_bgr_rejected(self):
        """Rejected should be red (0, 0, 255)."""
        feedback = DetectionFeedback(stage_1b_passed=False)
        assert feedback.color_bgr == (0, 0, 255)

    def test_color_bgr_no_match(self):
        """No match should be orange (0, 165, 255)."""
        feedback = DetectionFeedback(
            stage_1b_passed=True,
            stage_2_searched=True,
            rag_match_found=False
        )
        assert feedback.color_bgr == (0, 165, 255)

    def test_color_name_mapping(self):
        """Color names should map correctly."""
        rejected = DetectionFeedback(stage_1b_passed=False)
        assert rejected.color_name == "red"

        identified = DetectionFeedback(
            stage_1b_passed=True,
            stage_2_searched=True,
            rag_match_found=True
        )
        assert identified.color_name == "green"

    # =========================================================================
    # Serialization Tests
    # =========================================================================

    def test_to_dict_keys(self):
        """DF-06: to_dict should have required keys."""
        feedback = DetectionFeedback()
        d = feedback.to_dict()

        required_keys = [
            "detection_id", "shape_type", "bounding_box", "status",
            "stage_1b_passed", "stage_1b_confidence", "stage_1b_reason",
            "stage_2_searched", "rag_match_found", "rag_top_match",
            "rag_confidence", "rag_top_3"
        ]

        for key in required_keys:
            assert key in d, f"Missing key: {key}"

    def test_to_dict_serializable(self):
        """to_dict output should be JSON serializable."""
        import json

        feedback = DetectionFeedback(
            detection_id="test123",
            shape_type="quadrilateral",
            bounding_box=(10, 20, 100, 150),
            stage_1b_passed=True,
            rag_top_3=[{"id": "AU-123", "score": 0.9}]
        )

        d = feedback.to_dict()
        # Should not raise
        json_str = json.dumps(d)
        assert len(json_str) > 0

    # =========================================================================
    # Default Values Tests
    # =========================================================================

    def test_default_detection_id(self):
        """Detection ID should be auto-generated."""
        f1 = DetectionFeedback()
        f2 = DetectionFeedback()
        assert f1.detection_id != f2.detection_id
        assert len(f1.detection_id) == 8

    def test_default_values(self):
        """Default values should be sensible."""
        feedback = DetectionFeedback()
        assert feedback.stage_1b_passed is False
        assert feedback.stage_1b_confidence == 0.0
        assert feedback.rag_match_found is False
        assert feedback.rag_top_3 == []


class TestScanSession:
    """Test cases for ScanSession model."""

    # =========================================================================
    # Session ID Tests
    # =========================================================================

    def test_session_id_format(self):
        """SS-01: Session ID should match expected format."""
        session = ScanSession()
        parts = session.session_id.split("_")
        assert len(parts) == 3
        assert len(parts[0]) == 8  # YYYYMMDD
        assert len(parts[1]) == 6  # HHMMSS
        assert len(parts[2]) == 6  # Random suffix

    def test_session_id_unique(self):
        """Each session should have unique ID."""
        s1 = ScanSession()
        s2 = ScanSession()
        assert s1.session_id != s2.session_id

    # =========================================================================
    # Summary Tests
    # =========================================================================

    def test_summary_counts(self):
        """SS-02: Summary should count correctly."""
        session = ScanSession()
        session.detections = [
            DetectionFeedback(stage_1b_passed=True, stage_2_searched=True, rag_match_found=True),
            DetectionFeedback(stage_1b_passed=True, stage_2_searched=True, rag_match_found=True),
            DetectionFeedback(stage_1b_passed=True, stage_2_searched=True, rag_match_found=False),
            DetectionFeedback(stage_1b_passed=False),
            DetectionFeedback(stage_1b_passed=False),
            DetectionFeedback(stage_1b_passed=False),
        ]

        summary = session.summary
        assert summary["identified"] == 2
        assert summary["no_match"] == 1
        assert summary["rejected"] == 3
        assert summary["total_shapes"] == 6

    def test_summary_empty_session(self):
        """Empty session should have zero counts."""
        session = ScanSession()
        summary = session.summary
        assert summary["total_shapes"] == 0
        assert summary["identified"] == 0
        assert summary["no_match"] == 0
        assert summary["rejected"] == 0

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_identified_stamps_property(self):
        """SS-03: identified_stamps returns only identified."""
        session = ScanSession()
        session.detections = [
            DetectionFeedback(stage_1b_passed=True, stage_2_searched=True, rag_match_found=True),
            DetectionFeedback(stage_1b_passed=True, stage_2_searched=True, rag_match_found=False),
            DetectionFeedback(stage_1b_passed=False),
        ]

        identified = session.identified_stamps
        assert len(identified) == 1
        assert identified[0].status == "identified"

    def test_missed_stamps_property(self):
        """SS-04: missed_stamps returns only no_match."""
        session = ScanSession()
        session.detections = [
            DetectionFeedback(stage_1b_passed=True, stage_2_searched=True, rag_match_found=True),
            DetectionFeedback(stage_1b_passed=True, stage_2_searched=True, rag_match_found=False),
            DetectionFeedback(stage_1b_passed=False),
        ]

        missed = session.missed_stamps
        assert len(missed) == 1
        assert missed[0].status == "no_match"

    def test_rejected_shapes_property(self):
        """rejected_shapes returns only rejected."""
        session = ScanSession()
        session.detections = [
            DetectionFeedback(stage_1b_passed=True, stage_2_searched=True, rag_match_found=True),
            DetectionFeedback(stage_1b_passed=False),
            DetectionFeedback(stage_1b_passed=False),
        ]

        rejected = session.rejected_shapes
        assert len(rejected) == 2
        for r in rejected:
            assert r.status == "rejected"

    # =========================================================================
    # Serialization Tests
    # =========================================================================

    def test_to_dict_keys(self):
        """SS-05: to_dict should have required keys."""
        session = ScanSession()
        d = session.to_dict()

        required_keys = ["session_id", "timestamp", "source", "summary", "detections"]
        for key in required_keys:
            assert key in d, f"Missing key: {key}"

    def test_to_dict_serializable(self):
        """to_dict output should be JSON serializable."""
        import json

        session = ScanSession(source="test")
        session.detections.append(DetectionFeedback())

        d = session.to_dict()
        json_str = json.dumps(d)
        assert len(json_str) > 0

    def test_timestamp_is_datetime(self):
        """Timestamp should be datetime object."""
        session = ScanSession()
        assert isinstance(session.timestamp, datetime)
