"""YOLO model training for stamp detection.

Handles:
- Training YOLOv8 on stamp dataset
- Model evaluation and validation
- Exporting trained models
"""

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Configuration for YOLO training."""

    # Dataset
    dataset_yaml: Path

    # Model
    base_model: str = "yolov8n.pt"  # nano model, fastest
    model_size: str = "n"  # n=nano, s=small, m=medium, l=large, x=extra-large

    # Training parameters
    epochs: int = 100
    batch_size: int = 16
    image_size: int = 640
    patience: int = 20  # Early stopping patience

    # Output
    project_name: str = "stamp_detection"
    run_name: str = "train"

    # Hardware
    device: str = "cpu"  # or "0" for GPU, "0,1" for multi-GPU

    @property
    def output_dir(self) -> Path:
        """Training output directory."""
        return Path("runs") / "detect" / self.project_name / self.run_name


@dataclass
class TrainingResult:
    """Result of a training run."""

    best_model_path: Path
    last_model_path: Path
    metrics: dict
    epochs_completed: int
    output_dir: Path

    @property
    def map50(self) -> float:
        """mAP at IoU 0.5."""
        return self.metrics.get("metrics/mAP50(B)", 0.0)

    @property
    def map50_95(self) -> float:
        """mAP at IoU 0.5-0.95."""
        return self.metrics.get("metrics/mAP50-95(B)", 0.0)


class StampTrainer:
    """Trains YOLOv8 models for stamp detection."""

    def __init__(self, config: Optional[TrainingConfig] = None):
        """Initialize trainer.

        Args:
            config: Training configuration (uses defaults if not provided)
        """
        self.config = config
        self._model = None

    def train(self, config: Optional[TrainingConfig] = None) -> TrainingResult:
        """Train a YOLO model on stamp dataset.

        Args:
            config: Training config (uses self.config if not provided)

        Returns:
            TrainingResult with model paths and metrics
        """
        from ultralytics import YOLO

        cfg = config or self.config
        if cfg is None:
            raise ValueError("No training configuration provided")

        logger.info(f"Starting training with {cfg.base_model}")
        logger.info(f"Dataset: {cfg.dataset_yaml}")
        logger.info(f"Epochs: {cfg.epochs}, Batch: {cfg.batch_size}, Image size: {cfg.image_size}")

        # Load base model
        model = YOLO(cfg.base_model)

        # Train
        results = model.train(
            data=str(cfg.dataset_yaml),
            epochs=cfg.epochs,
            batch=cfg.batch_size,
            imgsz=cfg.image_size,
            patience=cfg.patience,
            project=cfg.project_name,
            name=cfg.run_name,
            device=cfg.device,
            verbose=True,
            plots=True,
        )

        # Get output paths
        output_dir = Path(results.save_dir)
        best_model = output_dir / "weights" / "best.pt"
        last_model = output_dir / "weights" / "last.pt"

        # Extract metrics
        metrics = {}
        if hasattr(results, "results_dict"):
            metrics = results.results_dict

        logger.info(f"Training complete. Best model: {best_model}")

        return TrainingResult(
            best_model_path=best_model,
            last_model_path=last_model,
            metrics=metrics,
            epochs_completed=cfg.epochs,
            output_dir=output_dir,
        )

    def evaluate(self, model_path: Path, dataset_yaml: Path) -> dict:
        """Evaluate a trained model on validation set.

        Args:
            model_path: Path to trained model
            dataset_yaml: Path to dataset config

        Returns:
            Dict with evaluation metrics
        """
        from ultralytics import YOLO

        logger.info(f"Evaluating model: {model_path}")

        model = YOLO(str(model_path))
        results = model.val(data=str(dataset_yaml))

        metrics = {
            "mAP50": results.box.map50,
            "mAP50-95": results.box.map,
            "precision": results.box.mp,
            "recall": results.box.mr,
        }

        logger.info(f"Evaluation results: mAP50={metrics['mAP50']:.3f}, mAP50-95={metrics['mAP50-95']:.3f}")

        return metrics

    def export_model(
        self,
        model_path: Path,
        output_path: Optional[Path] = None,
        format: str = "pt",
    ) -> Path:
        """Export trained model.

        Args:
            model_path: Path to trained model
            output_path: Destination path (defaults to models/stamp_detector.pt)
            format: Export format (pt, onnx, torchscript, etc.)

        Returns:
            Path to exported model
        """
        settings = get_settings()

        if output_path is None:
            output_path = Path(settings.YOLO_MODEL_PATH).parent / "stamp_detector.pt"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "pt":
            # Just copy the model
            shutil.copy2(model_path, output_path)
            logger.info(f"Exported model to {output_path}")
        else:
            # Use YOLO export for other formats
            from ultralytics import YOLO

            model = YOLO(str(model_path))
            exported = model.export(format=format)
            output_path = Path(exported)
            logger.info(f"Exported model to {output_path} ({format} format)")

        return output_path

    def predict_test(self, model_path: Path, image_path: Path) -> dict:
        """Run prediction on a test image.

        Args:
            model_path: Path to trained model
            image_path: Path to test image

        Returns:
            Dict with prediction results
        """
        from ultralytics import YOLO

        model = YOLO(str(model_path))
        results = model(str(image_path), verbose=False)

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    confidence = float(box.conf[0])
                    detections.append({
                        "bbox": [x1, y1, x2, y2],
                        "confidence": confidence,
                        "class": "stamp",
                    })

        return {
            "image": str(image_path),
            "detections": detections,
            "count": len(detections),
        }


def quick_train(
    dataset_dir: Path,
    epochs: int = 50,
    model_size: str = "n",
) -> TrainingResult:
    """Quick training with sensible defaults.

    Args:
        dataset_dir: Directory containing dataset.yaml
        epochs: Number of training epochs
        model_size: Model size (n/s/m/l/x)

    Returns:
        TrainingResult
    """
    dataset_yaml = dataset_dir / "dataset.yaml"

    if not dataset_yaml.exists():
        raise FileNotFoundError(f"Dataset config not found: {dataset_yaml}")

    config = TrainingConfig(
        dataset_yaml=dataset_yaml,
        base_model=f"yolov8{model_size}.pt",
        epochs=epochs,
    )

    trainer = StampTrainer(config)
    return trainer.train()
