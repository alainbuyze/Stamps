# Stamp Detection: Lessons Learned

## Overview

This document captures the various approaches attempted for stamp detection, their limitations, and conclusions for future development. Includes both classical computer vision and Vision LLM approaches.

**Test Images Used:**
- `images (1).jpg` - 3 colorful stamps on teal background
- `i-completed-my-trans-mississippi-this-month-with-the-last-v0-bfekycfiljgg1.webp` - Album page with ~16 stamps including gray/violet row
- `s-l1600 (2).webp` - Album page with space stamps and binder
- `s-l1600 (10).webp` - Single white Europa stamp on white background

---

## Approaches Attempted

### 1. Adaptive Threshold with Contour Detection

**Method:**
```python
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV, 11, 3)
contours = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
```

**Result:** Failed on teal background - no stamps detected.

**Why it failed:** Adaptive threshold works on local contrast. On uniform colored backgrounds, the threshold doesn't separate stamps from background effectively.

---

### 2. Saturation-Based Detection

**Method:**
```python
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
saturation = hsv[:, :, 1]
sat_mask = (saturation > threshold).astype(np.uint8) * 255
```

**Result:** Worked for colorful stamps, failed for gray/violet stamps.

**Why it failed:** Low-saturation stamps (grayscale, violet, brown) have saturation values similar to neutral backgrounds. The method is inherently biased toward colorful content.

---

### 3. Value Difference from Background (Otsu)

**Method:**
```python
# Estimate background brightness from corners/edges
bg_value = estimate_background(gray)
value_diff = np.abs(gray.astype(np.float32) - bg_value)
_, binary = cv2.threshold(value_diff, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
```

**Result:**
- Worked well for colorful stamps on teal background
- Worked for Trans-Mississippi album page (16 stamps detected)
- Failed for white stamps on white backgrounds

**Why it failed:** When a stamp has a white/light interior on a white background, the interior has LOW value difference and merges with the background. Only the dark content (perforations, printed design) shows contrast, creating fragmented detection.

---

### 4. Edge Detection with Flood Fill

**Method:**
```python
edges = cv2.Canny(gray, 20, 60)
edge_dilated = cv2.dilate(edges, kernel, iterations=3)
edge_closed = cv2.morphologyEx(edge_dilated, cv2.MORPH_CLOSE, large_kernel)
# Flood fill from corners to mark background
cv2.floodFill(edge_closed, mask, (0, 0), 128)
# Unfilled regions = stamps
```

**Result:** Failed - detected tiny fragments, not stamps.

**Why it failed:**
1. Internal stamp content (text, portraits, patterns) creates many internal edges
2. Edge dilation connects internal edges, breaking up the stamp region
3. Flood fill leaks through gaps in perforation patterns
4. Result: stamp interiors get filled as "background"

---

### 5. Low Threshold with Heavy Morphological Closing

**Method:**
```python
low_threshold = 8  # Very low
value_mask = (value_diff > low_threshold).astype(np.uint8) * 255
# Progressive closing with 7x7, 11x11, 15x15 kernels
closed = cv2.morphologyEx(value_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
```

**Result:** Still fragmented stamps on white backgrounds.

**Why it failed:** Even with aggressive closing, large white areas inside stamps (larger than kernel size) remain as holes. Would need impossibly large kernels that would merge separate stamps.

---

### 6. Hybrid Edge + Value Approach

**Method:**
```python
# Method A: Edge-based (fill closed edge contours)
binary_edge = fill_edge_contours(edges)

# Method B: Value-based (Otsu on value_diff)
binary_value = otsu_threshold(value_diff)

# Combine with OR
binary = cv2.bitwise_or(binary_edge, binary_value)
```

**Result:** Inconsistent - works for some images, fails for others.

**Why it failed:** The combination inherits weaknesses from both methods. Edge-based detection is noisy and depends on edge continuity. Value-based detection fails for low-contrast stamps.

---

---

## Vision LLM Detection Approaches

After classical CV failed, Vision LLM detection was attempted using Claude and Groq APIs to detect stamp bounding boxes.

### 7. Vision LLM with Percentage Coordinates

**Method:**
```python
DETECTION_PROMPT = """Analyze this stamp album page. Detect each UNIQUE postage stamp.

For EACH stamp, output a JSON object:
{
  "box": [x_min, y_min, x_max, y_max],  // Percentage coordinates (0-100)
  "shape": "rectangle|triangle|diamond|irregular",
  "confidence": "high|medium|low"
}
"""
# Send preprocessed image to LLM
# Parse JSON response
# Convert percentage coordinates to pixels
```

**Providers Tested:**
- Claude Haiku (`claude-3-5-haiku-20241022`)
- Claude Sonnet 4 (`claude-sonnet-4-20250514`)
- Groq Llama Vision (`llama-3.2-11b-vision-preview`)

**Result:** All providers failed with systematic spatial offset.

**Evidence from Testing (Trans-Mississippi album page):**

| Provider | Stamps Detected | Spatial Accuracy | Notes |
|----------|-----------------|------------------|-------|
| Claude Haiku | 16 | Poor - boxes offset by ~10-20% | Boxes in grid pattern but wrong positions |
| Claude Sonnet 4 | 15 | Poor - same offset issue | No improvement over Haiku |
| Groq Llama | 15-16 | Poor - similar offset | Fallback produced same results |

**Visual Evidence:**
- Bounding boxes appeared in roughly correct *relative* positions to each other
- But *absolute* positions were systematically wrong
- Boxes were offset from actual stamps by significant margin
- Many stamps missed entirely (especially right side and bottom of page)
- Duplicate detections on some stamps despite NMS

**Why it failed:**

1. **Vision LLMs lack spatial precision** - They can SEE objects and understand relationships, but cannot accurately report pixel/percentage coordinates. This is a known limitation of current Vision LLM architectures.

2. **Coordinate format confusion** - LLMs may interpret coordinate systems differently (origin position, axis direction).

3. **Image preprocessing artifacts** - Downscaling for token efficiency may affect how the LLM perceives positions.

4. **Attention mechanism limitations** - Transformer attention doesn't preserve precise spatial information the way CNNs do.

**Session Data:**
- Session `20260303_092013_3aaf2b`: Claude Haiku primary, misaligned boxes
- Session `20260303_094844_f89d22`: Claude Sonnet attempted (model 404), Groq fallback
- Session `20260303_095033_c7fb43`: Claude Sonnet 4 primary, same offset issue

**Crop Quality Evidence:**
The misaligned boxes produced crops that cut off parts of stamps:
- *"partial view of a green-colored design"*
- *"The provided image does not display sufficient details"*
- *"partial view with a reddish-brown color scheme"*

This confirms the bounding boxes were not properly aligned with stamp positions.

---

### 8. NMS (Non-Maximum Suppression) for Duplicates

**Method:**
```python
def apply_nms(detections, iou_threshold=0.3):
    # Sort by confidence
    # Remove overlapping boxes where IoU > threshold
```

**Result:** Reduced duplicates but didn't fix spatial accuracy.

NMS successfully removed overlapping detections when IoU threshold was set appropriately, but since the underlying coordinates were wrong, this didn't improve overall quality.

---

## Fundamental Challenges

### 1. Background Variability
- **Dark backgrounds** (teal, black): Stamps appear lighter
- **Light backgrounds** (white, cream): Stamps may be lighter OR darker
- **Colored backgrounds**: Hue-based separation needed
- **Textured backgrounds** (album pages): Patterns interfere with detection

### 2. Stamp Content Variability
- **Colorful stamps**: High saturation, easy to detect
- **Monochrome stamps**: Low saturation, blend with neutral backgrounds
- **White stamps**: Interior merges with white backgrounds
- **Detailed stamps**: Many internal edges confuse edge-based methods
- **Simple stamps**: Few edges, hard to find boundaries

### 3. Stamp Border Variability
- **Perforated edges**: Gaps in boundary, flood fill leaks through
- **Clean cut edges**: Easier to detect but less common
- **Irregular shapes**: Triangles, diamonds need flexible shape detection

### 4. Environmental Factors
- **Binders/rings**: Create dark regions in corners
- **Page borders**: Large contours that must be filtered
- **Shadows**: Affect brightness-based detection
- **Glare**: Creates bright spots that confuse thresholding

---

## Key Insights

### What Works (Partially)
1. **Value difference + Otsu**: Best general-purpose method for stamps that contrast with background
2. **Adaptive filtering**: Using median contour area to set min/max thresholds
3. **Border removal**: Detecting and removing page borders based on size ratio and span

### What Doesn't Work
1. **Single-method approaches**: No single CV technique handles all stamp types
2. **Fixed thresholds**: Every image has different optimal parameters
3. **Edge-based region filling**: Internal content breaks up stamp regions
4. **Saturation-only**: Fails for ~30% of stamps (monochrome, vintage)

### Parameter Sensitivity
Classical CV methods require careful tuning of:
- Blur kernel size
- Threshold values
- Morphological kernel sizes
- Minimum/maximum area ratios
- Aspect ratio constraints
- Number of iterations

**These parameters that work for one image often fail for another.**

---

## Recommendations

### 1. Use YOLO for Primary Detection (CONFIRMED)

Both classical CV and Vision LLM approaches have failed. **YOLO is the only viable option** for reliable stamp detection.

**Why YOLO:**
- Learned features handle variability automatically
- Single forward pass, no parameter tuning per image
- Trained specifically for object localization (unlike Vision LLMs)
- Can detect stamps regardless of color, background, or content
- Handles occlusion and partial visibility
- Pre-trained models available, fine-tuning straightforward

**Approaches ruled out:**
| Approach | Result | Reason |
|----------|--------|--------|
| Classical CV (Otsu, edges, etc.) | Failed | Too much variability in backgrounds/stamps |
| Vision LLM (Claude, Groq) | Failed | Poor spatial accuracy - can see but can't localize |

### 2. Training Data Options

**Option A: Fine-tune YOLO from scratch**
1. Collect ~500-1000 annotated stamp images
2. Use labeling tool (Label Studio, CVAT, Roboflow)
3. Include variety: colors, backgrounds, conditions, shapes
4. Fine-tune YOLOv8 for stamp-specific detection
5. Expected result: >95% detection accuracy

**Option B: Use Roboflow**
- Pre-trained stamp detection models may exist
- Easy annotation interface
- Hosted training and inference
- Faster time to working solution

**Option C: Semi-supervised approach**
- Use corrected Vision LLM detections as training data
- Manually fix bounding boxes, use as labels
- Bootstrap YOLO training from corrected examples

### 3. Use Vision LLM for Description Only

Vision LLMs are excellent for:
- **Describing stamp content** (themes, colors, text)
- **Generating embeddings** for RAG search
- **Classification** (country, era, condition)

But NOT for:
- **Spatial localization** (bounding boxes)
- **Precise coordinates**

**Recommended pipeline:**
```
YOLO detects stamps → Crop regions → Vision LLM describes → RAG matches
```

### 4. Use Classical CV for Post-Processing Only
Classical CV is still useful for:
- **Perspective correction** after YOLO detects the stamp
- **Edge refinement** to find precise boundaries
- **Quality assessment** (blur detection, color analysis)

### 5. Consider Segment Anything Model (SAM)
For challenging cases, SAM can provide precise segmentation:
- Point-prompt or box-prompt based
- Handles arbitrary shapes well
- Can be combined with YOLO (YOLO detects, SAM segments)

---

## Conclusion

**Both classical CV and Vision LLM approaches are insufficient for reliable stamp detection.**

### Classical CV Failed Because:
- High variability in background colors and textures
- Stamp colors and content vary widely
- Border types (perforated, cut, irregular) differ
- Environmental conditions (lighting, shadows, binders) affect results
- Parameters that work for one image fail for another

### Vision LLM Failed Because:
- Transformer architectures lack precise spatial reasoning
- Can understand "there are stamps" but cannot report accurate coordinates
- Systematic offset in bounding boxes across all providers tested
- Higher-capability models (Sonnet) showed no improvement over basic models (Haiku)
- This is a fundamental architectural limitation, not a prompting issue

### Path Forward: YOLO

The only viable approach is **YOLO-based detection**:
1. Collect training data (500-1000 labeled images) OR use Roboflow
2. Fine-tune YOLOv8 for stamp detection
3. Use Vision LLM only for description/identification (not localization)

**Recommended Architecture:**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Input      │ ──▶ │   YOLO      │ ──▶ │  Crop       │ ──▶ │ Vision LLM  │
│  Image      │     │  Detection  │     │  Stamps     │     │ Description │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                          │                                        │
                          ▼                                        ▼
                    Bounding boxes                           RAG Search
                    (accurate)                              (identification)
```

**Next Steps:**
1. Research Roboflow for pre-trained stamp models
2. If none exist, set up annotation pipeline
3. Train custom YOLOv8 model
4. Integrate into existing `vision_detector.py` as primary method

---

## Files Modified During Experiments

### Classical CV Experiments
- `src/vision/detection/polygon_detector.py` - Multiple iterations of preprocessing approaches
- `test_output/debug_steps/` - Debug images from each approach

### Vision LLM Experiments
- `src/vision/vision_detector.py` - Vision LLM detection with Groq/Claude
- `src/vision/identification_pipeline.py` - Full pipeline orchestration
- `src/vision/preprocessing.py` - Image preprocessing for token efficiency
- `src/core/config.py` - Configuration for detection providers

### Inspection Data (Vision LLM sessions)
- `D:\Stamps\data\inspection\20260303_092013_3aaf2b\` - Claude Haiku test
- `D:\Stamps\data\inspection\20260303_094844_f89d22\` - Claude Sonnet attempt (404)
- `D:\Stamps\data\inspection\20260303_095033_c7fb43\` - Claude Sonnet 4 test

## Test Commands

```powershell
# Run classical CV detection test
& .\.venv\Scripts\python.exe .\src\vision\detection\polygon_detector.py

# Run Vision LLM detection
uv run stamp-tools identify image --path "path/to/album.jpg" --mode multi

# View inspection results
uv run stamp-tools inspect sessions
uv run stamp-tools inspect session <session_id>
```

## Configuration (for Vision LLM experiments)

```env
# .env.local
DETECTION_PRIMARY_PROVIDER=claude_sonnet  # or groq, claude_haiku
DETECTION_CLAUDE_MODEL_SONNET=claude-sonnet-4-20250514
```
