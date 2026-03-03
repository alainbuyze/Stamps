"""Vision module for stamp detection and identification.

This module provides:
- Image preprocessing with multiple strategies
- Vision LLM-based detection (Groq + Claude Haiku fallback)
- Single-stamp and multi-stamp identification modes
- Full inspection capabilities for debugging and tuning

Architecture:
    ┌──────────────────────────────────────────────────────┐
    │                    INPUT IMAGE                       │
    │                         │                            │
    │           ┌─────────────┴─────────────┐             │
    │           ▼                           ▼             │
    │    ┌─────────────┐           ┌─────────────┐       │
    │    │   SINGLE    │           │    MULTI    │       │
    │    │   STAMP     │           │   (ALBUM)   │       │
    │    └──────┬──────┘           └──────┬──────┘       │
    │           │                         │               │
    │           │              ┌──────────┴──────────┐   │
    │           │              ▼                     │   │
    │           │    ┌─────────────────┐            │   │
    │           │    │  PREPROCESSING  │            │   │
    │           │    └────────┬────────┘            │   │
    │           │             │                      │   │
    │           │             ▼                      │   │
    │           │    ┌─────────────────┐            │   │
    │           │    │  VISION LLM     │◄── Groq    │   │
    │           │    │  DETECTION      │◄── Claude  │   │
    │           │    └────────┬────────┘   fallback │   │
    │           │             │                      │   │
    │           │             ▼                      │   │
    │           │    ┌─────────────────┐            │   │
    │           │    │   CROP STAMPS   │            │   │
    │           └────┤   (full-res)    │◄───────────┘   │
    │                └────────┬────────┘                 │
    │                         │                          │
    │                         ▼                          │
    │                ┌─────────────────┐                │
    │                │  DESCRIPTION    │◄── Groq       │
    │                │  GENERATION     │                │
    │                └────────┬────────┘                │
    │                         │                          │
    │                         ▼                          │
    │                ┌─────────────────┐                │
    │                │  RAG SEARCH     │                │
    │                └────────┬────────┘                │
    │                         │                          │
    │                         ▼                          │
    │                ┌─────────────────┐                │
    │                │  INSPECTION &   │                │
    │                │  RESULTS        │                │
    │                └─────────────────┘                │
    └──────────────────────────────────────────────────┘
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
