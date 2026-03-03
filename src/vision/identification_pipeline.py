"""Stamp identification pipeline with single and multi-stamp modes.

Orchestrates the full flow from image capture to RAG identification.
Supports inspection of all intermediate steps.

Classes access settings directly via get_settings() - no config parameters.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Any
import json
import uuid

import cv2
import numpy as np

from src.core.config import get_settings
from .vision_detector import (
    VisionDetector,
    DetectionResult,
    VisionDetection,
    GROQ,
    CLAUDE_HAIKU,
    CLAUDE_SONNET,
)
from .preprocessing import PreprocessingStrategy, PreprocessedImage

logger = logging.getLogger(__name__)


class IdentificationMode(Enum):
    """Operation modes for identification."""
    SINGLE_STAMP = "single"     # Image contains one stamp, skip detection
    MULTI_STAMP = "multi"       # Album page with multiple stamps
    AUTO = "auto"               # Auto-detect based on image analysis


@dataclass
class RAGMatch:
    """A match from the RAG database."""
    
    colnect_id: str
    colnect_url: str
    similarity_score: float
    description: str
    country: Optional[str] = None
    year: Optional[int] = None
    image_url: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "colnect_id": self.colnect_id,
            "colnect_url": self.colnect_url,
            "similarity_score": self.similarity_score,
            "description": self.description[:200] + "..." if len(self.description) > 200 else self.description,
            "country": self.country,
            "year": self.year,
        }


@dataclass
class StampIdentification:
    """Complete identification result for a single stamp."""
    
    # Identity
    identification_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # Source info
    mode: IdentificationMode = IdentificationMode.MULTI_STAMP
    detection: Optional[VisionDetection] = None  # None for single-stamp mode
    
    # Images (for inspection)
    original_crop: Optional[np.ndarray] = None
    preprocessed_crop: Optional[np.ndarray] = None
    
    # Description generation
    description: Optional[str] = None
    description_provider: Optional[str] = None
    description_latency_ms: int = 0
    description_error: Optional[str] = None
    
    # RAG results
    rag_searched: bool = False
    rag_matches: list[RAGMatch] = field(default_factory=list)
    rag_latency_ms: int = 0
    rag_error: Optional[str] = None
    
    # Final result
    top_match: Optional[RAGMatch] = None
    auto_accepted: bool = False
    user_confirmed: Optional[bool] = None
    
    # Thresholds used
    auto_accept_threshold: float = 0.9
    min_match_threshold: float = 0.5
    
    @property
    def status(self) -> str:
        """Get identification status."""
        if not self.rag_searched:
            return "pending"
        if self.top_match is None:
            return "no_match"
        if self.auto_accepted or self.user_confirmed:
            return "identified"
        return "needs_review"
    
    @property
    def best_score(self) -> float:
        """Get best match score."""
        if self.top_match:
            return self.top_match.similarity_score
        return 0.0
    
    def to_dict(self) -> dict:
        return {
            "identification_id": self.identification_id,
            "mode": self.mode.value,
            "status": self.status,
            "description": self.description,
            "description_provider": self.description_provider,
            "description_latency_ms": self.description_latency_ms,
            "rag_searched": self.rag_searched,
            "rag_match_count": len(self.rag_matches),
            "rag_latency_ms": self.rag_latency_ms,
            "top_match": self.top_match.to_dict() if self.top_match else None,
            "top_3_matches": [m.to_dict() for m in self.rag_matches[:3]],
            "auto_accepted": self.auto_accepted,
            "user_confirmed": self.user_confirmed,
            "best_score": self.best_score,
        }


@dataclass
class IdentificationSession:
    """Complete session with all stamps and inspection data."""
    
    session_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:6])
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Mode and source
    mode: IdentificationMode = IdentificationMode.AUTO
    source: str = "camera"  # camera | file
    source_path: Optional[str] = None
    
    # Original image
    original_image: Optional[np.ndarray] = None
    
    # Detection results (multi-stamp mode)
    detection_result: Optional[DetectionResult] = None
    
    # All identifications
    identifications: list[StampIdentification] = field(default_factory=list)
    
    # Timing
    total_latency_ms: int = 0
    
    @property
    def summary(self) -> dict:
        """Get summary statistics."""
        statuses = [i.status for i in self.identifications]
        return {
            "total_stamps": len(self.identifications),
            "identified": statuses.count("identified"),
            "needs_review": statuses.count("needs_review"),
            "no_match": statuses.count("no_match"),
            "pending": statuses.count("pending"),
            "mode": self.mode.value,
        }
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "mode": self.mode.value,
            "source": self.source,
            "summary": self.summary,
            "detection_result": self.detection_result.to_dict() if self.detection_result else None,
            "identifications": [i.to_dict() for i in self.identifications],
            "total_latency_ms": self.total_latency_ms,
        }


class InspectionManager:
    """Manages saving and organizing inspection artifacts.

    Uses inspection_path from settings directly.
    """

    def __init__(self):
        settings = get_settings()
        self.base_dir = settings.inspection_path
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def create_session_dir(self, session_id: str) -> Path:
        """Create directory for session inspection data."""
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirs
        (session_dir / "crops").mkdir(exist_ok=True)
        (session_dir / "preprocessed").mkdir(exist_ok=True)
        (session_dir / "annotated").mkdir(exist_ok=True)
        
        return session_dir
    
    def save_image(
        self,
        image: np.ndarray,
        session_dir: Path,
        name: str,
        subdir: Optional[str] = None,
    ) -> Path:
        """Save an image with optional subdirectory."""
        if subdir:
            path = session_dir / subdir / f"{name}.jpg"
        else:
            path = session_dir / f"{name}.jpg"
        
        cv2.imwrite(str(path), image)
        return path
    
    def save_json(
        self,
        data: dict,
        session_dir: Path,
        name: str,
    ) -> Path:
        """Save JSON data."""
        path = session_dir / f"{name}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path
    
    def create_inspection_report(
        self,
        session: IdentificationSession,
        session_dir: Path,
    ) -> Path:
        """Create detailed inspection report."""
        report = {
            "session": session.to_dict(),
            "files": {
                "original": "original.jpg",
                "annotated": "annotated/detection.jpg",
                "crops": [f"crops/{i.identification_id}.jpg" for i in session.identifications],
            },
            "inspection_notes": {
                "preprocessing_strategy": session.detection_result.preprocessed_image.strategy.value if session.detection_result and session.detection_result.preprocessed_image else "N/A",
                "detection_provider": session.detection_result.provider_used if session.detection_result and session.detection_result.provider_used else "N/A",
            }
        }
        
        return self.save_json(report, session_dir, "inspection_report")


class IdentificationPipeline:
    """
    Main pipeline for stamp identification.

    Supports:
    - Single stamp mode: image is one stamp, skip detection, go directly to RAG
    - Multi stamp mode: detect stamps first, then identify each
    - Auto mode: analyze image to determine mode

    Full inspection capabilities for debugging and tuning.
    Accesses all configuration directly via get_settings().
    """

    def __init__(
        self,
        vision_detector: Optional[VisionDetector] = None,
        groq_client: Optional[Any] = None,
        rag_searcher: Optional[Any] = None,
    ):
        self.vision_detector = vision_detector
        self.groq_client = groq_client
        self.rag_searcher = rag_searcher

        # Access settings directly
        settings = get_settings()
        self.inspection = InspectionManager()

        logger.debug(f"IdentificationPipeline initialized, default_mode={settings.IDENTIFICATION_DEFAULT_MODE}")
    
    def identify(
        self,
        image: np.ndarray,
        mode: Optional[IdentificationMode] = None,
        source: str = "camera",
        source_path: Optional[str] = None,
    ) -> IdentificationSession:
        """
        Run full identification pipeline.

        Args:
            image: Input image (BGR)
            mode: Operation mode (single/multi/auto)
            source: Source type (camera/file)
            source_path: Path if from file

        Returns:
            IdentificationSession with all results and inspection data
        """
        import time

        settings = get_settings()
        start_time = time.time()

        mode = mode or IdentificationMode(settings.IDENTIFICATION_DEFAULT_MODE)

        # Create session
        session = IdentificationSession(
            mode=mode,
            source=source,
            source_path=source_path,
            original_image=image.copy(),
        )

        logger.info(f"Starting identification session {session.session_id}, mode={mode.value}")

        # Create inspection directory
        session_dir = self.inspection.create_session_dir(session.session_id)

        # Save original
        if settings.INSPECTION_SAVE_INTERMEDIATES:
            self.inspection.save_image(image, session_dir, "original")

        # Determine actual mode
        if mode == IdentificationMode.AUTO:
            mode = self._auto_detect_mode(image)
            session.mode = mode
            logger.info(f"Auto-detected mode: {mode.value}")

        # Process based on mode
        if mode == IdentificationMode.SINGLE_STAMP:
            identification = self._process_single_stamp(image, session_dir)
            session.identifications = [identification]
        else:
            # Multi-stamp: detect first
            if self.vision_detector is None:
                raise ValueError("VisionDetector required for multi-stamp mode")

            detection_result = self.vision_detector.detect(
                image,
                inspection_id=session.session_id,
            )
            session.detection_result = detection_result

            # Save detection annotated image
            if settings.INSPECTION_SAVE_INTERMEDIATES:
                annotated = self._create_detection_overlay(image, detection_result)
                self.inspection.save_image(annotated, session_dir, "detection", "annotated")

            # Process each detection
            for det in detection_result.detections:
                crop = self._extract_crop(image, det)
                identification = self._process_stamp_crop(
                    crop,
                    det,
                    session_dir,
                )
                session.identifications.append(identification)

        # Calculate total time
        session.total_latency_ms = int((time.time() - start_time) * 1000)

        # Save final inspection report
        if settings.INSPECTION_SAVE_INTERMEDIATES:
            self.inspection.save_json(session.to_dict(), session_dir, "session")
            self.inspection.create_inspection_report(session, session_dir)

            # Create final annotated image
            final_annotated = self._create_final_overlay(image, session)
            self.inspection.save_image(final_annotated, session_dir, "final_result", "annotated")

        logger.info(f"Session complete: {session.summary}")
        return session
    
    def identify_single(
        self,
        image: np.ndarray,
        source: str = "camera",
        source_path: Optional[str] = None,
    ) -> IdentificationSession:
        """Convenience method for single-stamp identification."""
        return self.identify(
            image,
            mode=IdentificationMode.SINGLE_STAMP,
            source=source,
            source_path=source_path,
        )
    
    def identify_album_page(
        self,
        image: np.ndarray,
        source: str = "camera",
        source_path: Optional[str] = None,
    ) -> IdentificationSession:
        """Convenience method for album page identification."""
        return self.identify(
            image,
            mode=IdentificationMode.MULTI_STAMP,
            source=source,
            source_path=source_path,
        )
    
    def _auto_detect_mode(self, image: np.ndarray) -> IdentificationMode:
        """
        Auto-detect if image contains single stamp or multiple.

        Uses simple heuristics - can be enhanced later.
        """
        h, w = image.shape[:2]
        aspect_ratio = w / h if h > 0 else 1

        # Heuristic: single stamps typically have aspect ratio 0.5-2.0
        # Album pages are usually wider
        if 0.4 <= aspect_ratio <= 2.5 and max(h, w) < 1000:
            # Small-ish image with stamp-like aspect ratio
            logger.debug(f"Auto-detect: likely single stamp (aspect={aspect_ratio:.2f})")
            return IdentificationMode.SINGLE_STAMP

        return IdentificationMode.MULTI_STAMP
    
    def _process_single_stamp(
        self,
        image: np.ndarray,
        session_dir: Path,
    ) -> StampIdentification:
        """Process a single-stamp image directly to RAG."""
        settings = get_settings()
        identification = StampIdentification(
            mode=IdentificationMode.SINGLE_STAMP,
            original_crop=image.copy(),
        )

        # Save crop
        if settings.INSPECTION_SAVE_INTERMEDIATES:
            self.inspection.save_image(
                image, session_dir,
                identification.identification_id,
                "crops"
            )

        # Generate description
        self._generate_description(identification, image)

        # Search RAG
        if identification.description:
            self._search_rag(identification)

        return identification

    def _process_stamp_crop(
        self,
        crop: np.ndarray,
        detection: VisionDetection,
        session_dir: Path,
    ) -> StampIdentification:
        """Process a detected stamp crop."""
        settings = get_settings()
        identification = StampIdentification(
            mode=IdentificationMode.MULTI_STAMP,
            detection=detection,
            original_crop=crop.copy(),
        )

        # Save crop
        if settings.INSPECTION_SAVE_INTERMEDIATES:
            self.inspection.save_image(
                crop, session_dir,
                identification.identification_id,
                "crops"
            )

        # Generate description
        self._generate_description(identification, crop)

        # Search RAG
        if identification.description:
            self._search_rag(identification)

        return identification
    
    def _generate_description(
        self,
        identification: StampIdentification,
        image: np.ndarray,
    ) -> None:
        """Generate description for stamp using vision LLM."""
        import time
        import base64

        settings = get_settings()

        if self.groq_client is None:
            identification.description_error = "Groq client not configured"
            return

        # Encode image
        _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        b64_image = base64.b64encode(buffer).decode('utf-8')

        prompt = self._get_description_prompt()

        start = time.time()
        try:
            response = self.groq_client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
                        }
                    ]
                }],
                max_tokens=500,
                temperature=0.3,
            )

            identification.description = response.choices[0].message.content
            identification.description_provider = "groq"

        except Exception as e:
            identification.description_error = str(e)
            logger.error(f"Description generation failed: {e}")

        identification.description_latency_ms = int((time.time() - start) * 1000)

    def _get_description_prompt(self) -> str:
        """Get the description prompt (can be loaded from file)."""
        settings = get_settings()

        # Try to load from config file
        prompt_path = settings.vision_prompt_path
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')

        # Default prompt
        return """Describe this postage stamp in detail for identification purposes.

Include:
1. Main subject/theme (rocket, satellite, astronaut, scientist, planet, etc.)
2. Colors and visual style
3. Country name if visible
4. Denomination/value if visible
5. Year if visible
6. Any text or inscriptions
7. Special features (perforations, shape, etc.)

Provide a single paragraph description suitable for semantic search."""

    def _search_rag(self, identification: StampIdentification) -> None:
        """Search RAG database for matches."""
        import time

        settings = get_settings()

        if self.rag_searcher is None:
            identification.rag_error = "RAG searcher not configured"
            return

        identification.rag_searched = True
        start = time.time()

        try:
            # Call RAG searcher
            results = self.rag_searcher.search(
                identification.description,
                limit=settings.IDENTIFICATION_MAX_MATCHES,
            )

            # Convert to RAGMatch objects
            for r in results:
                match = RAGMatch(
                    colnect_id=r.get('colnect_id'),
                    colnect_url=r.get('colnect_url'),
                    similarity_score=r.get('similarity', 0),
                    description=r.get('description', ''),
                    country=r.get('country'),
                    year=r.get('year'),
                    image_url=r.get('image_url'),
                )
                identification.rag_matches.append(match)

            # Set top match if above threshold
            if identification.rag_matches:
                top = identification.rag_matches[0]
                if top.similarity_score >= settings.RAG_MATCH_MIN_THRESHOLD:
                    identification.top_match = top

                    # Auto-accept if above threshold
                    if top.similarity_score >= settings.RAG_MATCH_AUTO_THRESHOLD:
                        identification.auto_accepted = True

        except Exception as e:
            identification.rag_error = str(e)
            logger.error(f"RAG search failed: {e}")

        identification.rag_latency_ms = int((time.time() - start) * 1000)
    
    def _extract_crop(
        self,
        image: np.ndarray,
        detection: VisionDetection,
    ) -> np.ndarray:
        """Extract crop from image using detection box."""
        settings = get_settings()

        if detection.box_pixels is None:
            raise ValueError("Detection has no pixel coordinates")

        h, w = image.shape[:2]
        x, y, bw, bh = detection.box_pixels

        # Add padding
        pad_x = int(bw * settings.IDENTIFICATION_CROP_PADDING_PERCENT)
        pad_y = int(bh * settings.IDENTIFICATION_CROP_PADDING_PERCENT)

        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(w, x + bw + pad_x)
        y2 = min(h, y + bh + pad_y)

        return image[y1:y2, x1:x2].copy()
    
    def _create_detection_overlay(
        self,
        image: np.ndarray,
        detection_result: DetectionResult,
    ) -> np.ndarray:
        """Create overlay showing all detections."""
        annotated = image.copy()
        
        for det in detection_result.detections:
            if det.box_pixels is None:
                continue
            
            x, y, w, h = det.box_pixels
            color = (0, 255, 0)  # Green
            
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
            label = f"{det.shape} ({det.confidence})"
            cv2.putText(annotated, label, (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Add provider info
        provider = detection_result.provider_used if detection_result.provider_used else "unknown"
        cv2.putText(annotated, f"Provider: {provider}", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return annotated
    
    def _create_final_overlay(
        self,
        image: np.ndarray,
        session: IdentificationSession,
    ) -> np.ndarray:
        """Create final overlay showing identification results."""
        annotated = image.copy()
        
        colors = {
            "identified": (0, 255, 0),     # Green
            "needs_review": (0, 255, 255), # Yellow
            "no_match": (0, 165, 255),     # Orange
            "pending": (128, 128, 128),    # Gray
        }
        
        for ident in session.identifications:
            if ident.detection is None or ident.detection.box_pixels is None:
                continue
            
            x, y, w, h = ident.detection.box_pixels
            color = colors.get(ident.status, (255, 255, 255))
            
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
            
            # Label with score
            if ident.top_match:
                label = f"{ident.best_score:.0%}"
            else:
                label = ident.status
            cv2.putText(annotated, label, (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Add summary
        summary = session.summary
        text = f"Identified: {summary['identified']} | Review: {summary['needs_review']} | No match: {summary['no_match']}"
        cv2.putText(annotated, text, (10, annotated.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return annotated


def create_pipeline_from_env() -> IdentificationPipeline:
    """Create pipeline with required clients.

    All configuration is accessed directly via get_settings() inside IdentificationPipeline.
    This factory only initializes the API clients and dependent services.
    """
    from .vision_detector import create_vision_detector_from_env
    from .rag_adapter import create_rag_adapter

    settings = get_settings()

    # Create vision detector
    vision_detector = create_vision_detector_from_env()

    # Get Groq client for description generation
    groq_client = None
    if settings.GROQ_API_KEY:
        try:
            from groq import Groq
            groq_client = Groq(api_key=settings.GROQ_API_KEY)
            logger.debug("Groq client initialized for descriptions")
        except ImportError:
            logger.warning("groq package not installed")

    # Create RAG adapter
    rag_searcher = None
    try:
        rag_searcher = create_rag_adapter()
        logger.debug("RAG adapter initialized")
    except Exception as e:
        logger.warning(f"Failed to create RAG adapter: {e}")

    return IdentificationPipeline(
        vision_detector=vision_detector,
        groq_client=groq_client,
        rag_searcher=rag_searcher,
    )
