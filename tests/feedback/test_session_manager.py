"""Tests for SessionManager."""

import pytest
import numpy as np
import json
from pathlib import Path
import tempfile
import shutil
from src.feedback.models import DetectionFeedback, ScanSession
from src.feedback.session_manager import SessionManager


class TestSessionManager:
    """Test cases for SessionManager."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        d = Path(tempfile.mkdtemp())
        yield d
        shutil.rmtree(d, ignore_errors=True)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create SessionManager with temp directory."""
        return SessionManager(output_dir=temp_dir)

    @pytest.fixture
    def sample_session(self):
        """Create a sample session for testing."""
        session = ScanSession(
            source="test",
            original_image=np.zeros((100, 100, 3), dtype=np.uint8)
        )
        return session

    @pytest.fixture
    def session_with_detections(self, sample_session):
        """Create session with various detection types."""
        # Identified stamp
        identified = DetectionFeedback(
            detection_id="test_001",
            shape_type="quadrilateral",
            bounding_box=(10, 10, 50, 60),
            stage_1b_passed=True,
            stage_2_searched=True,
            rag_match_found=True,
            rag_top_match="AU-5352",
            cropped_image=np.zeros((60, 50, 3), dtype=np.uint8)
        )

        # No match stamp
        no_match = DetectionFeedback(
            detection_id="test_002",
            shape_type="quadrilateral",
            bounding_box=(100, 10, 50, 60),
            stage_1b_passed=True,
            stage_2_searched=True,
            rag_match_found=False,
            cropped_image=np.zeros((60, 50, 3), dtype=np.uint8)
        )

        # Rejected shape
        rejected = DetectionFeedback(
            detection_id="test_003",
            shape_type="quadrilateral",
            bounding_box=(200, 10, 30, 30),
            stage_1b_passed=False,
            stage_1b_reason="low_variance",
            cropped_image=np.zeros((30, 30, 3), dtype=np.uint8)
        )

        sample_session.detections = [identified, no_match, rejected]
        return sample_session

    # =========================================================================
    # Directory Creation Tests
    # =========================================================================

    def test_creates_directories(self, manager):
        """Manager should create required directories."""
        assert manager.sessions_dir.exists()
        assert manager.missed_dir.exists()
        assert manager.resolved_dir.exists()

    # =========================================================================
    # Save Session Tests
    # =========================================================================

    def test_save_creates_directory(self, manager, sample_session):
        """SM-01: Saving creates session directory."""
        path = manager.save_session(sample_session)
        assert path.exists()
        assert path.is_dir()

    def test_save_creates_json(self, manager, sample_session):
        """SM-02: Saving creates session.json."""
        path = manager.save_session(sample_session)
        json_path = path / "session.json"
        assert json_path.exists()

    def test_save_creates_annotated(self, manager, sample_session):
        """SM-03: Saving creates annotated.png when image provided."""
        path = manager.save_session(sample_session)
        annotated_path = path / "annotated.png"
        assert annotated_path.exists()

    def test_save_creates_original(self, manager, sample_session):
        """Saving creates original.png when enabled."""
        path = manager.save_session(sample_session)
        original_path = path / "original.png"
        assert original_path.exists()

    def test_save_creates_crops_dir(self, manager, session_with_detections):
        """SM-04: Saving creates crops directory with files."""
        path = manager.save_session(session_with_detections)
        crops_dir = path / "crops"
        assert crops_dir.exists()
        crops = list(crops_dir.glob("*.png"))
        assert len(crops) == 3  # One for each detection

    def test_save_missed_stamps(self, manager, session_with_detections):
        """SM-05: No-match detections saved to missed_stamps/."""
        manager.save_session(session_with_detections)
        missed = manager.get_missed_stamps()
        assert len(missed) == 1  # One no_match detection

    # =========================================================================
    # JSON Content Tests
    # =========================================================================

    def test_json_has_session_id(self, manager, sample_session):
        """JSON should contain session_id."""
        path = manager.save_session(sample_session)
        with open(path / "session.json") as f:
            data = json.load(f)
        assert data["session_id"] == sample_session.session_id

    def test_json_has_summary(self, manager, session_with_detections):
        """JSON should contain accurate summary."""
        path = manager.save_session(session_with_detections)
        with open(path / "session.json") as f:
            data = json.load(f)

        summary = data["summary"]
        assert summary["total_shapes"] == 3
        assert summary["identified"] == 1
        assert summary["no_match"] == 1
        assert summary["rejected"] == 1

    def test_json_has_detections(self, manager, session_with_detections):
        """JSON should contain detection details."""
        path = manager.save_session(session_with_detections)
        with open(path / "session.json") as f:
            data = json.load(f)

        assert len(data["detections"]) == 3

    # =========================================================================
    # Load Session Tests
    # =========================================================================

    def test_load_session(self, manager, sample_session):
        """SM-06: Can load saved session."""
        manager.save_session(sample_session)
        loaded = manager.load_session(sample_session.session_id)
        assert loaded is not None
        assert loaded["session_id"] == sample_session.session_id

    def test_load_nonexistent_session(self, manager):
        """Loading nonexistent session returns None."""
        loaded = manager.load_session("nonexistent_session_id")
        assert loaded is None

    # =========================================================================
    # List Sessions Tests
    # =========================================================================

    def test_list_sessions_empty(self, manager):
        """List sessions on empty dir returns empty list."""
        sessions = manager.list_sessions()
        assert sessions == []

    def test_list_sessions(self, manager, sample_session):
        """SM-07: list_sessions returns saved sessions."""
        manager.save_session(sample_session)
        sessions = manager.list_sessions()
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == sample_session.session_id

    def test_list_sessions_sorted(self, manager):
        """Sessions should be sorted by timestamp descending."""
        import time

        s1 = ScanSession(source="test1")
        manager.save_session(s1)
        time.sleep(0.1)

        s2 = ScanSession(source="test2")
        manager.save_session(s2)

        sessions = manager.list_sessions()
        assert len(sessions) == 2
        # Most recent first
        assert sessions[0]["session_id"] == s2.session_id

    # =========================================================================
    # Missed Stamps Tests
    # =========================================================================

    def test_get_missed_stamps(self, manager, session_with_detections):
        """SM-08: get_missed_stamps returns paths."""
        manager.save_session(session_with_detections)
        missed = manager.get_missed_stamps()
        assert len(missed) == 1
        assert isinstance(missed[0], Path)
        assert missed[0].exists()

    def test_get_missed_stamp_info(self, manager, session_with_detections):
        """Can get info about missed stamp from path."""
        manager.save_session(session_with_detections)
        missed = manager.get_missed_stamps()

        info = manager.get_missed_stamp_info(missed[0])
        assert "session_id" in info
        assert "path" in info
        assert "filename" in info

    # =========================================================================
    # Resolve Missed Tests
    # =========================================================================

    def test_resolve_missed_stamp(self, manager, session_with_detections):
        """SM-09: Can resolve missed stamp with colnect_id."""
        manager.save_session(session_with_detections)
        missed = manager.get_missed_stamps()
        assert len(missed) == 1

        resolved_path = manager.resolve_missed_stamp(missed[0], "AU-9999")

        # Original should be gone
        assert not missed[0].exists()
        # Resolved should exist
        assert resolved_path.exists()
        assert "AU-9999" in resolved_path.name

        # Missed list should be empty
        assert len(manager.get_missed_stamps()) == 0

    # =========================================================================
    # Path Accessor Tests
    # =========================================================================

    def test_get_session_annotated_path(self, manager, sample_session):
        """Can get annotated image path."""
        manager.save_session(sample_session)
        path = manager.get_session_annotated_path(sample_session.session_id)
        assert path is not None
        assert path.exists()
        assert path.name == "annotated.png"

    def test_get_session_crops_dir(self, manager, session_with_detections):
        """Can get crops directory path."""
        manager.save_session(session_with_detections)
        path = manager.get_session_crops_dir(session_with_detections.session_id)
        assert path is not None
        assert path.exists()
        assert path.is_dir()

    # =========================================================================
    # Config Tests
    # =========================================================================

    def test_save_without_original(self, temp_dir, sample_session):
        """Can disable saving original image."""
        manager = SessionManager(output_dir=temp_dir, save_original=False)
        path = manager.save_session(sample_session)
        assert not (path / "original.png").exists()

    def test_save_without_annotated(self, temp_dir, sample_session):
        """Can disable saving annotated image."""
        manager = SessionManager(output_dir=temp_dir, save_annotated=False)
        path = manager.save_session(sample_session)
        assert not (path / "annotated.png").exists()

    def test_save_without_crops(self, temp_dir, session_with_detections):
        """Can disable saving crop images."""
        manager = SessionManager(output_dir=temp_dir, save_crops=False)
        path = manager.save_session(session_with_detections)
        assert not (path / "crops").exists()
