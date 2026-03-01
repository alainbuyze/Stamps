"""Stamp identification pipeline orchestration.

Coordinates the full identification workflow:
1. Image capture (camera or file)
2. Stage 1: Two-stage detection (polygon + classifier + YOLO fallback)
3. Stage 2: Description generation (Groq vision)
4. Stage 3: Similarity search (RAG)
5. Session persistence and feedback
"""

import asyncio
import base64
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from src.core.config import get_settings
from src.core.errors import IdentificationError
from src.feedback.models import DetectionFeedback, ScanSession
from src.feedback.session_manager import SessionManager
from src.rag.search import IdentificationResult, MatchConfidence, RAGSearcher
from src.vision.camera import CameraCapture, CapturedImage, load_image_file
from src.vision.describer import StampDescriber
from src.vision.detection.pipeline import (
    DetectionPipeline,
    DetectedStamp,
    create_pipeline_from_env,
)

logger = logging.getLogger(__name__)


@dataclass
class StampIdentification:
    """Result of identifying a single detected stamp (for backwards compatibility)."""

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
    """Result of identifying multiple stamps from an image (for backwards compatibility)."""

    source_image: CapturedImage
    session: ScanSession
    identifications: list[StampIdentification] = field(default_factory=list)

    @property
    def total_detected(self) -> int:
        """Total number of stamps detected."""
        return self.session.summary["total_shapes"]

    @property
    def total_identified(self) -> int:
        """Number of stamps successfully identified."""
        return self.session.summary["identified"]

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

    # For backwards compatibility with CLI
    @property
    def detection_result(self):
        """Backwards compatibility shim."""
        return self


class StampIdentifier:
    """Orchestrates the stamp identification pipeline with two-stage detection."""

    def __init__(
        self,
        pipeline: Optional[DetectionPipeline] = None,
        describer: Optional[StampDescriber] = None,
        searcher: Optional[RAGSearcher] = None,
        session_manager: Optional[SessionManager] = None,
        detector_type: str = "auto",  # Kept for backwards compatibility
    ):
        """Initialize the identifier.

        Args:
            pipeline: DetectionPipeline instance (creates from env if not provided)
            describer: StampDescriber instance (creates new if not provided)
            searcher: RAGSearcher instance (creates new if not provided)
            session_manager: SessionManager instance (creates new if not provided)
            detector_type: Detection method - kept for backwards compatibility
        """
        self.pipeline = pipeline
        self.describer = describer
        self.searcher = searcher
        self.session_manager = session_manager
        self.detector_type = detector_type
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Lazy initialize components."""
        if self._initialized:
            return

        settings = get_settings()

        if self.pipeline is None:
            self.pipeline = create_pipeline_from_env()
        if self.describer is None:
            self.describer = StampDescriber()
        if self.searcher is None:
            self.searcher = RAGSearcher()
        if self.session_manager is None:
            self.session_manager = SessionManager(
                output_dir=settings.feedback_output_path,
                save_original=settings.FEEDBACK_SAVE_ORIGINAL,
                save_annotated=settings.FEEDBACK_SAVE_ANNOTATED,
                save_crops=settings.FEEDBACK_SAVE_CROPS,
            )

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
            # Step 1: Create session
            session = ScanSession(
                source="file" if image.source != "camera" else "camera",
                source_path=image.source if image.source != "camera" else None,
                original_image=image.frame,
            )

            # Step 2: Detect stamps using two-stage pipeline
            if progress_callback:
                progress_callback(0, 0, "Detecting stamps...")

            accepted_stamps, rejected_stamps = self.pipeline.detect_stamps(image.frame)

            if len(accepted_stamps) == 0 and len(rejected_stamps) == 0:
                logger.info("No stamps detected in image")
                return IdentificationBatch(
                    source_image=image,
                    session=session,
                )

            logger.info(f"Detected {len(accepted_stamps)} stamps, {len(rejected_stamps)} rejected")

            # Step 3: Add rejected stamps to session (no RAG search needed)
            for stamp in rejected_stamps:
                feedback = self._create_feedback_from_stamp(stamp, searched=False)
                session.detections.append(feedback)

            # Step 4: Process accepted stamps through RAG
            identifications = []
            total = len(accepted_stamps)

            for idx, stamp in enumerate(accepted_stamps):
                if progress_callback:
                    progress_callback(idx + 1, total, f"Identifying stamp {idx + 1}/{total}")

                feedback, identification = await self._identify_stamp(stamp)
                session.detections.append(feedback)
                if identification:
                    identifications.append(identification)

            # Step 5: Save session
            session_path = self.session_manager.save_session(session)
            logger.info(f"Session saved to {session_path}")

            logger.info(
                f"Identification complete: {session.summary['identified']}/{total} identified"
            )

            return IdentificationBatch(
                source_image=image,
                session=session,
                identifications=identifications,
            )

        except Exception as e:
            error_msg = f"Identification failed: {e}"
            logger.error(error_msg)
            raise IdentificationError(error_msg) from e

    def _create_feedback_from_stamp(
        self,
        stamp: DetectedStamp,
        searched: bool = False,
    ) -> DetectionFeedback:
        """Convert DetectedStamp to DetectionFeedback."""
        return DetectionFeedback(
            detection_id=stamp.detection_id,
            shape_type=stamp.shape_type,
            bounding_box=stamp.bounding_box,
            vertices=stamp.vertices,
            stage_1b_passed=stamp.classifier_passed,
            stage_1b_confidence=stamp.classifier_confidence,
            stage_1b_reason=stamp.classifier_reason,
            stage_1b_details=stamp.classifier_details,
            stage_2_searched=searched,
            cropped_image=stamp.cropped_image,
        )

    async def _identify_stamp(
        self,
        stamp: DetectedStamp,
    ) -> tuple[DetectionFeedback, Optional[StampIdentification]]:
        """Identify a single detected stamp.

        Args:
            stamp: DetectedStamp to identify

        Returns:
            Tuple of (DetectionFeedback, StampIdentification or None)
        """
        logger.debug(f" * _identify_stamp > Processing stamp {stamp.detection_id}")

        feedback = self._create_feedback_from_stamp(stamp, searched=True)

        try:
            # Generate description via Groq vision
            from io import BytesIO
            from PIL import Image
            import cv2

            # Convert crop to bytes
            rgb_frame = cv2.cvtColor(stamp.cropped_image, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            buffer = BytesIO()
            pil_img.save(buffer, format="JPEG")
            image_bytes = buffer.getvalue()
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

            # Update feedback with RAG results
            feedback.rag_match_found = rag_result.has_match
            if rag_result.top_matches:
                feedback.rag_top_match = rag_result.top_matches[0].entry.colnect_id
                feedback.rag_confidence = rag_result.top_matches[0].score
                feedback.rag_top_3 = [
                    {
                        "colnect_id": m.entry.colnect_id,
                        "score": m.score,
                        "country": m.entry.country,
                        "year": m.entry.year,
                    }
                    for m in rag_result.top_matches
                ]

            identification = StampIdentification(
                stamp=stamp,
                description=description,
                rag_result=rag_result,
            )

            return feedback, identification

        except Exception as e:
            logger.error(f"Failed to identify stamp {stamp.detection_id}: {e}")
            # Return error feedback
            feedback.stage_1b_reason = f"identification_error: {str(e)}"
            return feedback, None

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
            "Detection pipeline": False,
            "Groq API": False,
            "RAG search": False,
        }

        # Check detection pipeline
        try:
            # Pipeline should always be available (uses built-in CV)
            status["Detection pipeline"] = True
        except Exception as e:
            logger.debug(f"Detection pipeline check failed: {e}")

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
