"""YOLO training module for stamp detection.

.. deprecated::
    This module is DEPRECATED. The project moved from local YOLO detection
    to Vision LLM-based detection (Groq/Claude) for better reliability with
    variable input quality. See src/vision/vision_detector.py for the current
    detection implementation.

    This module may be removed in a future version. Do not add new dependencies
    on these components.

Modules (deprecated)
--------------------
dataset.py
    StampDataset: Dataset preparation for YOLO training. Converts labeled
    images to YOLO format with train/val splits.

labelstudio.py
    Label Studio integration for stamp annotation export.

trainer.py
    StampTrainer: YOLO model training wrapper for fine-tuning on stamp data.

Historical Context
------------------
This approach was explored to create a custom stamp detector trained on
labeled album page images. While the model could be trained, inference
results were inconsistent across different album backgrounds, lighting
conditions, and stamp orientations. The Vision LLM approach provides more
robust detection without requiring model training infrastructure.
"""

from src.training.dataset import StampDataset, prepare_dataset
from src.training.trainer import StampTrainer

__all__ = ["StampDataset", "prepare_dataset", "StampTrainer"]
