"""Stamp identification pipeline orchestration.

Coordinates the full identification workflow:
1. Image capture (camera or file)
2. Stamp detection (YOLO)
3. Description generation (Groq vision)
4. Similarity search (RAG)
5. Result handling
"""

import asyncio
import base64
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from src.core.config import get_settings
from src.core.errors import IdentificationError
from src.rag.search import IdentificationResult, MatchConfidence, RAGSearcher
from src.vision.camera import CameraCapture, CapturedImage, load_image_file
from src.vision.describer import StampDescriber
from src.vision.detector import DetectedStamp, DetectionResult, SimpleStampDetector, StampDetector

logger = logging.getLogger(__name__)


@dataclass
class StampIdentification:
    """Result of identifying a single detected stamp."""

    stamp: DetectedStamp
    description: str
    rag_result: IdentificationResult
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """Check if identification succeeded."""
        return self.error is None and self.rag_result.has_match

    @property
    def confidence(self) -> MatchConfidence:
        """Get match confidence level."""
        return self.rag_result.confidence

    @property
    def is_auto_match(self) -> bool:
        """Check if this is an auto-accept match."""
        return self.confidence == MatchConfidence.AUTO_ACCEPT


@dataclass
class IdentificationBatch:
    """Result of identifying multiple stamps from an image."""

    source_image: CapturedImage
    detection_result: DetectionResult
    identifications: list[StampIdentification] = field(default_factory=list)

    @property
    def total_detected(self) -> int:
        """Total number of stamps detected."""
        return self.detection_result.count

    @property
    def total_identified(self) -> int:
        """Number of stamps successfully identified."""
        return sum(1 for i in self.identifications if i.is_success)

    @property
    def auto_matches(self) -> list[StampIdentification]:
        """Get stamps with auto-accept matches."""
        return [i for i in self.identifications if i.is_auto_match]

    @property
    def review_needed(self) -> list[StampIdentification]:
        """Get stamps needing user review."""
        return [
            i
            for i in self.identifications
            if i.confidence == MatchConfidence.REVIEW
        ]

    @property
    def no_matches(self) -> list[StampIdentification]:
        """Get stamps with no matches."""
        return [
            i
            for i in self.identifications
            if i.confidence == MatchConfidence.NO_MATCH
        ]


class StampIdentifier:
    """Orchestrates the stamp identification pipeline."""

    def __init__(
        self,
        detector: Optional[StampDetector | SimpleStampDetector] = None,
        describer: Optional[StampDescriber] = None,
        searcher: Optional[RAGSearcher] = None,
        detector_type: str = "auto",
    ):
        """Initialize the identifier.

        Args:
            detector: Detector instance (creates new based on detector_type if not provided)
            describer: StampDescriber instance (creates new if not provided)
            searcher: RAGSearcher instance (creates new if not provided)
            detector_type: Detection method - "yolo", "contour", or "auto"
        """
        self.detector = detector
        self.describer = describer
        self.searcher = searcher
        self.detector_type = detector_type
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Lazy initialize components."""
        if self._initialized:
            return

        if self.detector is None:
            if self.detector_type == "contour":
                self.detector = SimpleStampDetector()
            else:
                # "yolo" or "auto" - use YOLO with fallback
                self.detector = StampDetector()
        if self.describer is None:
            self.describer = StampDescriber()
        if self.searcher is None:
            self.searcher = RAGSearcher()

        self._initialized = True

    async def identify_image(
        self,
        image: CapturedImage,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> IdentificationBatch:
        """Identify all stamps in an image.

        Args:
            image: CapturedImage to process
            progress_callback: Optional callback(current, total, message) for progress

        Returns:
            IdentificationBatch with results for all stamps

        Raises:
            IdentificationError: If identification fails
        """
        self._ensure_initialized()

        logger.info(f"Starting identification for {image.source}")

        try:
            # Step 1: Detect stamps
            if progress_callback:
                progress_callback(0, 0, "Detecting stamps...")

            detection_result = self.detector.detect(image)

            if detection_result.count == 0:
                logger.info("No stamps detected in image")
                return IdentificationBatch(
                    source_image=image,
                    detection_result=detection_result,
                )

            logger.info(f"Detected {detection_result.count} stamps")

            # Step 2: Process each detected stamp
            batch = IdentificationBatch(
                source_image=image,
                detection_result=detection_result,
            )

            total = detection_result.count

            for idx, stamp in enumerate(detection_result.stamps):
                if progress_callback:
                    progress_callback(idx + 1, total, f"Processing stamp {idx + 1}/{total}")

                identification = await self._identify_stamp(stamp)
                batch.identifications.append(identification)

            logger.info(
                f"Identification complete: {batch.total_identified}/{batch.total_detected} identified"
            )

            return batch

        except Exception as e:
            error_msg = f"Identification failed: {e}"
            logger.error(error_msg)
            raise IdentificationError(error_msg) from e

    async def _identify_stamp(self, stamp: DetectedStamp) -> StampIdentification:
        """Identify a single detected stamp.

        Args:
            stamp: DetectedStamp to identify

        Returns:
            StampIdentification with results
        """
        logger.debug(f" * _identify_stamp > Processing stamp {stamp.index}")

        try:
            # Generate description via Groq vision
            image_bytes = stamp.to_bytes(format="JPEG")
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            description = await self.describer.describe_from_base64(
                image_base64, "image/jpeg"
            )

            logger.debug(f"    -> Description: {description[:100]}...")

            # Search RAG for matches
            rag_result = await self.searcher.identify_async(
                description=description,
                top_k=3,
            )

            return StampIdentification(
                stamp=stamp,
                description=description,
                rag_result=rag_result,
            )

        except Exception as e:
            logger.error(f"Failed to identify stamp {stamp.index}: {e}")
            # Return error result
            return StampIdentification(
                stamp=stamp,
                description="",
                rag_result=IdentificationResult(
                    query_description="",
                    top_matches=[],
                    confidence=MatchConfidence.NO_MATCH,
                ),
                error=str(e),
            )

    async def identify_from_camera(
        self,
        camera_index: Optional[int] = None,
        use_preview: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Optional[IdentificationBatch]:
        """Capture from camera and identify stamps.

        Args:
            camera_index: Camera device index (defaults to settings)
            use_preview: Show preview window for capture
            progress_callback: Optional callback for progress updates

        Returns:
            IdentificationBatch if successful, None if cancelled

        Raises:
            IdentificationError: If capture or identification fails
        """
        self._ensure_initialized()

        try:
            with CameraCapture(camera_index) as camera:
                if use_preview:
                    image = camera.capture_with_preview()
                    if image is None:
                        logger.info("Camera capture cancelled by user")
                        return None
                else:
                    image = camera.capture()

                return await self.identify_image(image, progress_callback)

        except Exception as e:
            raise IdentificationError(f"Camera identification failed: {e}") from e

    async def identify_from_file(
        self,
        path: Path,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> IdentificationBatch:
        """Load image file and identify stamps.

        Args:
            path: Path to image file
            progress_callback: Optional callback for progress updates

        Returns:
            IdentificationBatch with results

        Raises:
            IdentificationError: If loading or identification fails
        """
        self._ensure_initialized()

        try:
            image = load_image_file(path)
            return await self.identify_image(image, progress_callback)

        except Exception as e:
            raise IdentificationError(f"File identification failed: {e}") from e

    def verify_setup(self) -> dict[str, bool]:
        """Verify all components are properly configured.

        Returns:
            Dict mapping component name to ready status
        """
        status = {
            "YOLO model": False,
            "Groq API": False,
            "RAG search": False,
        }

        # Check YOLO
        try:
            settings = get_settings()
            yolo_path = Path(settings.YOLO_MODEL_PATH)
            # Model can be auto-downloaded, so just check if path is configured
            status["YOLO model"] = True
        except Exception as e:
            logger.debug(f"YOLO check failed: {e}")

        # Check Groq
        try:
            settings = get_settings()
            status["Groq API"] = bool(settings.GROQ_API_KEY)
        except Exception as e:
            logger.debug(f"Groq check failed: {e}")

        # Check RAG
        try:
            settings = get_settings()
            status["RAG search"] = bool(
                settings.SUPABASE_URL
                and settings.SUPABASE_KEY
                and settings.OPENAI_API_KEY
            )
        except Exception as e:
            logger.debug(f"RAG check failed: {e}")

        return status


def run_identification_sync(
    source: str | Path,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> IdentificationBatch:
    """Synchronous wrapper for identification.

    Args:
        source: "camera" for camera capture, or path to image file
        progress_callback: Optional callback for progress updates

    Returns:
        IdentificationBatch with results
    """
    identifier = StampIdentifier()

    async def _run():
        if source == "camera":
            result = await identifier.identify_from_camera(
                progress_callback=progress_callback
            )
            if result is None:
                raise IdentificationError("Camera capture cancelled")
            return result
        else:
            return await identifier.identify_from_file(
                Path(source),
                progress_callback=progress_callback,
            )

    return asyncio.run(_run())
