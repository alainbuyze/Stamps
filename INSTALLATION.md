# Stamp Collection Toolset - Project Update

This archive contains new and updated files for your project at:
`C:\Users\alain\CascadeProjects\Stamps`

## Files Included

### New Modules

```
src/
├── vision/
│   └── detection/                # Two-stage detection pipeline
│       ├── __init__.py           # Module exports
│       ├── polygon_detector.py   # Stage 1A: Classical CV
│       ├── stamp_classifier.py   # Stage 1B: Heuristic filter
│       ├── yolo_detector.py      # Stage 1C: YOLO fallback
│       └── pipeline.py           # Orchestration
│
└── feedback/                     # Scan feedback & visualization
    ├── __init__.py               # Module exports
    ├── models.py                 # DetectionFeedback, ScanSession
    ├── visualizer.py             # Annotated image generator
    ├── session_manager.py        # Session persistence
    └── console.py                # Rich console output
```

### Updated Configuration

```
.env.app                          # Complete config with detection & feedback settings
CLAUDE.md                         # Comprehensive project documentation
```

## Installation Instructions

### Option 1: Extract Directly

1. Open the ZIP file
2. Copy the contents to `C:\Users\alain\CascadeProjects\Stamps`
3. When prompted, choose to **merge** folders and **replace** existing files

### Option 2: Manual Copy

1. Extract the ZIP to a temporary location
2. Copy `src/vision/detection/` to `C:\Users\alain\CascadeProjects\Stamps\src\vision\detection\`
3. Copy `src/feedback/` to `C:\Users\alain\CascadeProjects\Stamps\src\feedback\`
4. Replace `.env.app` with the new version
5. Replace `CLAUDE.md` with the new version

### Option 3: PowerShell Commands

```powershell
# Navigate to your project
cd C:\Users\alain\CascadeProjects\Stamps

# Create new directories
New-Item -ItemType Directory -Force -Path src\vision\detection
New-Item -ItemType Directory -Force -Path src\feedback

# Then extract the ZIP and copy files...
```

## After Installation

1. **Sync dependencies** (if new packages added):
   ```powershell
   cd C:\Users\alain\CascadeProjects\Stamps
   uv sync
   ```

2. **Verify installation**:
   ```powershell
   uv run python -c "from src.vision.detection import DetectionPipeline; print('Detection OK')"
   uv run python -c "from src.feedback import ScanSession; print('Feedback OK')"
   ```

3. **Create data directories**:
   ```powershell
   New-Item -ItemType Directory -Force -Path data\sessions
   New-Item -ItemType Directory -Force -Path data\missed_stamps
   ```

## Key Features Added

### Two-Stage Detection (Decision #54-61)
- Stage 1A: OpenCV polygon detection (triangles + quadrilaterals)
- Stage 1B: Heuristic stamp classifier (color, edges, size, perforations)
- Stage 1C: YOLO fallback when CV finds nothing

### Visual Feedback (Decision #62-64)
- Annotated images with colored overlays
- Session persistence (JSON + crops)
- Missed stamps folder for re-ingestion
- Rich console output with tables

## Configuration Reference

### Detection Settings (.env.app)

```env
DETECTION_MODE=album
DETECTION_MIN_VERTICES=3
DETECTION_MAX_VERTICES=4
CLASSIFIER_CONFIDENCE_THRESHOLD=0.6
DETECTION_FALLBACK_TO_YOLO=true
```

### Feedback Settings (.env.app)

```env
SESSIONS_DIR=data/sessions
MISSED_STAMPS_DIR=data/missed_stamps
FEEDBACK_SAVE_ANNOTATED=true
FEEDBACK_SAVE_CROPS=true
```

## Decision Log Updates

| # | Decision | Choice | Date |
|---|----------|--------|------|
| 54 | Detection approach | Two-stage (CV + RAG) | 2026-02-22 |
| 55 | Stage 1 method | CV first, YOLO fallback | 2026-02-22 |
| 56 | Stage 1B filter | Heuristics (train later) | 2026-02-22 |
| 57 | Primary context | Album pages | 2026-02-22 |
| 58 | Stamp shapes | Triangles + Quadrilaterals | 2026-02-22 |
| 59 | Perforation detection | Optional soft signal | 2026-02-22 |
| 60 | Miniature sheets | Whole sheet as one | 2026-02-22 |
| 61 | Diamond classification | As rectangle | 2026-02-22 |
| 62 | Visual feedback | Overlay + Rich console | 2026-02-22 |
| 63 | Session persistence | Save all sessions | 2026-02-22 |
| 64 | Missed stamps | Dedicated folder | 2026-02-22 |
