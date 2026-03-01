"""Test imports for the identification pipeline implementation."""

import sys

def test_detection_module():
    """Test detection module imports."""
    try:
        from src.vision.detection import (
            DetectionPipeline,
            PipelineConfig,
            DetectedStamp,
            create_pipeline_from_env,
            PolygonDetector,
            DetectionConfig,
            StampClassifier,
            ClassifierConfig,
            YOLODetector,
            YOLOConfig,
        )
        print("Detection module imports: OK")
        return True
    except Exception as e:
        print(f"Detection module imports: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_feedback_module():
    """Test feedback module imports."""
    try:
        from src.feedback import (
            DetectionFeedback,
            ScanSession,
            FeedbackVisualizer,
            SessionManager,
            display_scan_results,
            display_session_list,
        )
        print("Feedback module imports: OK")
        return True
    except Exception as e:
        print(f"Feedback module imports: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_identifier():
    """Test identifier imports."""
    try:
        from src.identification.identifier import StampIdentifier, IdentificationBatch
        print("Identifier imports: OK")
        return True
    except Exception as e:
        print(f"Identifier imports: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test config settings."""
    try:
        from src.core.config import get_settings
        settings = get_settings()
        print(f"DETECTION_MODE: {settings.DETECTION_MODE}")
        print(f"CLASSIFIER_CONFIDENCE_THRESHOLD: {settings.CLASSIFIER_CONFIDENCE_THRESHOLD}")
        print(f"FEEDBACK_OUTPUT_DIR: {settings.FEEDBACK_OUTPUT_DIR}")
        print("Config settings: OK")
        return True
    except Exception as e:
        print(f"Config settings: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing identification pipeline imports...")
    print()

    results = []
    results.append(("Detection module", test_detection_module()))
    results.append(("Feedback module", test_feedback_module()))
    results.append(("Identifier", test_identifier()))
    results.append(("Config settings", test_config()))

    print()
    print("=" * 50)
    print("Summary:")
    all_passed = True
    for name, passed in results:
        status = "OK" if passed else "FAILED"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print()
        print("All imports successful!")
        sys.exit(0)
    else:
        print()
        print("Some imports failed!")
        sys.exit(1)
