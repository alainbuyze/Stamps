"""Stamp Collection Toolset - AI-powered stamp management.

This package provides tools for building a searchable RAG database from Colnect,
identifying physical stamps via camera, and migrating collections from LASTDODO.

Package Structure
-----------------
core/
    Shared infrastructure: configuration (Pydantic Settings), SQLite database
    operations, custom exceptions, and Rich logging setup.

scraping/
    Web scraping with Playwright and BeautifulSoup. Scrapes stamp catalogs from
    Colnect and user collections from LASTDODO via browser automation.

rag/
    Retrieval-Augmented Generation for stamp identification. Uses OpenAI embeddings
    stored in Supabase with pgvector for similarity search.

vision/
    Multi-provider stamp detection with Roboflow YOLOv8 as primary detector.
    Supports: roboflow (hosted API), roboflow_local (self-trained .pt), groq
    and claude_haiku (Vision LLM fallbacks). Includes preprocessing, inspection
    tools, and active learning loop for model improvement.

identification/
    Pipeline orchestration for stamp identification. Coordinates vision detection,
    RAG search, and result display with user selection interface.

feedback/
    Visual feedback system for scan sessions. Generates annotated images with
    color-coded detections, manages session persistence, and provides Rich
    console output.

Deprecated Packages (flagged for removal)
-----------------------------------------
training/
    YOLO model training infrastructure. DEPRECATED: Replaced by Roboflow-based
    active learning loop. Use Roboflow UI for annotation and export dataset
    for local training with `ultralytics`.

vision/detection/
    OpenCV polygon detection + YOLO fallback pipeline. DEPRECATED: Tested but
    rejected as unreliable. See git commit 3454cd2 for details.

vision/detector.py
    Basic YOLOv8 detector with heuristics. DEPRECATED: Replaced by
    roboflow_detector.py and roboflow_api_detector.py.

See Also
--------
- CLAUDE.md: Full project documentation and conventions
- PRD.md: Product requirements document
"""

__version__ = "0.1.0"
