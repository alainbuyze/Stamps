"""YOLO training module for stamp detection.

Components:
- dataset: Dataset preparation and management
- labelstudio: Label Studio integration for annotation
- trainer: YOLO model training
"""

from src.training.dataset import StampDataset, prepare_dataset
from src.training.trainer import StampTrainer

__all__ = ["StampDataset", "prepare_dataset", "StampTrainer"]
