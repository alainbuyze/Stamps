"""Vision module for stamp detection and identification.

This module provides multi-provider stamp detection with Roboflow YOLOv8 as the
primary detector. Vision LLM (Groq/Claude) serves as fallback.

Detection Provider Hierarchy
----------------------------
1. `roboflow` (default) - Roboflow hosted API, free tier (1000 calls/month)
2. `roboflow_local` - Local YOLOv8 .pt weights (after self-training)
3. `groq` - Vision LLM fallback via Groq API
4. `claude_haiku` - Vision LLM fallback via Anthropic API

Configure via `DETECTION_PRIMARY_PROVIDER` in `.env.app`.

Active Modules
--------------
roboflow_api_detector.py
    RoboflowAPIDetector: Primary detector using Roboflow hosted inference API.
    Fast (~200ms), accurate, handles all stamp shapes including triangular and
    circular. Free tier: 1000 API calls/month.

roboflow_detector.py
    RoboflowDetector: Local YOLOv8 detector using downloaded .pt weights.
    Use after self-training via active learning loop. Requires no API calls.

vision_detector.py
    VisionDetector: Fallback detector using Vision LLMs (Groq primary, Claude
    secondary). Slower (~2-4s) but requires no model training.
    DetectionResult, VisionDetection: Data classes for detection output.

identification_pipeline.py
    IdentificationPipeline: Orchestrates the full detection-to-identification
    flow. Handles mode selection (auto/single/multi), detection provider
    selection, cropping, description generation, and RAG search.
    InspectionManager: Saves all intermediate outputs for debugging.

preprocessing.py
    ImagePreprocessor: Applies preprocessing strategies for LLM detection.
    Strategies: original, downscale, compress (default), posterize, etc.

inspection.py
    InspectionViewer: CLI for browsing inspection sessions.

describer.py
    Generates textual descriptions of stamp images via Groq vision API.

camera.py
    CapturedImage: Data class for camera captures with OpenCV integration.

rag_adapter.py
    RAGSearchAdapter: Bridges vision module to RAG search.

Deprecated Modules (flagged for removal)
----------------------------------------
detection/ (subpackage)
    OpenCV polygon detection + YOLO fallback pipeline. DEPRECATED: Tested but
    rejected as unreliable. See git commit 3454cd2.

detector.py
    Basic YOLOv8 detector with heuristics. DEPRECATED: Replaced by Roboflow
    detectors for better accuracy and shape handling.

Architecture
------------
    INPUT IMAGE
         │
    ┌────┴────┐
    ▼         ▼
  SINGLE    MULTI
    │         │
    │    ROBOFLOW DETECTION (or Vision LLM fallback)
    │         │
    │    CROP STAMPS (full-res)
    └────┬────┘
         │
    DESCRIPTION (Groq vision)
         │
    RAG SEARCH (OpenAI embeddings → Supabase pgvector)
         │
    INSPECTION & RESULTS

Active Learning Loop
--------------------
1. Run pipeline → low RAG confidence flags bad crops
2. Upload flagged images to Roboflow for annotation correction
3. Re-train: export dataset → `yolo train` locally → update model version
4. Switch to `roboflow_local` provider with new weights
"""

# Preprocessing
from .preprocessing import (
    ImagePreprocessor,
    PreprocessingConfig,
    PreprocessingStrategy,
    PreprocessedImage,
    PreprocessingTester,
    create_preprocessor_from_env,
)

# Vision LLM Detection
from .vision_detector import (
    VisionDetector,
    DetectionResult,
    VisionDetection,
    create_vision_detector_from_env,
    DETECTION_PROMPT,
    GROQ,
    CLAUDE_HAIKU,
    CLAUDE_SONNET,
)

# Identification Pipeline
from .identification_pipeline import (
    IdentificationPipeline,
    IdentificationMode,
    IdentificationSession,
    StampIdentification,
    RAGMatch,
    InspectionManager,
    create_pipeline_from_env,
)

# Inspection Tools
from .inspection import (
    InspectionViewer,
    InspectionSession as LoadedInspectionSession,
    create_inspection_cli,
)

# RAG Adapter
from .rag_adapter import (
    RAGSearchAdapter,
    create_rag_adapter,
)

__all__ = [
    # Preprocessing
    "ImagePreprocessor",
    "PreprocessingConfig",
    "PreprocessingStrategy",
    "PreprocessedImage",
    "PreprocessingTester",
    "create_preprocessor_from_env",

    # Vision Detection
    "VisionDetector",
    "DetectionResult",
    "VisionDetection",
    "create_vision_detector_from_env",
    "DETECTION_PROMPT",
    "GROQ",
    "CLAUDE_HAIKU",
    "CLAUDE_SONNET",

    # Identification Pipeline
    "IdentificationPipeline",
    "IdentificationMode",
    "IdentificationSession",
    "StampIdentification",
    "RAGMatch",
    "InspectionManager",
    "create_pipeline_from_env",

    # Inspection
    "InspectionViewer",
    "LoadedInspectionSession",
    "create_inspection_cli",

    # RAG Adapter
    "RAGSearchAdapter",
    "create_rag_adapter",
]
