# Stamp Collection Toolset - Vision LLM Update

This update replaces OpenCV-based detection with Vision LLM detection (Groq + Claude Haiku fallback).

## What's New

### Architecture Change (Decision #65-69)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 65 | Detection method | Vision LLM | More reliable for variable input |
| 66 | Detection model | Hybrid (Groq → Haiku) | Balance cost and reliability |
| 67 | Single stamp mode | Integrated flag | Skip detection, go direct to RAG |
| 68 | Inspection level | Full debug | All intermediates saved |
| 69 | Preprocessing | Configurable strategies | Find optimal cost/quality |

### New Pipeline Flow

```
INPUT IMAGE
     │
     ├─── SINGLE STAMP MODE ──────────────────────┐
     │                                            │
     └─── MULTI STAMP MODE                        │
              │                                   │
              ▼                                   │
     ┌─────────────────┐                         │
     │  PREPROCESSING  │  ◄── 7 strategies       │
     │  (configurable) │      to test            │
     └────────┬────────┘                         │
              │                                   │
              ▼                                   │
     ┌─────────────────┐                         │
     │  GROQ DETECTION │  ◄── Primary            │
     └────────┬────────┘      (cheap, fast)      │
              │                                   │
         Good? ├── Yes ──────────────────┐       │
              │                          │       │
              No                         │       │
              ▼                          │       │
     ┌─────────────────┐                │       │
     │  CLAUDE HAIKU   │  ◄── Fallback  │       │
     │  FALLBACK       │      (reliable)│       │
     └────────┬────────┘                │       │
              │                          │       │
              └──────────┬───────────────┘       │
                         │                       │
                         ▼                       │
              ┌─────────────────┐               │
              │   CROP STAMPS   │◄──────────────┘
              │   (full-res)    │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   DESCRIPTION   │  ◄── Groq Vision
              │   GENERATION    │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   RAG SEARCH    │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   INSPECTION    │  ◄── All steps saved!
              │   & RESULTS     │
              └─────────────────┘
```

## Files Included

```
src/vision/
├── __init__.py                 # Module exports
├── preprocessing.py            # 7 preprocessing strategies + test framework
├── vision_detector.py          # Hybrid Groq/Claude detection
├── identification_pipeline.py  # Single/multi stamp modes
└── inspection.py               # Inspection viewer & CLI

.env.app                        # Updated configuration
```

## Installation

### 1. Extract to Project

```powershell
# Navigate to your project
cd C:\Users\alain\CascadeProjects\Stamps

# Backup existing vision module
Rename-Item src\vision src\vision_backup

# Extract new files (from ZIP or copy)
# Copy src/vision/ to C:\Users\alain\CascadeProjects\Stamps\src\vision\
# Replace .env.app with new version
```

### 2. Install New Dependencies

```powershell
# Add anthropic package for Claude fallback
uv add anthropic

# Verify
uv run python -c "from src.vision import IdentificationPipeline; print('OK')"
```

### 3. Set Up API Keys

Add to `.env.keys`:

```env
# Existing
GROQ_API_KEY=gsk_xxxxx
OPENAI_API_KEY=sk-xxxxx
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-service-role-key

# NEW - For Claude fallback
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### 4. Create Directories

```powershell
New-Item -ItemType Directory -Force -Path data\inspection
```

## Usage

### Single Stamp Mode

When you have an image of just one stamp:

```python
from src.vision import create_pipeline_from_env, IdentificationMode

pipeline = create_pipeline_from_env()

# Explicit single-stamp mode
session = pipeline.identify_single(image)

# Or use AUTO mode (will detect single stamp automatically)
session = pipeline.identify(image, mode=IdentificationMode.AUTO)

# Results
print(session.identifications[0].top_match)
```

### Multi-Stamp Mode (Album Page)

```python
# Explicit multi-stamp mode
session = pipeline.identify_album_page(image)

# Results
for ident in session.identifications:
    print(f"{ident.identification_id}: {ident.status} ({ident.best_score:.1%})")
```

### CLI Commands

```powershell
# Identify from camera (auto mode)
uv run stamp-tools identify camera

# Identify single stamp from file
uv run stamp-tools identify image --path photo.jpg --mode single

# Identify album page
uv run stamp-tools identify image --path album.jpg --mode multi
```

## Inspection

### View Sessions

```powershell
# List recent sessions
uv run stamp-tools inspect sessions

# View session details
uv run stamp-tools inspect session 20260302_143052_abc123

# View specific identification
uv run stamp-tools inspect identification 20260302_143052_abc123 abc123_001

# Open images in viewer
uv run stamp-tools inspect open-images 20260302_143052_abc123
```

### Inspection Output Structure

```
data/inspection/
└── 20260302_143052_abc123/
    ├── original.jpg              # Original input
    ├── session.json              # Full session data
    ├── inspection_report.json    # Summary report
    │
    ├── preprocessed/
    │   └── preprocessed.jpg      # Image sent to detection API
    │
    ├── annotated/
    │   ├── detection.jpg         # Detection boxes
    │   └── final_result.jpg      # Final results with colors
    │
    └── crops/
        ├── abc123_001.jpg        # Individual stamp crops
        ├── abc123_002.jpg
        └── ...
```

### Programmatic Inspection

```python
from src.vision import InspectionViewer
from pathlib import Path

viewer = InspectionViewer(Path("data/inspection"))

# List sessions
sessions = viewer.list_sessions(limit=10)
viewer.display_sessions_list(sessions)

# Load specific session
session = viewer.load_session("20260302_143052_abc123")
viewer.display_session_detail(session)

# Get images
original = session.get_original()
annotated = session.get_annotated("final_result")
crop = session.get_crop("abc123_001")
```

## Preprocessing Test Framework

### Test All Strategies

```powershell
# Test preprocessing on an image
uv run stamp-tools inspect preprocess-test path/to/album.jpg
```

Output:
```
┌──────────────────────────────────────────────────────────────┐
│                  Preprocessing Comparison                    │
├───────────────┬────────────┬───────────┬───────────────────┤
│ Strategy      │ Resolution │ File Size │ Est. Tokens       │
├───────────────┼────────────┼───────────┼───────────────────┤
│ original      │ 4000x3000  │ 2450 KB   │ 17578             │
│ downscale     │ 640x480    │ 89 KB     │ 450               │
│ compress      │ 640x480    │ 45 KB     │ 450               │
│ posterize     │ 640x480    │ 32 KB     │ 450               │
│ high_contrast │ 640x480    │ 52 KB     │ 450               │
│ edge_enhanced │ 640x480    │ 41 KB     │ 450               │
│ minimal       │ 480x360    │ 18 KB     │ 253               │
└───────────────┴────────────┴───────────┴───────────────────┘
```

### Programmatic Testing

```python
from src.vision import PreprocessingTester, PreprocessingStrategy
from pathlib import Path
import cv2

image = cv2.imread("album.jpg")
tester = PreprocessingTester(Path("data/preprocessing_test"))

# Generate all variants
variants = tester.generate_all_variants(image, save_images=True)

# Get comparison report
report = tester.create_comparison_report(variants)
print(report)

# Create side-by-side visual
comparison = tester.create_visual_comparison(variants, Path("comparison.jpg"))
```

## Configuration Reference

### Detection Provider Settings

```env
# Primary: groq (cheap, fast)
DETECTION_PRIMARY_PROVIDER=groq

# Fallback: claude_haiku (reliable) or claude_sonnet (best quality)
DETECTION_FALLBACK_PROVIDER=claude_haiku
DETECTION_ENABLE_FALLBACK=true

# Trigger fallback if fewer than N stamps detected
DETECTION_MIN_DETECTIONS=1
```

### Preprocessing Strategies

| Strategy | Description | Token Reduction | Best For |
|----------|-------------|-----------------|----------|
| `original` | No change | 0% | Baseline testing |
| `downscale` | Reduce resolution | ~75% | General use |
| `compress` | Downscale + JPEG | ~80% | **Recommended** |
| `posterize` | Reduce colors | ~85% | High contrast images |
| `high_contrast` | CLAHE enhancement | ~80% | Low contrast scans |
| `edge_enhanced` | Edges on posterized | ~85% | Detail preservation |
| `minimal` | Most aggressive | ~95% | Cost-critical |

### Mode Settings

```env
# auto: Detect if single stamp based on aspect ratio and size
# single: Always treat as single stamp (skip detection)
# multi: Always run detection for multiple stamps
IDENTIFICATION_DEFAULT_MODE=auto
```

## Cost Comparison

### Per Album Page (8 stamps average)

| Approach | Detection | Description | Total |
|----------|-----------|-------------|-------|
| Groq only | $0.0003 | $0.0024 | ~$0.003 |
| Groq + Haiku fallback (20%) | $0.0004 | $0.0024 | ~$0.003 |
| Always Haiku | $0.0004 | $0.0024 | ~$0.003 |

### Per 100 Album Pages

| Approach | Est. Cost |
|----------|-----------|
| Groq primary, Haiku fallback | ~$0.30 |
| Always use Haiku for detection | ~$0.35 |

## Troubleshooting

### Detection Returns Empty

1. Check inspection images: `data/inspection/<session>/preprocessed/`
2. Verify preprocessing isn't too aggressive
3. Try `PREPROCESSING_STRATEGY=downscale` (less compression)
4. Check API responses in `session.json`

### Fallback Always Triggered

1. Check Groq API key is valid
2. Review `primary_error` in inspection data
3. Try increasing `DETECTION_MIN_DETECTIONS=0` temporarily

### Single Stamp Detected as Multi

1. Set `IDENTIFICATION_DEFAULT_MODE=single` explicitly
2. Or use `pipeline.identify_single(image)` in code

### Poor RAG Matches

1. Check description quality in inspection data
2. Verify stamp crop is clean (check `crops/` folder)
3. Consider adjusting `CROP_PADDING_PERCENT`
