"""OpenCV camera capture for stamp identification.

Provides functionality to capture single frames from a webcam
for stamp detection and identification.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image

from src.core.config import get_settings
from src.core.errors import CameraError

logger = logging.getLogger(__name__)


@dataclass
class CapturedImage:
    """Container for a captured image."""

    frame: np.ndarray
    width: int
    height: int
    source: str

    @property
    def pil_image(self) -> Image.Image:
        """Convert to PIL Image (RGB)."""
        rgb_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_frame)

    def save(self, path: Path) -> None:
        """Save image to file.

        Args:
            path: Output file path
        """
        cv2.imwrite(str(path), self.frame)
        logger.debug(f"Saved image to {path}")

    def to_bytes(self, format: str = "JPEG") -> bytes:
        """Convert to bytes for API upload.

        Args:
            format: Image format (JPEG, PNG)

        Returns:
            Image bytes
        """
        from io import BytesIO

        pil_img = self.pil_image
        buffer = BytesIO()
        pil_img.save(buffer, format=format)
        return buffer.getvalue()


class CameraCapture:
    """Captures images from webcam using OpenCV."""

    def __init__(self, camera_index: Optional[int] = None):
        """Initialize camera capture.

        Args:
            camera_index: Camera device index (defaults to settings)
        """
        settings = get_settings()
        self.camera_index = camera_index if camera_index is not None else settings.CAMERA_INDEX
        self._cap: Optional[cv2.VideoCapture] = None

    def __enter__(self) -> "CameraCapture":
        """Context manager entry - open camera."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close camera."""
        self.close()

    def open(self) -> None:
        """Open the camera device.

        Raises:
            CameraError: If camera cannot be opened
        """
        logger.debug(f" * CameraCapture.open > Opening camera {self.camera_index}")

        self._cap = cv2.VideoCapture(self.camera_index)

        if not self._cap.isOpened():
            raise CameraError(
                f"Could not open camera at index {self.camera_index}. "
                "Check if camera is connected and not in use by another application."
            )

        # Get camera properties
        width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.debug(f"    -> Camera opened: {width}x{height}")

    def close(self) -> None:
        """Release the camera device."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.debug("    -> Camera released")

    def is_open(self) -> bool:
        """Check if camera is open."""
        return self._cap is not None and self._cap.isOpened()

    def capture(self) -> CapturedImage:
        """Capture a single frame from the camera.

        Returns:
            CapturedImage containing the frame

        Raises:
            CameraError: If capture fails
        """
        if not self.is_open():
            raise CameraError("Camera not opened. Call open() first or use context manager.")

        logger.debug(" * CameraCapture.capture > Capturing frame")

        # Read frame
        ret, frame = self._cap.read()

        if not ret or frame is None:
            raise CameraError("Failed to capture frame from camera")

        height, width = frame.shape[:2]
        logger.debug(f"    -> Captured {width}x{height} frame")

        return CapturedImage(
            frame=frame,
            width=width,
            height=height,
            source=f"camera:{self.camera_index}",
        )

    def capture_with_preview(
        self,
        window_name: str = "Stamp Capture",
        instructions: str = "Press SPACE to capture, ESC to cancel",
    ) -> Optional[CapturedImage]:
        """Show preview window and capture on keypress.

        Args:
            window_name: Name for preview window
            instructions: Instructions to show

        Returns:
            CapturedImage if captured, None if cancelled

        Raises:
            CameraError: If capture fails
        """
        if not self.is_open():
            raise CameraError("Camera not opened. Call open() first or use context manager.")

        logger.info(f"Starting preview: {instructions}")

        try:
            while True:
                ret, frame = self._cap.read()
                if not ret:
                    raise CameraError("Failed to read frame during preview")

                # Add instruction text overlay
                cv2.putText(
                    frame,
                    instructions,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

                cv2.imshow(window_name, frame)

                key = cv2.waitKey(1) & 0xFF

                if key == 27:  # ESC
                    logger.info("Preview cancelled by user")
                    cv2.destroyAllWindows()
                    return None
                elif key == 32:  # SPACE
                    height, width = frame.shape[:2]
                    logger.info(f"Captured {width}x{height} frame")
                    cv2.destroyAllWindows()
                    return CapturedImage(
                        frame=frame,
                        width=width,
                        height=height,
                        source=f"camera:{self.camera_index}",
                    )

        except Exception as e:
            cv2.destroyAllWindows()
            raise CameraError(f"Preview capture failed: {e}") from e


def load_image_file(path: Path) -> CapturedImage:
    """Load an image from file.

    Args:
        path: Path to image file

    Returns:
        CapturedImage containing the loaded image

    Raises:
        CameraError: If file cannot be loaded
    """
    logger.debug(f" * load_image_file > Loading {path}")

    if not path.exists():
        raise CameraError(f"Image file not found: {path}")

    frame = cv2.imread(str(path))

    if frame is None:
        raise CameraError(f"Failed to load image: {path}")

    height, width = frame.shape[:2]
    logger.debug(f"    -> Loaded {width}x{height} image")

    return CapturedImage(
        frame=frame,
        width=width,
        height=height,
        source=str(path),
    )


def list_cameras(max_index: int = 5) -> list[int]:
    """List available camera devices.

    Args:
        max_index: Maximum camera index to check

    Returns:
        List of available camera indices
    """
    available = []

    for idx in range(max_index):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            available.append(idx)
            cap.release()

    logger.debug(f"Found {len(available)} cameras: {available}")
    return available
