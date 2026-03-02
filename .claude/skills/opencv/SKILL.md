---
name: opencv
description: >
  Use this skill whenever the user wants to perform image or video processing tasks using OpenCV (cv2).
  Triggers include: any mention of 'opencv', 'cv2', 'image processing', 'computer vision', 'object detection',
  'edge detection', 'contour', 'image segmentation', 'optical flow', 'feature detection', 'camera calibration',
  'face detection', 'background subtraction', 'image filtering', 'color space', 'morphological operations',
  'template matching', 'histogram equalization', or 'video capture'. Also use when the user wants to manipulate
  images programmatically (resize, crop, rotate, warp, threshold, blur), extract features from images,
  track objects in video, or build a computer vision pipeline. If the task involves pixels, frames, or visual
  data analysis in Python — consult this skill.
compatibility:
  python: ">=3.8"
  packages:
    - opencv-python>=4.5       # pip install opencv-python
    - opencv-contrib-python    # optional: adds SIFT, AKAZE, extra algorithms
    - numpy>=1.21
    - matplotlib               # optional: for display in notebooks
---

# OpenCV — Techniques & Approaches Reference

## Quick Decision Matrix

| Goal | Recommended Approach |
|------|---------------------|
| Read/write images or video | I/O section |
| Remove noise, smooth | Filtering & Smoothing |
| Detect edges/lines/circles | Edge Detection / Hough Transforms |
| Isolate objects by color/intensity | Thresholding & Segmentation |
| Find and measure shapes | Contours & Shape Analysis |
| Rotate, crop, correct perspective | Geometric Transformations |
| Match or recognize keypoints | Feature Detection & Matching |
| Detect faces, people, objects | Object Detection (DNN / Haar) |
| Track moving objects | Optical Flow & Tracking |
| Fix camera lens distortion | Camera Calibration |
| Enhance contrast | Histograms & CLAHE |

---

## 1. Setup & Imports

```python
import cv2
import numpy as np

# Verify installation
print(cv2.__version__)

# Install (choose one):
# pip install opencv-python             # headless (servers, scripts)
# pip install opencv-contrib-python     # includes SIFT, AKAZE, tracking APIs
```

### Display helpers

```python
# In scripts (blocking window):
cv2.imshow("title", img)
cv2.waitKey(0)
cv2.destroyAllWindows()

# In Jupyter notebooks:
from matplotlib import pyplot as plt
plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
plt.axis('off'); plt.show()
```

---

## 2. Image & Video I/O

```python
# Read image
img = cv2.imread("path/to/image.jpg")           # BGR, uint8
gray = cv2.imread("path/to/image.jpg", cv2.IMREAD_GRAYSCALE)

# Write image
cv2.imwrite("output.png", img)

# Read video / webcam
cap = cv2.VideoCapture("video.mp4")   # or 0 for webcam
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    # process frame...
cap.release()

# Write video
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter("out.mp4", fourcc, 30, (width, height))
out.write(frame)
out.release()
```

**Common pitfall:** OpenCV reads in **BGR** order, not RGB. Always convert before displaying with matplotlib.

---

## 3. Color Space Conversions

```python
gray  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
rgb   = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
hsv   = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
lab   = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
```

**When to use each:**
- **Grayscale** — processing pipelines that don't need color
- **HSV** — color-based masking (robust to lighting changes)
- **LAB** — perceptually uniform; good for color correction
- **YCrCb** — skin tone detection, compression artefacts

### Color range masking (HSV example)

```python
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
lower = np.array([35, 50, 50])    # green range
upper = np.array([85, 255, 255])
mask = cv2.inRange(hsv, lower, upper)
result = cv2.bitwise_and(img, img, mask=mask)
```

---

## 4. Filtering & Smoothing

| Filter | Use case | Function |
|--------|----------|----------|
| Gaussian | General noise removal | `cv2.GaussianBlur(img, (ksize,ksize), sigma)` |
| Median | Salt-and-pepper noise | `cv2.medianBlur(img, ksize)` |
| Bilateral | Blur + preserve edges | `cv2.bilateralFilter(img, d, sigmaColor, sigmaSpace)` |
| Box/Average | Fast, simple blur | `cv2.blur(img, (ksize,ksize))` |
| Custom kernel | Sharpen, emboss, etc. | `cv2.filter2D(img, -1, kernel)` |

```python
# Gaussian — most common choice
blurred = cv2.GaussianBlur(img, (5, 5), 0)

# Bilateral — preserve edges (slower)
smooth = cv2.bilateralFilter(img, 9, 75, 75)

# Sharpening with custom kernel
kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
sharpened = cv2.filter2D(img, -1, kernel)
```

**Rule of thumb:** kernel size must be **odd** (3, 5, 7…).

---

## 5. Morphological Operations

Used on binary images (after thresholding) to remove noise or fill gaps.

```python
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

eroded   = cv2.erode(binary, kernel, iterations=1)
dilated  = cv2.dilate(binary, kernel, iterations=1)
opened   = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)   # erode → dilate (remove noise)
closed   = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)  # dilate → erode (fill holes)
gradient = cv2.morphologyEx(binary, cv2.MORPH_GRADIENT, kernel) # edge outline
tophat   = cv2.morphologyEx(binary, cv2.MORPH_TOPHAT, kernel)  # bright regions on dark bg
blackhat = cv2.morphologyEx(binary, cv2.MORPH_BLACKHAT, kernel)# dark regions on bright bg
```

**Kernel shapes:** `MORPH_RECT`, `MORPH_ELLIPSE`, `MORPH_CROSS`

---

## 6. Edge & Gradient Detection

### Canny (recommended for most use cases)

```python
edges = cv2.Canny(gray, threshold1=50, threshold2=150)
# Lower t1 = more edges detected; ratio 1:2 or 1:3 is a good starting point
```

### Sobel / Scharr (directional gradients)

```python
sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)  # horizontal
sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)  # vertical
magnitude = np.sqrt(sobelx**2 + sobely**2)
magnitude = np.uint8(np.clip(magnitude, 0, 255))

# Scharr — better accuracy for small kernels
scharrx = cv2.Scharr(gray, cv2.CV_64F, 1, 0)
```

### Laplacian (blob edges)

```python
laplacian = cv2.Laplacian(gray, cv2.CV_64F)
laplacian = np.uint8(np.absolute(laplacian))
```

### Hough Transforms

```python
# Detect lines
edges = cv2.Canny(gray, 50, 150)
lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180,
                         threshold=100, minLineLength=50, maxLineGap=10)
for line in lines:
    x1, y1, x2, y2 = line[0]
    cv2.line(img, (x1,y1), (x2,y2), (0,255,0), 2)

# Detect circles
circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                            param1=50, param2=30, minRadius=5, maxRadius=100)
```

---

## 7. Thresholding & Segmentation

### Basic thresholding

```python
_, binary   = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
_, inv      = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
_, otsu     = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)  # auto threshold
_, trunc    = cv2.threshold(gray, 127, 255, cv2.THRESH_TRUNC)
```

### Adaptive thresholding (uneven lighting)

```python
adaptive = cv2.adaptiveThreshold(
    gray, 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,   # or ADAPTIVE_THRESH_MEAN_C
    cv2.THRESH_BINARY,
    blockSize=11,   # neighborhood size (odd)
    C=2             # constant subtracted from mean
)
```

### GrabCut (interactive foreground extraction)

```python
mask = np.zeros(img.shape[:2], np.uint8)
bgd_model = np.zeros((1,65), np.float64)
fgd_model = np.zeros((1,65), np.float64)
rect = (x, y, w, h)  # bounding box around object
cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
mask2 = np.where((mask==2)|(mask==0), 0, 1).astype('uint8')
result = img * mask2[:,:,np.newaxis]
```

### Watershed (touching objects)

```python
# 1. Threshold + morphology to find sure foreground/background
# 2. Mark labels
# 3. Apply watershed
ret, markers = cv2.connectedComponents(sure_fg)
markers += 1
markers[unknown == 255] = 0
markers = cv2.watershed(img, markers)
img[markers == -1] = [255, 0, 0]  # mark boundaries red
```

---

## 8. Contours & Shape Analysis

```python
# Find contours
contours, hierarchy = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Draw contours
cv2.drawContours(img, contours, -1, (0, 255, 0), 2)

# Analyze each contour
for c in contours:
    area = cv2.contourArea(c)
    perimeter = cv2.arcLength(c, closed=True)
    
    # Bounding rectangle
    x, y, w, h = cv2.boundingRect(c)
    aspect_ratio = w / h
    
    # Rotated bounding box
    rect = cv2.minAreaRect(c)
    box  = np.int0(cv2.boxPoints(rect))
    
    # Min enclosing circle
    (cx, cy), radius = cv2.minEnclosingCircle(c)
    
    # Convex hull
    hull = cv2.convexHull(c)
    
    # Moments (centroid)
    M = cv2.moments(c)
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
    
    # Approx polygon (simplify shape)
    epsilon = 0.02 * perimeter
    approx = cv2.approxPolyDP(c, epsilon, closed=True)
    # len(approx) == 3 → triangle, 4 → quadrilateral, etc.

# Shape matching
similarity = cv2.matchShapes(c1, c2, cv2.CONTOURS_MATCH_I1, 0.0)
# 0.0 = identical shape
```

**Retrieval modes:** `RETR_EXTERNAL` (outermost only), `RETR_LIST` (all, no hierarchy), `RETR_TREE` (full hierarchy)

---

## 9. Geometric Transformations

```python
h, w = img.shape[:2]

# Resize
resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
# INTER_NEAREST (fast), INTER_LINEAR (default), INTER_CUBIC (quality upscale), INTER_AREA (downscale)

# Flip
flipped_h = cv2.flip(img, 1)   # horizontal
flipped_v = cv2.flip(img, 0)   # vertical

# Rotate
center = (w//2, h//2)
M = cv2.getRotationMatrix2D(center, angle=45, scale=1.0)
rotated = cv2.warpAffine(img, M, (w, h))

# Translate
M = np.float32([[1, 0, tx], [0, 1, ty]])
translated = cv2.warpAffine(img, M, (w, h))

# Perspective correction (4-point transform)
src_pts = np.float32([[x1,y1],[x2,y2],[x3,y3],[x4,y4]])
dst_pts = np.float32([[0,0],[W,0],[W,H],[0,H]])
M = cv2.getPerspectiveTransform(src_pts, dst_pts)
warped = cv2.warpPerspective(img, M, (W, H))

# Padding
padded = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=0)
```

---

## 10. Feature Detection & Description

| Algorithm | Module | Speed | Best for |
|-----------|--------|-------|----------|
| Harris | `cv2` | Fast | Simple corner detection |
| Shi-Tomasi | `cv2` | Fast | Good features to track |
| SIFT | `contrib` | Moderate | Scale + rotation invariant |
| ORB | `cv2` | Very fast | Real-time, no patent |
| AKAZE | `cv2` | Moderate | Nonlinear scale space |
| BRISK | `cv2` | Fast | Binary descriptor |
| FAST | `cv2` | Fastest | Corners only |

```python
# Shi-Tomasi corners (good for tracking)
corners = cv2.goodFeaturesToTrack(gray, maxCorners=100, qualityLevel=0.3, minDistance=7)

# ORB (recommended free alternative to SIFT)
orb = cv2.ORB_create(nfeatures=500)
keypoints, descriptors = orb.detectAndCompute(gray, None)
img_kp = cv2.drawKeypoints(img, keypoints, None, flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

# SIFT (requires opencv-contrib-python)
sift = cv2.SIFT_create()
kp, des = sift.detectAndCompute(gray, None)
```

---

## 11. Feature Matching

```python
# Brute-force matcher (ORB → NORM_HAMMING; SIFT → NORM_L2)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
matches = bf.match(des1, des2)
matches = sorted(matches, key=lambda x: x.distance)

# Draw top 20 matches
result = cv2.drawMatches(img1, kp1, img2, kp2, matches[:20], None,
                          flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

# FLANN (faster for large descriptor sets)
index_params = dict(algorithm=6, table_number=6, key_size=12, multi_probe_level=1)  # for ORB
search_params = dict(checks=50)
flann = cv2.FlannBasedMatcher(index_params, search_params)
matches = flann.knnMatch(des1, des2, k=2)

# Lowe's ratio test (filter good matches)
good = [m for m, n in matches if m.distance < 0.75 * n.distance]

# Find homography from good matches (image alignment / stitching)
if len(good) >= 4:
    src = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1,1,2)
    dst = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1,1,2)
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
```

---

## 12. Object Detection

### Template Matching

```python
result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
threshold = 0.8
locations = np.where(result >= threshold)
h, w = template.shape[:2]
for pt in zip(*locations[::-1]):
    cv2.rectangle(img, pt, (pt[0]+w, pt[1]+h), (0,255,0), 2)

# Single best match
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
```

### Haar Cascades (face/eye detection)

```python
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30,30))
for (x, y, w, h) in faces:
    cv2.rectangle(img, (x,y), (x+w, y+h), (255,0,0), 2)
```

**Available cascades:** frontal/profile face, eyes, full body, upper body, cat face.

### HOG + SVM (pedestrian detection)

```python
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
boxes, weights = hog.detectMultiScale(img, winStride=(8,8), padding=(4,4), scale=1.05)
```

### DNN Module (YOLO, SSD, MobileNet)

```python
net = cv2.dnn.readNetFromDarknet("yolov4.cfg", "yolov4.weights")
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)  # or DNN_TARGET_CUDA

blob = cv2.dnn.blobFromImage(img, scalefactor=1/255.0, size=(416,416),
                               mean=(0,0,0), swapRB=True, crop=False)
net.setInput(blob)
layer_names = net.getLayerNames()
out_layers = [layer_names[i-1] for i in net.getUnconnectedOutLayers()]
outputs = net.forward(out_layers)

# Parse outputs for bounding boxes, confidence, class IDs
# Apply NMS to remove duplicate detections
indices = cv2.dnn.NMSBoxes(boxes, confidences, score_threshold=0.5, nms_threshold=0.4)
```

---

## 13. Optical Flow & Motion Tracking

### Sparse (Lucas-Kanade) — track specific points

```python
lk_params = dict(winSize=(15,15), maxLevel=2,
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
p0 = cv2.goodFeaturesToTrack(prev_gray, maxCorners=100, qualityLevel=0.3, minDistance=7)
p1, st, err = cv2.calcOpticalFlowPyrLK(prev_gray, next_gray, p0, None, **lk_params)
good_new = p1[st==1]
good_old = p0[st==1]
```

### Dense (Farneback) — motion field for every pixel

```python
flow = cv2.calcOpticalFlowFarneback(prev_gray, next_gray, None,
                                     pyr_scale=0.5, levels=3, winsize=15,
                                     iterations=3, poly_n=5, poly_sigma=1.2, flags=0)
# flow[:,:,0] = dx, flow[:,:,1] = dy
magnitude, angle = cv2.cartToPolar(flow[...,0], flow[...,1])
```

### Background Subtraction

```python
# MOG2 (recommended — handles shadows)
fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)
fgmask = fgbg.apply(frame)

# KNN
fgbg = cv2.createBackgroundSubtractorKNN()
fgmask = fgbg.apply(frame)
```

### Object Trackers (opencv-contrib)

```python
# Available: CSRT (accurate), KCF (fast), MOSSE (fastest)
tracker = cv2.TrackerCSRT_create()
bbox = (x, y, w, h)  # initial bounding box
tracker.init(frame, bbox)

ok, bbox = tracker.update(next_frame)
if ok:
    x, y, w, h = [int(v) for v in bbox]
    cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
```

---

## 14. Camera Calibration & 3D Vision

```python
# 1. Collect checkerboard images
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
obj_pts, img_pts = [], []

for fname in images:
    gray = cv2.imread(fname, cv2.IMREAD_GRAYSCALE)
    ret, corners = cv2.findChessboardCorners(gray, (7,6), None)
    if ret:
        corners2 = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
        obj_pts.append(objp)
        img_pts.append(corners2)

# 2. Calibrate
ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(obj_pts, img_pts, gray.shape[::-1], None, None)

# 3. Undistort
undistorted = cv2.undistort(img, mtx, dist)

# 4. Pose estimation (solvePnP)
ret, rvec, tvec = cv2.solvePnP(obj_pts_3d, img_pts_2d, mtx, dist)
```

### Stereo Vision (depth map)

```python
stereo = cv2.StereoSGBM_create(minDisparity=0, numDisparities=128, blockSize=11)
disparity = stereo.compute(gray_L, gray_R)
# depth = (focal_length * baseline) / disparity
```

---

## 15. Histograms & Contrast Enhancement

```python
# Compute histogram
hist = cv2.calcHist([img], channels=[0], mask=None, histSize=[256], ranges=[0,256])

# Global equalization (grayscale)
equalized = cv2.equalizeHist(gray)

# CLAHE — adaptive equalization (recommended over global)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
cl_img = clahe.apply(gray)

# Histogram back-projection (object localization by color model)
roi_hist = cv2.calcHist([roi_hsv], [0], None, [180], [0,180])
cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)
dst = cv2.calcBackProject([hsv], [0], roi_hist, [0,180], scale=1)
```

---

## 16. Drawing & Annotation

```python
cv2.line(img, (x1,y1), (x2,y2), color=(0,255,0), thickness=2)
cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2)
cv2.circle(img, (cx,cy), radius=10, color=(0,0,255), thickness=-1)  # -1 = filled
cv2.ellipse(img, center, axes, angle, startAngle, endAngle, color, thickness)
cv2.polylines(img, [pts], isClosed=True, color=(0,255,255), thickness=2)
cv2.fillPoly(img, [pts], color=(100,100,100))
cv2.putText(img, "Label", (x,y), cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.8,
            color=(255,255,255), thickness=2, lineType=cv2.LINE_AA)
cv2.arrowedLine(img, (x1,y1), (x2,y2), (0,0,255), 2)
```

---

## 17. Image Arithmetic & Blending

```python
# Safe addition (clips at 255)
added = cv2.add(img1, img2)

# Weighted blend
blended = cv2.addWeighted(img1, alpha=0.6, img2, beta=0.4, gamma=0)

# Bitwise operations (masking)
mask = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)[1]
result = cv2.bitwise_and(img, img, mask=mask)
inv = cv2.bitwise_not(img)
combined = cv2.bitwise_or(img1, img2)

# Absolute difference (change detection)
diff = cv2.absdiff(frame1, frame2)
```

---

## 18. Performance Tips

```python
# Check CUDA availability
cv2.cuda.getCudaEnabledDeviceCount()

# Use GPU mat (requires CUDA build)
gpu_img = cv2.cuda_GpuMat()
gpu_img.upload(img)

# Resize before processing — biggest speedup
small = cv2.resize(img, None, fx=0.5, fy=0.5)

# Profile with ticks
t1 = cv2.getTickCount()
# ... code ...
t2 = cv2.getTickCount()
ms = (t2 - t1) / cv2.getTickFrequency() * 1000
print(f"{ms:.2f} ms")

# Prefer in-place ops where possible
cv2.GaussianBlur(img, (5,5), 0, dst=img)

# Release memory explicitly in loops
cap.release()
out.release()
cv2.destroyAllWindows()
```

---

## 19. Typical Pipeline Patterns

### Document scanner

```
Read → Resize → Grayscale → Bilateral filter → Canny edges
→ findContours → largest 4-point contour → warpPerspective → adaptiveThreshold
```

### Color-based object tracker

```
VideoCapture → cvtColor(HSV) → inRange mask → morphologyEx(OPEN)
→ findContours → largest contour → minEnclosingCircle → draw + log centroid
```

### Face detection pipeline

```
Read frame → Resize → cvtColor(GRAY) → equalizeHist
→ detectMultiScale (Haar) → drawRectangle → display
```

### Feature-based image alignment

```
Read two images → ORB detect+describe → BFMatcher → Lowe's ratio test
→ findHomography (RANSAC) → warpPerspective to align
```

### Motion detection (security camera)

```
VideoCapture → BackgroundSubtractorMOG2 → morphologyEx(DILATE)
→ findContours → filter by area → annotate + alert
```

---

## 20. Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `NoneType` for `imread` | Path wrong or unsupported format | Check path; use `os.path.exists()` |
| Black output after `threshold` | Image already binary or wrong dtype | Ensure `uint8` grayscale input |
| `error: (-215) npoints` in `findContours` | Empty binary image | Check threshold result is non-empty |
| SIFT not found | Using `opencv-python`, not contrib | `pip install opencv-contrib-python` |
| Contours not finding objects | Noise or wrong retrieval mode | Pre-process with morphology; check mode |
| Video writer produces empty file | Wrong codec or size mismatch | Verify `fourcc`, match frame size exactly |
| Camera matrix assertion error in `solvePnP` | Wrong point count or shape | Ensure `(N,1,2)` shape for image points |

---

## Reference Links

- Official docs: https://docs.opencv.org/4.x/
- Python tutorials: https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html
- Contrib modules: https://docs.opencv.org/4.x/d3/d81/tutorial_contrib_root.html
- Sample data: `cv2.data.haarcascades` path for built-in cascade classifiers
