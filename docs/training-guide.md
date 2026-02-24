# Stamp Detection Training Guide

Train a custom YOLOv8 model to detect stamps on album pages, booklets, and scanned images.

## Overview

The pre-trained YOLOv8 model doesn't recognize stamps (it's trained on general objects like cars, people, etc.). To detect stamps on album pages, you need to train a custom model on labeled stamp images.

**What you'll need:**
- 100-200 photos of album pages with stamps
- ~30 minutes to label images
- ~30 minutes to train (CPU) or ~5 minutes (GPU)

**Result:** A custom `stamp_detector.pt` model that finds stamps in any image.

---

## Quick Start

```powershell
# 1. Prepare your images
stamp-tools train prepare --source "C:\Photos\AlbumPages"

# 2. Label stamps in Label Studio
stamp-tools train labelstudio

# 3. Export annotations from Label Studio, then import
stamp-tools train import --annotations "data/training/raw/annotations.json"

# 4. Train the model
stamp-tools train run --epochs 100

# 5. Export for use
stamp-tools train export --model "runs/detect/stamp_detection/train/weights/best.pt"
```

---

## Detailed Instructions

### Step 1: Prepare Training Images

Collect photos of your album pages, stamp booklets, or any images containing stamps you want to detect.

**Good training images include:**
- Album pages with multiple stamps
- Different page backgrounds (black, white, colored)
- Various stamp sizes and orientations
- Different lighting conditions
- Scanned pages and camera photos

**Run the prepare command:**

```powershell
stamp-tools train prepare --source "C:\Your\Photo\Directory"
```

This command:
- Copies images to `data/training/raw/`
- Creates a Label Studio import file
- Shows setup instructions

**Output:**
```
╭─ Prepare Training Dataset ─╮
│                            │
╰────────────────────────────╯
Source: C:\Your\Photo\Directory
Output: data\training

✓ Copied images to data\training\raw
✓ Created import file: data\training\raw\import.json
```

---

### Step 2: Label Stamps with Label Studio

Label Studio is a free, open-source annotation tool. You'll draw rectangles around each stamp in your images.

**Start Label Studio:**

```powershell
stamp-tools train labelstudio
```

If Label Studio isn't installed, you'll be prompted to install it automatically.

**First-time setup in Label Studio:**

1. **Create account** - Sign up with any email (local only, no verification)

2. **Create project**
   - Click "Create Project"
   - Name: `Stamp Detection`
   - Click "Save"

3. **Configure labeling interface**
   - Go to **Settings** → **Labeling Interface**
   - Delete the default template
   - Paste this configuration:
   ```xml
   <View>
     <Image name="image" value="$image"/>
     <RectangleLabels name="label" toName="image">
       <Label value="stamp" background="#FF0000"/>
     </RectangleLabels>
   </View>
   ```
   - Click "Save"

4. **Import images**
   - Go to your project
   - Click "Import"
   - Select the file: `data/training/raw/import.json`
   - Or drag and drop images directly

5. **Label stamps**
   - Click on an image to open the labeling interface
   - Select "stamp" label (red)
   - Draw a rectangle around each stamp
   - Click "Submit" to save and move to next image
   - Repeat for all images

**Labeling tips:**
- Draw boxes **tight** around stamp edges (include perforations)
- Label **every** stamp visible in the image
- Skip images that are too blurry or have no stamps
- Aim for at least 100-200 labeled images

6. **Export annotations**
   - Click "Export" in the top menu
   - Select **JSON** format
   - Save to: `data/training/raw/annotations.json`

**Stop Label Studio:** Press `Ctrl+C` in the terminal.

---

### Step 3: Import Annotations

Convert Label Studio annotations to YOLO format:

```powershell
stamp-tools train import --annotations "data/training/raw/annotations.json"
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--annotations` | (required) | Path to Label Studio JSON export |
| `--images` | `data/training/raw` | Directory containing source images |
| `--output` | `data/training` | Output dataset directory |
| `--split` | `0.8` | Train/validation split (80% train, 20% val) |

**Output:**
```
╭─ Import Annotations ─╮
│                      │
╰──────────────────────╯
Annotations: data\training\raw\annotations.json
Images: data\training\raw
Output: data\training
Train/Val split: 80% / 20%

┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric              ┃ Count ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Training images     │   160 │
│ Validation images   │    40 │
│ Total bounding boxes│  1247 │
└─────────────────────┴───────┘
```

---

### Step 4: Train the Model

Start YOLO training:

```powershell
stamp-tools train run
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--dataset` | `data/training` | Dataset directory |
| `--epochs` | `100` | Number of training epochs |
| `--batch` | `16` | Batch size (lower if out of memory) |
| `--model-size` | `n` | Model size: `n`=nano, `s`=small, `m`=medium, `l`=large |
| `--device` | `cpu` | Device: `cpu`, `0` (GPU), `0,1` (multi-GPU) |

**Examples:**

```powershell
# Basic CPU training
stamp-tools train run --epochs 100

# Faster training with GPU (requires CUDA)
stamp-tools train run --device 0 --epochs 100 --batch 32

# Larger, more accurate model (slower)
stamp-tools train run --model-size m --epochs 150

# Quick test with fewer epochs
stamp-tools train run --epochs 20
```

**Training output:**

YOLO will show progress during training:
```
Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
1/100         0G      1.234      0.567      0.891         45        640
2/100         0G      1.123      0.456      0.789         52        640
...
```

**Training time estimates:**
| Device | 100 epochs | 200 images |
|--------|------------|------------|
| CPU | ~30-60 min | ~60-120 min |
| GPU (RTX 3060) | ~5-10 min | ~10-20 min |

Training stops early if no improvement for 20 epochs (patience).

---

### Step 5: Export the Model

After training completes, export the model for use:

```powershell
stamp-tools train export --model "runs/detect/stamp_detection/train/weights/best.pt"
```

This copies the trained model to `models/stamp_detector.pt`.

**Update your configuration** in `.env.app`:

```ini
YOLO_MODEL_PATH=models/stamp_detector.pt
```

Now `stamp-tools identify` will use your trained model!

---

## Additional Commands

### Check Training Status

See where you are in the training workflow:

```powershell
stamp-tools train status
```

**Output:**
```
╭─ Training Status ─╮
│                   │
╰───────────────────╯
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Stage             ┃ Status      ┃ Details                          ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1. Raw Images     │ Ready       │ 200 images in data\training\raw  │
│ 2. Annotations    │ Exported    │ data\training\raw\annotations... │
│ 3. YOLO Dataset   │ Ready       │ 200 images, 1247 boxes           │
│ 4. Trained Model  │ Available   │ runs\detect\stamp_detection\...  │
└───────────────────┴─────────────┴──────────────────────────────────┘
```

### Evaluate Model Performance

Check how well your model performs:

```powershell
stamp-tools train evaluate --model "models/stamp_detector.pt"
```

**Output:**
```
┏━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Metric      ┃  Value ┃
┡━━━━━━━━━━━━━╇━━━━━━━━┩
│ mAP@50      │  0.923 │
│ mAP@50-95   │  0.756 │
│ Precision   │  0.891 │
│ Recall      │  0.867 │
└─────────────┴────────┘
```

**Metric meanings:**
- **mAP@50**: Accuracy at 50% overlap threshold (higher is better, >0.9 is good)
- **mAP@50-95**: Stricter accuracy metric
- **Precision**: How many detections are correct
- **Recall**: How many stamps are found

### Test on a Single Image

Preview detection results before full use:

```powershell
stamp-tools train test --model "models/stamp_detector.pt" --image "test_page.jpg"
```

Save the annotated result:

```powershell
stamp-tools train test --model "models/stamp_detector.pt" --image "test_page.jpg" --save "result.jpg"
```

---

## Troubleshooting

### "Only X images in dataset" warning

You need more labeled images. For reliable detection:
- **Minimum**: 50 images
- **Recommended**: 100-200 images
- **Optimal**: 300+ images

### Training is slow

- Use GPU if available: `--device 0`
- Reduce batch size: `--batch 8`
- Use smaller model: `--model-size n`
- Reduce epochs for testing: `--epochs 20`

### Out of memory errors

- Reduce batch size: `--batch 4` or `--batch 2`
- Use smaller model: `--model-size n`
- Close other applications

### Low accuracy (mAP < 0.7)

- Label more images
- Check label quality (boxes should be tight around stamps)
- Train for more epochs: `--epochs 200`
- Try larger model: `--model-size s` or `--model-size m`

### Model doesn't detect stamps

- Verify images in training set are similar to test images
- Check that labels were exported correctly
- Ensure `YOLO_MODEL_PATH` points to your trained model

### Label Studio won't start

Install manually:
```powershell
pip install label-studio
```

Then run:
```powershell
label-studio start
```

---

## Best Practices

### Image Quality
- **Resolution**: At least 1000x1000 pixels
- **Focus**: Stamps should be clearly visible
- **Lighting**: Even lighting, avoid shadows

### Labeling Quality
- Draw boxes that include the entire stamp with perforations
- Don't include too much background
- Label ALL stamps in each image (don't skip any)
- Be consistent with box placement

### Dataset Diversity
Include variety in your training data:
- Different album page colors
- Various stamp sizes (small definitives to large commemoratives)
- Horizontal and vertical stamps
- Single stamps and blocks
- Camera photos and scans

### Training Strategy
1. Start with quick test: `--epochs 20`
2. Check results with `train test`
3. If promising, train longer: `--epochs 100`
4. If accuracy plateaus, add more training images

---

## File Locations

| Path | Description |
|------|-------------|
| `data/training/raw/` | Raw images for labeling |
| `data/training/raw/import.json` | Label Studio import file |
| `data/training/raw/annotations.json` | Exported annotations |
| `data/training/images/train/` | Training images (YOLO format) |
| `data/training/images/val/` | Validation images (YOLO format) |
| `data/training/labels/train/` | Training labels (YOLO format) |
| `data/training/labels/val/` | Validation labels (YOLO format) |
| `data/training/dataset.yaml` | YOLO dataset configuration |
| `runs/detect/stamp_detection/` | Training runs and models |
| `models/stamp_detector.pt` | Exported model for use |

---

## Command Reference

| Command | Description |
|---------|-------------|
| `stamp-tools train prepare` | Copy images and create Label Studio import |
| `stamp-tools train labelstudio` | Start Label Studio for annotation |
| `stamp-tools train import` | Convert Label Studio export to YOLO format |
| `stamp-tools train run` | Train YOLOv8 model |
| `stamp-tools train export` | Export trained model for detection |
| `stamp-tools train evaluate` | Evaluate model on validation set |
| `stamp-tools train test` | Test model on single image |
| `stamp-tools train status` | Show training workflow status |
