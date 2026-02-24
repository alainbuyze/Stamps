"""Dataset preparation and management for YOLO training.

Handles:
- Organizing images into train/val splits
- Converting annotations to YOLO format
- Creating dataset configuration files
"""

import json
import logging
import random
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from src.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class BBoxAnnotation:
    """Bounding box annotation in YOLO format."""

    class_id: int
    x_center: float  # Normalized 0-1
    y_center: float  # Normalized 0-1
    width: float  # Normalized 0-1
    height: float  # Normalized 0-1

    def to_yolo_line(self) -> str:
        """Convert to YOLO annotation format line."""
        return f"{self.class_id} {self.x_center:.6f} {self.y_center:.6f} {self.width:.6f} {self.height:.6f}"

    @classmethod
    def from_pixel_coords(
        cls,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        img_width: int,
        img_height: int,
        class_id: int = 0,
    ) -> "BBoxAnnotation":
        """Create from pixel coordinates.

        Args:
            x1, y1: Top-left corner
            x2, y2: Bottom-right corner
            img_width, img_height: Image dimensions
            class_id: Class ID (0 for stamp)
        """
        x_center = ((x1 + x2) / 2) / img_width
        y_center = ((y1 + y2) / 2) / img_height
        width = (x2 - x1) / img_width
        height = (y2 - y1) / img_height

        return cls(
            class_id=class_id,
            x_center=x_center,
            y_center=y_center,
            width=width,
            height=height,
        )


@dataclass
class ImageAnnotation:
    """Annotations for a single image."""

    image_path: Path
    boxes: list[BBoxAnnotation] = field(default_factory=list)

    @property
    def image_name(self) -> str:
        """Image filename without extension."""
        return self.image_path.stem

    def save_yolo_labels(self, labels_dir: Path) -> Path:
        """Save annotations in YOLO format.

        Args:
            labels_dir: Directory to save label file

        Returns:
            Path to saved label file
        """
        label_path = labels_dir / f"{self.image_name}.txt"

        with open(label_path, "w") as f:
            for box in self.boxes:
                f.write(box.to_yolo_line() + "\n")

        return label_path


@dataclass
class StampDataset:
    """Manages a YOLO training dataset for stamp detection."""

    base_dir: Path
    train_split: float = 0.8
    classes: list[str] = field(default_factory=lambda: ["stamp"])

    def __post_init__(self):
        """Ensure directories exist."""
        self.images_dir = self.base_dir / "images"
        self.labels_dir = self.base_dir / "labels"

        # Train/val splits
        self.train_images_dir = self.images_dir / "train"
        self.train_labels_dir = self.labels_dir / "train"
        self.val_images_dir = self.images_dir / "val"
        self.val_labels_dir = self.labels_dir / "val"

        # Create directories
        for d in [
            self.train_images_dir,
            self.train_labels_dir,
            self.val_images_dir,
            self.val_labels_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    @property
    def yaml_path(self) -> Path:
        """Path to dataset YAML config."""
        return self.base_dir / "dataset.yaml"

    def create_yaml_config(self) -> Path:
        """Create YOLO dataset configuration file.

        Returns:
            Path to created YAML file
        """
        config = {
            "path": str(self.base_dir.absolute()),
            "train": "images/train",
            "val": "images/val",
            "names": {i: name for i, name in enumerate(self.classes)},
        }

        with open(self.yaml_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        logger.info(f"Created dataset config at {self.yaml_path}")
        return self.yaml_path

    def add_image(
        self,
        image_path: Path,
        annotations: list[BBoxAnnotation],
        split: Optional[str] = None,
    ) -> None:
        """Add an annotated image to the dataset.

        Args:
            image_path: Path to source image
            annotations: List of bounding box annotations
            split: "train" or "val" (random if not specified)
        """
        if split is None:
            split = "train" if random.random() < self.train_split else "val"

        if split == "train":
            dest_images = self.train_images_dir
            dest_labels = self.train_labels_dir
        else:
            dest_images = self.val_images_dir
            dest_labels = self.val_labels_dir

        # Copy image
        dest_image = dest_images / image_path.name
        shutil.copy2(image_path, dest_image)

        # Save labels
        label_path = dest_labels / f"{image_path.stem}.txt"
        with open(label_path, "w") as f:
            for box in annotations:
                f.write(box.to_yolo_line() + "\n")

        logger.debug(f"Added {image_path.name} to {split} split with {len(annotations)} annotations")

    def get_stats(self) -> dict:
        """Get dataset statistics.

        Returns:
            Dict with counts and splits
        """
        train_images = list(self.train_images_dir.glob("*.[jJ][pP][gG]")) + \
                       list(self.train_images_dir.glob("*.[pP][nN][gG]")) + \
                       list(self.train_images_dir.glob("*.[jJ][pP][eE][gG]"))
        val_images = list(self.val_images_dir.glob("*.[jJ][pP][gG]")) + \
                     list(self.val_images_dir.glob("*.[pP][nN][gG]")) + \
                     list(self.val_images_dir.glob("*.[jJ][pP][eE][gG]"))

        train_labels = list(self.train_labels_dir.glob("*.txt"))
        val_labels = list(self.val_labels_dir.glob("*.txt"))

        # Count total boxes
        total_boxes = 0
        for label_file in train_labels + val_labels:
            with open(label_file) as f:
                total_boxes += len(f.readlines())

        return {
            "train_images": len(train_images),
            "val_images": len(val_images),
            "total_images": len(train_images) + len(val_images),
            "train_labels": len(train_labels),
            "val_labels": len(val_labels),
            "total_annotations": total_boxes,
            "classes": self.classes,
        }

    def import_from_labelstudio(self, export_file: Path) -> int:
        """Import annotations from Label Studio JSON export.

        Args:
            export_file: Path to Label Studio JSON export

        Returns:
            Number of images imported
        """
        logger.info(f"Importing from Label Studio: {export_file}")

        with open(export_file) as f:
            data = json.load(f)

        imported = 0

        for item in data:
            # Get image path from Label Studio format
            image_path = None

            # Try different Label Studio export formats
            if "data" in item and "image" in item["data"]:
                image_url = item["data"]["image"]
                # Extract filename from URL or local path
                if image_url.startswith("/data/"):
                    # Local upload format
                    image_name = image_url.split("/")[-1]
                else:
                    image_name = Path(image_url).name

                # Look for image in common locations
                for search_dir in [
                    self.base_dir / "raw",
                    self.base_dir / "uploads",
                    Path("data/training/raw"),
                ]:
                    potential_path = search_dir / image_name
                    if potential_path.exists():
                        image_path = potential_path
                        break

            if image_path is None or not image_path.exists():
                logger.warning(f"Image not found for item {item.get('id', '?')}")
                continue

            # Parse annotations
            annotations = []
            img_width = item.get("annotations", [{}])[0].get("result", [{}])[0].get(
                "original_width", 1000
            )
            img_height = item.get("annotations", [{}])[0].get("result", [{}])[0].get(
                "original_height", 1000
            )

            for annotation in item.get("annotations", []):
                for result in annotation.get("result", []):
                    if result.get("type") == "rectanglelabels":
                        value = result["value"]

                        # Label Studio uses percentage coordinates
                        x = value["x"] / 100 * img_width
                        y = value["y"] / 100 * img_height
                        w = value["width"] / 100 * img_width
                        h = value["height"] / 100 * img_height

                        x1, y1 = int(x), int(y)
                        x2, y2 = int(x + w), int(y + h)

                        bbox = BBoxAnnotation.from_pixel_coords(
                            x1, y1, x2, y2, int(img_width), int(img_height)
                        )
                        annotations.append(bbox)

            if annotations:
                self.add_image(image_path, annotations)
                imported += 1

        logger.info(f"Imported {imported} annotated images")
        return imported


def prepare_dataset(
    source_dir: Path,
    output_dir: Optional[Path] = None,
    train_split: float = 0.8,
) -> StampDataset:
    """Prepare a dataset from a directory of images.

    Creates the YOLO dataset structure. Images will need to be
    annotated separately using Label Studio.

    Args:
        source_dir: Directory containing raw images
        output_dir: Output directory (defaults to data/training)
        train_split: Fraction of images for training

    Returns:
        StampDataset ready for annotation import
    """
    if output_dir is None:
        output_dir = Path("data/training")

    dataset = StampDataset(base_dir=output_dir, train_split=train_split)

    # Create raw images directory for Label Studio
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Copy images to raw directory
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    copied = 0

    for img_path in source_dir.iterdir():
        if img_path.suffix.lower() in image_extensions:
            dest = raw_dir / img_path.name
            if not dest.exists():
                shutil.copy2(img_path, dest)
                copied += 1

    logger.info(f"Copied {copied} images to {raw_dir}")

    # Create dataset YAML
    dataset.create_yaml_config()

    return dataset
