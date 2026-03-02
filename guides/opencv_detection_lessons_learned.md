# OpenCV Stamp Detection: Lessons Learned

## Overview

This document captures the various classical computer vision approaches attempted for stamp detection, their limitations, and conclusions for future development.

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

### 1. Use YOLO for Primary Detection
The project already includes YOLO as a fallback (`yolo_detector.py`). Based on these experiments, **YOLO should be the primary detection method**, not a fallback.

**Advantages of YOLO:**
- Learned features handle variability automatically
- Single forward pass, no parameter tuning per image
- Can detect stamps regardless of color, background, or content
- Handles occlusion and partial visibility
- Pre-trained models available, fine-tuning straightforward

### 2. Use Classical CV for Post-Processing Only
Classical CV is still useful for:
- **Perspective correction** after YOLO detects the stamp
- **Edge refinement** to find precise boundaries
- **Quality assessment** (blur detection, color analysis)

### 3. Fine-Tune YOLO on Stamp Dataset
1. Collect ~500-1000 annotated stamp images
2. Include variety: colors, backgrounds, conditions, shapes
3. Fine-tune YOLOv8 for stamp-specific detection
4. Expected result: >95% detection accuracy

### 4. Consider Segment Anything Model (SAM)
For challenging cases, SAM can provide precise segmentation:
- Point-prompt or box-prompt based
- Handles arbitrary shapes well
- Can be combined with YOLO (YOLO detects, SAM segments)

---

## Conclusion

**Classical OpenCV approaches are insufficient for reliable stamp detection** due to the high variability in:
- Background colors and textures
- Stamp colors and content
- Border types (perforated, cut, irregular)
- Environmental conditions (lighting, shadows, binders)

The time invested in tuning classical CV parameters would be better spent:
1. Collecting training data for YOLO
2. Fine-tuning a YOLO model
3. Implementing a robust YOLO-based pipeline

**The current architecture already supports this** - `pipeline.py` orchestrates detection, and `yolo_detector.py` exists. The recommendation is to make YOLO the default and remove the classical CV dependency for primary detection.

---

## Files Modified During Experiments

- `src/vision/detection/polygon_detector.py` - Multiple iterations of preprocessing approaches
- `test_output/debug_steps/` - Debug images from each approach

## Test Commands

```powershell
# Run detection test
& .\.venv\Scripts\python.exe .\src\vision\detection\polygon_detector.py

# Change test image in polygon_detector.py main block (line ~687)
image_path = r"A:\Stamps\your_test_image.jpg"
```
