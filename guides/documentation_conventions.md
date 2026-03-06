# Documentation Conventions

This guide defines the documentation standards for all Python modules in the Stamp Collection Toolset. Consistent documentation improves code maintainability, onboarding, and AI-assisted development.

## 1. Package `__init__.py` Documentation

Every package's `__init__.py` MUST include a comprehensive docstring with:

### Required Sections

1. **Package Overview** - One-paragraph description of the package's purpose
2. **Modules** - List each module with description of its classes/functions
3. **Key Exports** - Summary of main public API elements
4. **Deprecated Modules** (if any) - Clearly mark deprecated code with migration path

### Template

```python
"""Package name and one-line description.

Extended description explaining the package's role in the overall system,
what problems it solves, and how it integrates with other packages.

Modules
-------
module_a.py
    ClassA: Brief description of what it does.
    function_a(): Brief description of what it does.

module_b.py
    ClassB: Brief description of what it does.
    helper_function(): Brief description of what it does.

Deprecated Modules (flagged for removal)
----------------------------------------
old_module.py
    DEPRECATED: Brief explanation of why deprecated and what to use instead.
    See git commit XXXXXXX for context.

Key Exports
-----------
- ClassA: Main purpose
- ClassB: Main purpose
- function_a(): Main purpose
"""
```

### Example (from src/vision/__init__.py)

```python
"""Vision module for stamp detection and identification.

This module provides Vision LLM-based stamp detection using cloud APIs.
Groq serves as the primary provider with Claude Haiku as fallback.

Active Modules
--------------
preprocessing.py
    ImagePreprocessor: Applies various preprocessing strategies to optimize
    images for LLM detection.

vision_detector.py
    VisionDetector: Main detection class using Vision LLMs.
    DetectionResult, VisionDetection: Data classes for detection output.

Deprecated Modules (flagged for removal)
----------------------------------------
detection/ (subpackage)
    OpenCV polygon detection + YOLO fallback pipeline. DEPRECATED: Tested but
    rejected as unreliable. See git commit 3454cd2.
"""
```

### Maintenance Rules

- Update `__init__.py` docstrings whenever modules are added, removed, or significantly changed
- Mark deprecated modules immediately when they are superseded
- Include git commit references for historical context on deprecations

---

## 2. Module Docstring Structure

Every module (`.py` file) MUST have a docstring at the top with the following sections:

### Required Sections

1. **Goal** - What problem this module solves
2. **How to Use** - Quick usage example
3. **Function/Class Tree** - Hierarchical overview of public API
4. **Configuration Parameters** - Table of relevant settings
5. **Usage Examples** - Complete, runnable examples

### Template

```python
"""Module name - one-line description.

Goal
----
Explain what problem this module solves and why it exists. Describe its role
in the overall system and what outcomes it produces.

How to Use
----------
Quick start example showing the most common usage pattern:

    from src.package.module import MainClass

    obj = MainClass()
    result = obj.main_method(input_data)

Function Tree
-------------
### Classes
- MainClass
  - __init__(param1, param2)
  - main_method(input) -> Output
  - helper_method() -> None

### Functions
- factory_function() -> MainClass
- utility_function(data) -> ProcessedData

### Data Classes
- InputConfig: Configuration for main operations
- OutputResult: Container for results

Configuration Parameters
------------------------
These settings are loaded from `get_settings()`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| PARAM_ONE | str | "value" | Description of parameter one |
| PARAM_TWO | int | 100 | Description of parameter two |
| PARAM_THREE | bool | True | Description of parameter three |

Usage Examples
--------------
### Basic Usage
```python
from src.package.module import MainClass, factory_function

# Create instance via factory (recommended)
obj = factory_function()

# Process data
result = obj.main_method(input_data)
print(f"Result: {result}")
```

### Advanced Usage with Custom Configuration
```python
from src.package.module import MainClass
from src.core.config import get_settings

settings = get_settings()
obj = MainClass(custom_param=settings.CUSTOM_VALUE)

# Use with error handling
try:
    result = obj.main_method(data)
except ProcessingError as e:
    logger.error(f"Processing failed: {e}")
```

See Also
--------
- related_module.py: Description of relationship
- other_package: How they work together
"""
```

### Example (condensed from vision_detector.py)

```python
"""Vision LLM-based stamp detection system.

Goal
----
Detect stamps in images using Vision LLMs (Groq primary, Claude fallback).
Returns bounding boxes with confidence levels for each detected stamp.

How to Use
----------
    from src.vision.vision_detector import create_vision_detector_from_env

    detector = create_vision_detector_from_env()
    result = detector.detect(image)

    for detection in result.detections:
        print(f"Stamp at {detection.center}")

Function Tree
-------------
### Classes
- VisionDetector
  - __init__(groq_client, anthropic_client)
  - detect(image, strategy, inspection_id) -> DetectionResult
  - _call_groq(image) -> LLMResponse
  - _call_claude(image) -> LLMResponse

### Data Classes
- DetectionResult: Container for all detections
- VisionDetection: Single stamp detection with geometry
- LLMResponse: Raw LLM response wrapper

### Factory Functions
- create_vision_detector_from_env() -> VisionDetector

Configuration Parameters
------------------------
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| GROQ_API_KEY | str | - | API key for Groq |
| GROQ_MODEL | str | llama-3.2-90b-vision | Vision model name |
| DETECTION_NMS_IOU_THRESHOLD | float | 0.5 | NMS overlap threshold |
"""
```

---

## 3. Module `__main__` Block

Every module MUST include an `if __name__ == "__main__":` block with:

1. **Hardcoded test case** - Simple, self-contained test
2. **Expected output** - What success looks like
3. **No external dependencies** - Should run without test fixtures

### Template

```python
if __name__ == "__main__":
    """Test module functionality with hardcoded inputs."""
    import logging

    # Setup logging for test
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("=== ModuleName Test ===")
    print("Testing module functionality with hardcoded input...")

    try:
        # 1. Setup - create test data
        test_input = {"key": "value", "number": 42}
        print(f"Test input: {test_input}")

        # 2. Execute - run the main functionality
        from src.package.module import MainClass
        obj = MainClass()
        result = obj.process(test_input)

        # 3. Verify - check results
        print(f"Result: {result}")
        assert result is not None, "Result should not be None"
        assert result.status == "success", f"Expected success, got {result.status}"

        print("\n[PASS] All tests passed!")

    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        import sys
        sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
```

### Guidelines for Test Cases

1. **Self-contained** - No external files or databases required
2. **Deterministic** - Same input always produces same output
3. **Fast** - Should complete in under 5 seconds
4. **Informative** - Print progress and results clearly
5. **Exit codes** - Return 0 on success, 1 on failure

### Example (from roboflow_detector.py)

```python
if __name__ == "__main__":
    """Test the Roboflow detector with hardcoded input."""
    import logging
    from pathlib import Path

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== Roboflow Detector Test ===")

    try:
        # Create detector
        detector = create_roboflow_detector()
        print(f"Detector created with model: {detector.model_path}")

        # Create synthetic test image
        import numpy as np
        import cv2
        test_image = np.zeros((600, 800, 3), dtype=np.uint8)
        cv2.rectangle(test_image, (100, 100), (300, 250), (255, 255, 255), -1)

        # Run detection
        result = detector.detect(test_image)
        print(f"Detected {len(result.detections)} stamps")

        print("\n[PASS] Test completed successfully!")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import sys
        sys.exit(1)
```

---

## 4. Function and Method Docstrings

All public functions and methods MUST have docstrings following NumPy style:

```python
def process_stamps(
    image: np.ndarray,
    strategy: PreprocessingStrategy = PreprocessingStrategy.COMPRESS,
    save_intermediates: bool = False,
) -> DetectionResult:
    """Detect and process stamps in an image.

    Applies preprocessing strategy, runs vision LLM detection, and returns
    structured results with bounding boxes and confidence scores.

    Parameters
    ----------
    image : np.ndarray
        Input image as BGR numpy array (OpenCV format).
    strategy : PreprocessingStrategy, optional
        Preprocessing strategy to apply before detection.
        Default: PreprocessingStrategy.COMPRESS
    save_intermediates : bool, optional
        If True, save intermediate images for debugging.
        Default: False

    Returns
    -------
    DetectionResult
        Container with:
        - detections: List[VisionDetection] with bounding boxes
        - success: bool indicating if detection succeeded
        - provider_used: str name of LLM provider used
        - processing_time_ms: int total processing time

    Raises
    ------
    DetectionError
        If both primary and fallback providers fail.
    ValueError
        If image is empty or has invalid dimensions.

    Examples
    --------
    >>> from src.vision import process_stamps
    >>> import cv2
    >>> image = cv2.imread("album_page.jpg")
    >>> result = process_stamps(image)
    >>> print(f"Found {len(result.detections)} stamps")

    See Also
    --------
    VisionDetector.detect : Lower-level detection method
    ImagePreprocessor.apply : Apply preprocessing strategies
    """
```

---

## 5. Class Docstrings

Classes MUST document their purpose, attributes, and provide usage example:

```python
class IdentificationPipeline:
    """End-to-end pipeline for stamp identification.

    Orchestrates the complete flow from image input through detection,
    description generation, RAG search, and result aggregation.

    Attributes
    ----------
    detector : VisionDetector
        Vision LLM detector instance.
    describer : StampDescriber
        Description generator for stamp images.
    rag_adapter : RAGSearchAdapter
        Adapter for RAG similarity search.
    inspection_manager : InspectionManager
        Manager for saving intermediate outputs.

    Parameters
    ----------
    mode : IdentificationMode
        Operating mode: AUTO, SINGLE, or MULTI.

    Examples
    --------
    >>> from src.vision import create_pipeline_from_env
    >>> pipeline = create_pipeline_from_env()
    >>> session = pipeline.identify(image)
    >>> for stamp in session.identifications:
    ...     print(f"{stamp.detection_id}: {stamp.top_match.title}")

    See Also
    --------
    VisionDetector : Stamp detection component
    RAGSearchAdapter : Similarity search component
    """
```

---

## 6. Deprecation Documentation

When deprecating code, use the `.. deprecated::` directive and provide migration guidance:

```python
"""Module description.

.. deprecated:: 0.2.0
    This module is DEPRECATED. Use `new_module.py` instead.
    Migration guide:
    - Replace `OldClass` with `NewClass`
    - Replace `old_function()` with `new_function()`
    See git commit abc123 for details on why this was deprecated.

Historical Context
------------------
This approach was explored but abandoned because [reasons].
"""
```

---

## 7. Documentation Checklist

Before committing code, verify:

- [ ] Package `__init__.py` has complete module overview
- [ ] Module has Goal, How to Use, Function Tree, Parameters table
- [ ] Module has `if __name__ == "__main__":` test block
- [ ] All public functions/methods have NumPy-style docstrings
- [ ] All classes document attributes and provide examples
- [ ] Deprecated code has migration guidance and historical context
- [ ] Configuration parameters are documented with types and defaults

---

## 8. Maintaining Documentation

### When Adding New Modules

1. Add module docstring with all required sections
2. Add `__main__` test block
3. Update package `__init__.py` to list the new module
4. Update CLAUDE.md project structure if needed

### When Modifying Modules

1. Update function/class docstrings if signatures change
2. Update parameter tables if configuration changes
3. Update `__main__` test if functionality changes

### When Deprecating Modules

1. Add `.. deprecated::` directive to module docstring
2. Add to "Deprecated Modules" section in package `__init__.py`
3. Add to "Deprecated Packages" section in `src/__init__.py`
4. Include git commit reference for historical context
