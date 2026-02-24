"""Label Studio integration for stamp annotation.

Provides utilities to:
- Set up Label Studio project for stamp annotation
- Export annotations in YOLO format
- Generate labeling configuration
"""

import json
import logging
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Optional

from src.core.config import get_settings

logger = logging.getLogger(__name__)


# Label Studio configuration for rectangle labeling
LABELING_CONFIG = """
<View>
  <Image name="image" value="$image"/>
  <RectangleLabels name="label" toName="image">
    <Label value="stamp" background="#FF0000"/>
  </RectangleLabels>
</View>
"""


def check_labelstudio_installed() -> bool:
    """Check if Label Studio is installed.

    Returns:
        True if label-studio is available
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "label_studio", "--version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def install_labelstudio() -> bool:
    """Install Label Studio using pip.

    Returns:
        True if installation succeeded
    """
    logger.info("Installing Label Studio...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "label-studio"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.info("Label Studio installed successfully")
            return True
        else:
            logger.error(f"Installation failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Installation error: {e}")
        return False


def start_labelstudio(
    data_dir: Path,
    port: int = 8080,
    open_browser: bool = True,
) -> subprocess.Popen:
    """Start Label Studio server.

    Args:
        data_dir: Directory containing images to label
        port: Port to run on
        open_browser: Whether to open browser automatically

    Returns:
        Popen process handle
    """
    logger.info(f"Starting Label Studio on port {port}...")

    # Set environment for Label Studio data
    env = {
        "LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED": "true",
        "LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT": str(data_dir.absolute()),
    }

    # Merge with current environment
    import os
    full_env = os.environ.copy()
    full_env.update(env)

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "label_studio",
            "start",
            "--port",
            str(port),
            "--no-browser" if not open_browser else "",
        ],
        env=full_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if open_browser:
        webbrowser.open(f"http://localhost:{port}")

    return process


def create_import_file(images_dir: Path, output_path: Optional[Path] = None) -> Path:
    """Create a JSON file for importing images into Label Studio.

    Args:
        images_dir: Directory containing images
        output_path: Output JSON path (defaults to images_dir/import.json)

    Returns:
        Path to created import file
    """
    if output_path is None:
        output_path = images_dir / "import.json"

    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    tasks = []

    for img_path in sorted(images_dir.iterdir()):
        if img_path.suffix.lower() in image_extensions:
            tasks.append({
                "data": {
                    "image": f"/data/local-files/?d={img_path.name}"
                }
            })

    with open(output_path, "w") as f:
        json.dump(tasks, f, indent=2)

    logger.info(f"Created import file with {len(tasks)} images: {output_path}")
    return output_path


def generate_project_setup_instructions(data_dir: Path, port: int = 8080) -> str:
    """Generate instructions for setting up Label Studio project.

    Args:
        data_dir: Directory with images
        port: Label Studio port

    Returns:
        Instruction text
    """
    import_file = data_dir / "import.json"

    return f"""
Label Studio Setup Instructions
================================

1. Start Label Studio:
   stamp-tools train labelstudio --port {port}

2. Create a new project:
   - Click "Create Project"
   - Name it "Stamp Detection"

3. Configure labeling interface:
   - Go to Settings > Labeling Interface
   - Paste this configuration:

{LABELING_CONFIG}

4. Import images:
   - Go to your project
   - Click "Import"
   - Upload the file: {import_file}
   - Or drag and drop images from: {data_dir}

5. Label stamps:
   - Click on each image
   - Draw rectangles around stamps
   - Click "Submit" when done

6. Export annotations:
   - Go to Export
   - Select "JSON" format
   - Save to: {data_dir / 'annotations.json'}

7. Import to training:
   stamp-tools train import --annotations {data_dir / 'annotations.json'}

Tips:
- Label at least 100-200 images for good results
- Include variety: different page backgrounds, stamp sizes, orientations
- Make boxes tight around stamp edges
"""


def parse_labelstudio_export(export_file: Path) -> list[dict]:
    """Parse Label Studio JSON export.

    Args:
        export_file: Path to exported JSON file

    Returns:
        List of annotation dicts with normalized coordinates
    """
    with open(export_file) as f:
        data = json.load(f)

    results = []

    for item in data:
        image_data = item.get("data", {})
        image_url = image_data.get("image", "")

        # Extract image filename
        if "/data/local-files/" in image_url:
            image_name = image_url.split("d=")[-1]
        else:
            image_name = Path(image_url).name

        annotations = []

        for annotation in item.get("annotations", []):
            for result in annotation.get("result", []):
                if result.get("type") == "rectanglelabels":
                    value = result["value"]
                    original_width = result.get("original_width", 100)
                    original_height = result.get("original_height", 100)

                    # Convert from percentage to normalized (0-1)
                    x_center = (value["x"] + value["width"] / 2) / 100
                    y_center = (value["y"] + value["height"] / 2) / 100
                    width = value["width"] / 100
                    height = value["height"] / 100

                    labels = value.get("rectanglelabels", ["stamp"])

                    annotations.append({
                        "class": labels[0] if labels else "stamp",
                        "x_center": x_center,
                        "y_center": y_center,
                        "width": width,
                        "height": height,
                    })

        if annotations:
            results.append({
                "image": image_name,
                "annotations": annotations,
            })

    return results


def export_to_yolo_format(
    labelstudio_export: Path,
    images_dir: Path,
    output_dir: Path,
    train_split: float = 0.8,
) -> dict:
    """Convert Label Studio export to YOLO format.

    Args:
        labelstudio_export: Path to Label Studio JSON export
        images_dir: Directory containing source images
        output_dir: Output directory for YOLO dataset
        train_split: Fraction for training set

    Returns:
        Dict with conversion statistics
    """
    import random
    import shutil

    parsed = parse_labelstudio_export(labelstudio_export)

    # Create YOLO directory structure
    train_images = output_dir / "images" / "train"
    train_labels = output_dir / "labels" / "train"
    val_images = output_dir / "images" / "val"
    val_labels = output_dir / "labels" / "val"

    for d in [train_images, train_labels, val_images, val_labels]:
        d.mkdir(parents=True, exist_ok=True)

    stats = {"train": 0, "val": 0, "total_boxes": 0}

    for item in parsed:
        image_name = item["image"]
        annotations = item["annotations"]

        # Find source image
        source_image = None
        for ext in ["", ".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]:
            candidate = images_dir / f"{Path(image_name).stem}{ext}"
            if candidate.exists():
                source_image = candidate
                break

            candidate = images_dir / image_name
            if candidate.exists():
                source_image = candidate
                break

        if source_image is None:
            logger.warning(f"Image not found: {image_name}")
            continue

        # Decide split
        is_train = random.random() < train_split
        dest_images = train_images if is_train else val_images
        dest_labels = train_labels if is_train else val_labels

        # Copy image
        dest_image = dest_images / source_image.name
        shutil.copy2(source_image, dest_image)

        # Write YOLO labels
        label_path = dest_labels / f"{source_image.stem}.txt"
        with open(label_path, "w") as f:
            for ann in annotations:
                # Class 0 = stamp
                line = f"0 {ann['x_center']:.6f} {ann['y_center']:.6f} {ann['width']:.6f} {ann['height']:.6f}\n"
                f.write(line)
                stats["total_boxes"] += 1

        if is_train:
            stats["train"] += 1
        else:
            stats["val"] += 1

    # Create dataset.yaml
    yaml_content = f"""path: {output_dir.absolute()}
train: images/train
val: images/val
names:
  0: stamp
"""
    yaml_path = output_dir / "dataset.yaml"
    with open(yaml_path, "w") as f:
        f.write(yaml_content)

    logger.info(f"Exported {stats['train']} train, {stats['val']} val images with {stats['total_boxes']} boxes")

    return stats
