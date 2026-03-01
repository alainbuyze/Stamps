# Identification Pipeline Test Plan

## Overview

This test plan covers the two-stage detection pipeline, feedback system, and CLI commands implemented for stamp identification.

---

## 1. Unit Tests

### 1.1 Detection Module (`src/vision/detection/`)

#### 1.1.1 PolygonDetector (`test_polygon_detector.py`)

| Test ID | Test Case | Input | Expected Output |
|---------|-----------|-------|-----------------|
| PD-01 | Detect quadrilateral stamps | Image with 3 rectangular stamps | 3 DetectedPolygon objects with shape_type="quadrilateral" |
| PD-02 | Detect triangular stamps | Image with triangle stamp | 1 DetectedPolygon with shape_type="triangle" |
| PD-03 | Filter small contours | Image with stamps + noise dots | Only stamp-sized polygons returned |
| PD-04 | Filter large contours | Image where border is detected | Border excluded, only stamps returned |
| PD-05 | Perspective correction | Tilted rectangular stamp | Cropped image is rectangular (not skewed) |
| PD-06 | Empty image | Blank white image | Empty list returned |
| PD-07 | Config min_vertices=4 | Image with triangles + quads | Only quadrilaterals returned |
| PD-08 | Aspect ratio filtering | Very elongated rectangle | Filtered out if outside aspect_ratio_min/max |

```python
# tests/vision/detection/test_polygon_detector.py

import pytest
import numpy as np
import cv2
from src.vision.detection import PolygonDetector, DetectionConfig

class TestPolygonDetector:

    @pytest.fixture
    def detector(self):
        return PolygonDetector()

    @pytest.fixture
    def sample_image_with_rectangles(self):
        """Create test image with 3 rectangles."""
        img = np.ones((800, 600, 3), dtype=np.uint8) * 255
        cv2.rectangle(img, (50, 50), (150, 200), (0, 0, 0), 2)
        cv2.rectangle(img, (200, 100), (350, 280), (0, 0, 0), 2)
        cv2.rectangle(img, (400, 50), (550, 250), (0, 0, 0), 2)
        return img

    def test_detect_rectangles(self, detector, sample_image_with_rectangles):
        """PD-01: Detect quadrilateral stamps."""
        polygons = detector.detect(sample_image_with_rectangles)
        assert len(polygons) == 3
        for p in polygons:
            assert p.shape_type == "quadrilateral"

    def test_empty_image_returns_empty(self, detector):
        """PD-06: Empty image returns no detections."""
        blank = np.ones((400, 400, 3), dtype=np.uint8) * 255
        polygons = detector.detect(blank)
        assert len(polygons) == 0

    def test_cropped_image_not_none(self, detector, sample_image_with_rectangles):
        """Verify cropped images are generated."""
        polygons = detector.detect(sample_image_with_rectangles)
        for p in polygons:
            assert p.cropped_image is not None
            assert p.cropped_image.shape[0] > 0
            assert p.cropped_image.shape[1] > 0
```

#### 1.1.2 StampClassifier (`test_stamp_classifier.py`)

| Test ID | Test Case | Input | Expected Output |
|---------|-----------|-------|-----------------|
| SC-01 | Classify colorful stamp | Cropped stamp image | is_stamp=True, confidence > 0.6 |
| SC-02 | Reject blank area | White rectangle crop | is_stamp=False, reason="color_variance" |
| SC-03 | Reject smooth edges | Solid color rectangle | Lower perforation score |
| SC-04 | Accept complex edges | Stamp with detailed design | High edge_complexity score |
| SC-05 | Size scoring | 150x180 crop (ideal size) | High size_plausibility score |
| SC-06 | Confidence threshold | Crop with score=0.55 | is_stamp=False (threshold=0.6) |
| SC-07 | Custom threshold | score=0.55, threshold=0.5 | is_stamp=True |
| SC-08 | Score details | Any crop | details dict contains all 4 scores |

```python
# tests/vision/detection/test_stamp_classifier.py

import pytest
import numpy as np
import cv2
from src.vision.detection import StampClassifier, ClassifierConfig

class TestStampClassifier:

    @pytest.fixture
    def classifier(self):
        return StampClassifier()

    @pytest.fixture
    def colorful_stamp_crop(self):
        """Create a colorful test image simulating a stamp."""
        img = np.zeros((180, 150, 3), dtype=np.uint8)
        # Add colors and patterns
        cv2.rectangle(img, (10, 10), (140, 170), (200, 100, 50), -1)
        cv2.circle(img, (75, 90), 40, (50, 150, 200), -1)
        cv2.putText(img, "TEST", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return img

    @pytest.fixture
    def blank_crop(self):
        """Create a blank white crop."""
        return np.ones((100, 100, 3), dtype=np.uint8) * 255

    def test_classify_colorful_stamp(self, classifier, colorful_stamp_crop):
        """SC-01: Colorful stamps should be accepted."""
        result = classifier.classify(colorful_stamp_crop)
        assert result.is_stamp is True
        assert result.confidence >= 0.6

    def test_reject_blank_area(self, classifier, blank_crop):
        """SC-02: Blank areas should be rejected."""
        result = classifier.classify(blank_crop)
        assert result.is_stamp is False
        assert "color_variance" in result.reason or result.details["color_variance"] < 0.3

    def test_details_contains_all_scores(self, classifier, colorful_stamp_crop):
        """SC-08: Details should contain all heuristic scores."""
        result = classifier.classify(colorful_stamp_crop)
        assert "color_variance" in result.details
        assert "edge_complexity" in result.details
        assert "size_plausibility" in result.details
        assert "perforation_hint" in result.details
```

#### 1.1.3 YOLODetector (`test_yolo_detector.py`)

| Test ID | Test Case | Input | Expected Output |
|---------|-----------|-------|-----------------|
| YD-01 | Check availability | N/A | is_available() returns bool |
| YD-02 | Lazy loading | New detector | _model is None until detect() |
| YD-03 | Detect returns list | Sample image | List of YOLODetection objects |
| YD-04 | Cropped images included | Sample image | Each detection has cropped_image |
| YD-05 | Size filtering | Image with large/small objects | Only stamp-sized objects returned |
| YD-06 | Unavailable gracefully | ultralytics not installed | Returns empty list, no exception |

```python
# tests/vision/detection/test_yolo_detector.py

import pytest
import numpy as np
from src.vision.detection import YOLODetector, YOLOConfig

class TestYOLODetector:

    @pytest.fixture
    def detector(self):
        return YOLODetector(YOLOConfig(auto_download=False))

    def test_lazy_loading(self, detector):
        """YD-02: Model should not load until first detection."""
        assert detector._model is None

    def test_is_available_returns_bool(self, detector):
        """YD-01: is_available should return boolean."""
        result = detector.is_available()
        assert isinstance(result, bool)

    def test_detect_returns_list(self, detector):
        """YD-03: detect() should return a list."""
        if not detector.is_available():
            pytest.skip("YOLO not available")
        img = np.zeros((640, 640, 3), dtype=np.uint8)
        result = detector.detect(img)
        assert isinstance(result, list)
```

#### 1.1.4 DetectionPipeline (`test_pipeline.py`)

| Test ID | Test Case | Input | Expected Output |
|---------|-----------|-------|-----------------|
| DP-01 | Full pipeline | Image with stamps | Tuple of (accepted, rejected) |
| DP-02 | Accepted stamps pass classifier | Image with stamps | All accepted have classifier_passed=True |
| DP-03 | Rejected shapes fail classifier | Image with non-stamps | All rejected have classifier_passed=False |
| DP-04 | YOLO fallback triggers | Image with no polygons | YOLO detector called |
| DP-05 | YOLO fallback disabled | Config with enable_yolo_fallback=False | Empty result when no polygons |
| DP-06 | Detection IDs unique | Multiple detections | All detection_id values unique |
| DP-07 | Visualize all | accepted + rejected lists | Annotated image with colored boxes |

```python
# tests/vision/detection/test_pipeline.py

import pytest
import numpy as np
import cv2
from src.vision.detection import DetectionPipeline, PipelineConfig

class TestDetectionPipeline:

    @pytest.fixture
    def pipeline(self):
        config = PipelineConfig(enable_yolo_fallback=False)
        return DetectionPipeline(config)

    @pytest.fixture
    def sample_album_page(self):
        """Create test image simulating album page with stamps."""
        img = np.ones((1000, 800, 3), dtype=np.uint8) * 240  # Light gray background

        # Add 3 "stamps" with colors
        for i, (x, y) in enumerate([(100, 100), (300, 100), (100, 400)]):
            stamp = np.random.randint(50, 200, (150, 120, 3), dtype=np.uint8)
            img[y:y+150, x:x+120] = stamp
            cv2.rectangle(img, (x, y), (x+120, y+150), (0, 0, 0), 2)

        return img

    def test_detect_stamps_returns_tuple(self, pipeline, sample_album_page):
        """DP-01: detect_stamps returns tuple of lists."""
        accepted, rejected = pipeline.detect_stamps(sample_album_page)
        assert isinstance(accepted, list)
        assert isinstance(rejected, list)

    def test_accepted_have_classifier_passed(self, pipeline, sample_album_page):
        """DP-02: All accepted stamps should have classifier_passed=True."""
        accepted, _ = pipeline.detect_stamps(sample_album_page)
        for stamp in accepted:
            assert stamp.classifier_passed is True

    def test_detection_ids_unique(self, pipeline, sample_album_page):
        """DP-06: All detection IDs should be unique."""
        accepted, rejected = pipeline.detect_stamps(sample_album_page)
        all_stamps = accepted + rejected
        ids = [s.detection_id for s in all_stamps]
        assert len(ids) == len(set(ids))
```

---

### 1.2 Feedback Module (`src/feedback/`)

#### 1.2.1 DetectionFeedback (`test_models.py`)

| Test ID | Test Case | Input | Expected Output |
|---------|-----------|-------|-----------------|
| DF-01 | Status rejected | stage_1b_passed=False | status == "rejected" |
| DF-02 | Status pending | stage_1b_passed=True, stage_2_searched=False | status == "pending" |
| DF-03 | Status identified | rag_match_found=True | status == "identified" |
| DF-04 | Status no_match | stage_2_searched=True, rag_match_found=False | status == "no_match" |
| DF-05 | Color BGR correct | status="identified" | color_bgr == (0, 255, 0) green |
| DF-06 | to_dict serializable | Complete feedback | Dict with all required keys |

#### 1.2.2 ScanSession (`test_models.py`)

| Test ID | Test Case | Input | Expected Output |
|---------|-----------|-------|-----------------|
| SS-01 | Session ID format | New session | Format: YYYYMMDD_HHMMSS_xxxxxx |
| SS-02 | Summary counts | 2 identified, 1 no_match, 3 rejected | summary["identified"]==2, etc. |
| SS-03 | identified_stamps property | Mixed detections | Only identified ones returned |
| SS-04 | missed_stamps property | Mixed detections | Only no_match ones returned |
| SS-05 | to_dict serializable | Complete session | Dict with detections array |

```python
# tests/feedback/test_models.py

import pytest
import numpy as np
from datetime import datetime
from src.feedback.models import DetectionFeedback, ScanSession

class TestDetectionFeedback:

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

    def test_to_dict_keys(self):
        """DF-06: to_dict should have required keys."""
        feedback = DetectionFeedback()
        d = feedback.to_dict()
        assert "detection_id" in d
        assert "status" in d
        assert "stage_1b_passed" in d
        assert "rag_match_found" in d


class TestScanSession:

    def test_session_id_format(self):
        """SS-01: Session ID should match expected format."""
        session = ScanSession()
        parts = session.session_id.split("_")
        assert len(parts) == 3
        assert len(parts[0]) == 8  # YYYYMMDD
        assert len(parts[1]) == 6  # HHMMSS

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
```

#### 1.2.3 SessionManager (`test_session_manager.py`)

| Test ID | Test Case | Input | Expected Output |
|---------|-----------|-------|-----------------|
| SM-01 | Save session creates directory | Valid session | Session dir exists |
| SM-02 | Save session creates JSON | Valid session | session.json exists |
| SM-03 | Save annotated image | Session with image | annotated.png exists |
| SM-04 | Save crops | Session with detections | crops/ dir with files |
| SM-05 | Save missed stamps | Session with no_match | Files in missed_stamps/ |
| SM-06 | Load session | Saved session ID | Dict with session data |
| SM-07 | List sessions | Multiple saved sessions | List sorted by timestamp desc |
| SM-08 | Get missed stamps | Saved missed stamps | List of Path objects |
| SM-09 | Resolve missed stamp | Stamp path + colnect_id | File moved to resolved/ |

```python
# tests/feedback/test_session_manager.py

import pytest
import numpy as np
from pathlib import Path
import tempfile
import shutil
from src.feedback.models import DetectionFeedback, ScanSession
from src.feedback.session_manager import SessionManager

class TestSessionManager:

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        d = Path(tempfile.mkdtemp())
        yield d
        shutil.rmtree(d)

    @pytest.fixture
    def manager(self, temp_dir):
        return SessionManager(output_dir=temp_dir)

    @pytest.fixture
    def sample_session(self):
        """Create a sample session for testing."""
        session = ScanSession(
            source="test",
            original_image=np.zeros((100, 100, 3), dtype=np.uint8)
        )
        # Add a detection with crop
        detection = DetectionFeedback(
            stage_1b_passed=True,
            stage_2_searched=True,
            rag_match_found=False,
            cropped_image=np.zeros((50, 50, 3), dtype=np.uint8)
        )
        session.detections.append(detection)
        return session

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

    def test_save_missed_stamps(self, manager, sample_session):
        """SM-05: No-match detections saved to missed_stamps/."""
        manager.save_session(sample_session)
        missed = manager.get_missed_stamps()
        assert len(missed) == 1

    def test_load_session(self, manager, sample_session):
        """SM-06: Can load saved session."""
        manager.save_session(sample_session)
        loaded = manager.load_session(sample_session.session_id)
        assert loaded is not None
        assert loaded["session_id"] == sample_session.session_id

    def test_list_sessions(self, manager, sample_session):
        """SM-07: list_sessions returns saved sessions."""
        manager.save_session(sample_session)
        sessions = manager.list_sessions()
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == sample_session.session_id
```

#### 1.2.4 FeedbackVisualizer (`test_visualizer.py`)

| Test ID | Test Case | Input | Expected Output |
|---------|-----------|-------|-----------------|
| FV-01 | Annotate image | Image + detections | Image with overlays |
| FV-02 | Color coding | Identified detection | Green overlay |
| FV-03 | Color coding | Rejected detection | Red overlay |
| FV-04 | Legend drawn | show_legend=True | Legend at bottom |
| FV-05 | No legend | show_legend=False | No legend |

---

### 1.3 Identifier Module (`src/identification/`)

#### 1.3.1 StampIdentifier (`test_identifier.py`)

| Test ID | Test Case | Input | Expected Output |
|---------|-----------|-------|-----------------|
| SI-01 | Lazy initialization | New identifier | _initialized=False |
| SI-02 | Initialize creates components | Call _ensure_initialized | pipeline, describer, searcher not None |
| SI-03 | identify_image returns batch | CapturedImage | IdentificationBatch object |
| SI-04 | Session saved | After identify_image | Session dir created |
| SI-05 | Rejected stamps in session | Image with non-stamps | Detections with stage_1b_passed=False |
| SI-06 | verify_setup | Configured system | Dict with status bools |

```python
# tests/identification/test_identifier.py

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from src.identification.identifier import StampIdentifier, IdentificationBatch
from src.vision.camera import CapturedImage

class TestStampIdentifier:

    @pytest.fixture
    def identifier(self):
        return StampIdentifier()

    def test_lazy_initialization(self, identifier):
        """SI-01: Should not initialize until needed."""
        assert identifier._initialized is False

    def test_verify_setup_returns_dict(self, identifier):
        """SI-06: verify_setup returns status dict."""
        status = identifier.verify_setup()
        assert isinstance(status, dict)
        assert "Detection pipeline" in status
        assert "Groq API" in status
        assert "RAG search" in status

    @pytest.mark.asyncio
    async def test_identify_image_returns_batch(self, identifier):
        """SI-03: identify_image should return IdentificationBatch."""
        # Mock the pipeline and other components
        with patch.object(identifier, '_ensure_initialized'):
            identifier.pipeline = MagicMock()
            identifier.pipeline.detect_stamps.return_value = ([], [])
            identifier.session_manager = MagicMock()
            identifier.session_manager.save_session.return_value = Path("/tmp/test")

            image = CapturedImage(
                frame=np.zeros((100, 100, 3), dtype=np.uint8),
                source="test"
            )
            identifier._initialized = True

            result = await identifier.identify_image(image)
            assert isinstance(result, IdentificationBatch)
```

---

## 2. Integration Tests

### 2.1 Full Pipeline Integration (`test_integration_pipeline.py`)

| Test ID | Test Case | Description |
|---------|-----------|-------------|
| INT-01 | Album page detection | Real album page image → detections → session saved |
| INT-02 | Single stamp image | Single stamp image → 1 detection → RAG search |
| INT-03 | Empty image handling | Blank image → no detections → empty session |
| INT-04 | Mixed detections | Image with stamps + non-stamps → correct classification |

```python
# tests/integration/test_pipeline_integration.py

import pytest
import numpy as np
import cv2
from pathlib import Path
import tempfile
import shutil
from src.vision.detection import create_pipeline_from_env
from src.feedback.session_manager import SessionManager
from src.feedback.models import ScanSession

class TestPipelineIntegration:

    @pytest.fixture
    def temp_output(self):
        d = Path(tempfile.mkdtemp())
        yield d
        shutil.rmtree(d)

    @pytest.fixture
    def realistic_album_page(self):
        """Create more realistic test image."""
        img = np.ones((1200, 900, 3), dtype=np.uint8) * 245

        # Add stamps with varied content
        stamps = [
            ((100, 100), (220, 280)),
            ((300, 100), (450, 300)),
            ((550, 100), (700, 290)),
            ((100, 400), (250, 600)),
        ]

        for (x1, y1), (x2, y2) in stamps:
            # Create colorful stamp
            h, w = y2-y1, x2-x1
            stamp = np.random.randint(30, 220, (h, w, 3), dtype=np.uint8)
            # Add some detail
            cv2.circle(stamp, (w//2, h//2), min(w, h)//3, (200, 50, 100), -1)
            img[y1:y2, x1:x2] = stamp
            cv2.rectangle(img, (x1, y1), (x2, y2), (20, 20, 20), 2)

        return img

    def test_full_detection_flow(self, realistic_album_page, temp_output):
        """INT-01: Full detection pipeline with session save."""
        pipeline = create_pipeline_from_env()
        manager = SessionManager(output_dir=temp_output)

        # Detect
        accepted, rejected = pipeline.detect_stamps(realistic_album_page)

        # Create session
        session = ScanSession(
            source="test",
            original_image=realistic_album_page
        )

        # Convert to feedback (simplified - no RAG)
        from src.feedback.models import DetectionFeedback
        for stamp in accepted:
            feedback = DetectionFeedback(
                detection_id=stamp.detection_id,
                shape_type=stamp.shape_type,
                bounding_box=stamp.bounding_box,
                stage_1b_passed=True,
                stage_1b_confidence=stamp.classifier_confidence,
                cropped_image=stamp.cropped_image
            )
            session.detections.append(feedback)

        # Save
        session_path = manager.save_session(session)

        # Verify
        assert session_path.exists()
        assert (session_path / "session.json").exists()
        assert (session_path / "annotated.png").exists()
        assert len(accepted) > 0
```

---

## 3. CLI Command Tests

### 3.1 Review Commands (`test_cli_review.py`)

| Test ID | Test Case | Command | Expected |
|---------|-----------|---------|----------|
| CLI-01 | Review sessions empty | `review sessions` | "No sessions found" message |
| CLI-02 | Review sessions | `review sessions` | Table with sessions |
| CLI-03 | Review session not found | `review session invalid_id` | Error message, exit code 1 |
| CLI-04 | Review session exists | `review session <valid_id>` | Session details displayed |
| CLI-05 | Review missed empty | `review missed` | "No stamps pending" message |
| CLI-06 | Review missed | `review missed` | Table with missed stamps |

```python
# tests/cli/test_review_commands.py

import pytest
from click.testing import CliRunner
from src.cli import cli
import tempfile
from pathlib import Path

class TestReviewCommands:

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_review_sessions_empty(self, runner, monkeypatch):
        """CLI-01: Empty sessions list shows message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("FEEDBACK_OUTPUT_DIR", tmpdir)
            result = runner.invoke(cli, ["review", "sessions"])
            assert "No sessions found" in result.output or result.exit_code == 0

    def test_review_session_not_found(self, runner, monkeypatch):
        """CLI-03: Invalid session ID shows error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("FEEDBACK_OUTPUT_DIR", tmpdir)
            result = runner.invoke(cli, ["review", "session", "nonexistent_id"])
            assert result.exit_code == 1 or "not found" in result.output.lower()

    def test_review_missed_empty(self, runner, monkeypatch):
        """CLI-05: Empty missed list shows success."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("FEEDBACK_OUTPUT_DIR", tmpdir)
            result = runner.invoke(cli, ["review", "missed"])
            assert "No stamps pending" in result.output or result.exit_code == 0
```

---

## 4. Test Data Requirements

### 4.1 Test Images Needed

| Image | Description | Location |
|-------|-------------|----------|
| `album_page_3stamps.png` | Album page with 3 rectangular stamps | `tests/fixtures/images/` |
| `album_page_mixed.png` | Page with stamps + non-stamp shapes | `tests/fixtures/images/` |
| `single_stamp.jpg` | Single stamp crop | `tests/fixtures/images/` |
| `triangle_stamp.png` | Triangular stamp | `tests/fixtures/images/` |
| `blank_page.png` | Empty white image | `tests/fixtures/images/` |
| `noisy_page.png` | Page with noise/dots | `tests/fixtures/images/` |

### 4.2 Mock Data

```python
# tests/fixtures/mock_rag_results.py

MOCK_RAG_MATCH = {
    "colnect_id": "AU-5352",
    "score": 0.92,
    "country": "Australia",
    "year": 1969,
    "description": "Apollo 11 moon landing commemorative stamp"
}

MOCK_RAG_NO_MATCH = {
    "top_matches": [],
    "confidence": "NO_MATCH"
}
```

---

## 5. Test Execution

### 5.1 Commands

```bash
# Run all tests
uv run pytest tests/

# Run specific module tests
uv run pytest tests/vision/detection/
uv run pytest tests/feedback/
uv run pytest tests/identification/

# Run with coverage
uv run pytest --cov=src --cov-report=html tests/

# Run integration tests only
uv run pytest tests/integration/ -v

# Run CLI tests
uv run pytest tests/cli/ -v
```

### 5.2 CI/CD Configuration

```yaml
# .github/workflows/test.yml (partial)
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Install uv
      uses: astral-sh/setup-uv@v4
    - name: Install dependencies
      run: uv sync --dev
    - name: Run tests
      run: uv run pytest tests/ -v --tb=short
```

---

## 6. Coverage Goals

| Module | Target Coverage |
|--------|-----------------|
| `src/vision/detection/` | 85% |
| `src/feedback/` | 90% |
| `src/identification/identifier.py` | 80% |
| CLI commands | 70% |

---

## 7. Test Priority

1. **P0 (Critical)**: Detection pipeline, session persistence
2. **P1 (High)**: Classifier accuracy, feedback models
3. **P2 (Medium)**: CLI commands, visualizer
4. **P3 (Low)**: Edge cases, error messages
