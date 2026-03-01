"""Manage scan sessions and missed stamps for re-ingestion."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2

from .models import ScanSession, DetectionFeedback
from .visualizer import FeedbackVisualizer

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage scan sessions and missed stamps for re-ingestion."""
    
    def __init__(
        self, 
        output_dir: Path,
        save_original: bool = True,
        save_annotated: bool = True,
        save_crops: bool = True,
    ):
        self.output_dir = Path(output_dir)
        self.sessions_dir = self.output_dir / "sessions"
        self.missed_dir = self.output_dir / "missed_stamps"
        self.resolved_dir = self.output_dir / "resolved"
        
        self.save_original = save_original
        self.save_annotated = save_annotated
        self.save_crops = save_crops
        
        # Create directories
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.missed_dir.mkdir(parents=True, exist_ok=True)
        self.resolved_dir.mkdir(parents=True, exist_ok=True)
        
        self.visualizer = FeedbackVisualizer()
    
    def save_session(self, session: ScanSession) -> Path:
        """
        Save complete session for review.
        
        Creates:
        - sessions/{session_id}/
          ├── annotated.png      # Annotated full image
          ├── original.png       # Original image
          ├── session.json       # Detection details
          └── crops/             # Individual stamp crops
              ├── 001_identified_AU5352.png
              ├── 002_no_match.png
              └── 003_rejected.png
        
        Returns:
            Path to session directory
        """
        session_dir = self.sessions_dir / session.session_id
        session_dir.mkdir(exist_ok=True)
        
        logger.info(f"Saving session to {session_dir}")
        
        # Save original image
        if self.save_original and session.original_image is not None:
            original_path = session_dir / "original.png"
            cv2.imwrite(str(original_path), session.original_image)
            logger.debug(f"Saved original image: {original_path}")
        
        # Generate and save annotated image
        if self.save_annotated and session.original_image is not None:
            try:
                annotated = self.visualizer.annotate_session(session)
                annotated_path = session_dir / "annotated.png"
                cv2.imwrite(str(annotated_path), annotated)
                logger.debug(f"Saved annotated image: {annotated_path}")
            except Exception as e:
                logger.error(f"Failed to save annotated image: {e}")
        
        # Save individual crops
        if self.save_crops:
            crops_dir = session_dir / "crops"
            crops_dir.mkdir(exist_ok=True)
            
            for i, det in enumerate(session.detections):
                if det.cropped_image is not None:
                    # Create descriptive filename
                    suffix = self._get_crop_suffix(det)
                    filename = f"{i+1:03d}_{det.status}_{suffix}.png"
                    crop_path = crops_dir / filename
                    cv2.imwrite(str(crop_path), det.cropped_image)
                    
                    # Also save to missed_stamps for no_match cases
                    if det.status == "no_match":
                        missed_filename = f"{session.session_id}_{i+1:03d}.png"
                        missed_path = self.missed_dir / missed_filename
                        cv2.imwrite(str(missed_path), det.cropped_image)
                        logger.debug(f"Saved missed stamp: {missed_path}")
        
        # Save session JSON
        session_json = self._build_session_json(session)
        json_path = session_dir / "session.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(session_json, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved session JSON: {json_path}")
        
        logger.info(f"Session saved: {session.summary}")
        return session_dir
    
    def _get_crop_suffix(self, det: DetectionFeedback) -> str:
        """Get descriptive suffix for crop filename."""
        if det.status == "identified" and det.rag_top_match:
            # Clean the colnect ID for filename
            return det.rag_top_match.replace("/", "_").replace("\\", "_")[:20]
        elif det.status == "rejected":
            reason = det.stage_1b_reason or "unknown"
            return reason.replace(" ", "_")[:15]
        elif det.status == "no_match":
            return "unmatched"
        return det.shape_type
    
    def _build_session_json(self, session: ScanSession) -> dict:
        """Build JSON-serializable session data."""
        return {
            "session_id": session.session_id,
            "timestamp": session.timestamp.isoformat(),
            "source": session.source,
            "source_path": session.source_path,
            "summary": session.summary,
            "detections": [
                {
                    **det.to_dict(),
                    "crop_filename": f"{i+1:03d}_{det.status}_{self._get_crop_suffix(det)}.png",
                }
                for i, det in enumerate(session.detections)
            ]
        }
    
    def load_session(self, session_id: str) -> Optional[dict]:
        """Load session data from JSON."""
        json_path = self.sessions_dir / session_id / "session.json"
        if not json_path.exists():
            logger.warning(f"Session not found: {session_id}")
            return None
        
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def list_sessions(self) -> list[dict]:
        """List all saved sessions with summary info."""
        sessions = []
        for session_dir in sorted(self.sessions_dir.iterdir(), reverse=True):
            if session_dir.is_dir():
                json_path = session_dir / "session.json"
                if json_path.exists():
                    try:
                        with open(json_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            sessions.append({
                                "session_id": data["session_id"],
                                "timestamp": data["timestamp"],
                                "summary": data["summary"],
                                "path": str(session_dir),
                            })
                    except Exception as e:
                        logger.warning(f"Failed to load session {session_dir}: {e}")
        return sessions
    
    def get_missed_stamps(self) -> list[Path]:
        """Get all stamps that need re-ingestion."""
        return sorted(self.missed_dir.glob("*.png"))
    
    def get_missed_stamp_info(self, stamp_path: Path) -> dict:
        """Get info about a missed stamp from its filename."""
        # Filename format: {session_id}_{index}.png
        stem = stamp_path.stem
        parts = stem.rsplit("_", 1)
        if len(parts) == 2:
            session_id = parts[0]
            index = parts[1]
            return {
                "path": stamp_path,
                "session_id": session_id,
                "index": index,
                "filename": stamp_path.name,
            }
        return {
            "path": stamp_path,
            "session_id": "unknown",
            "index": "0",
            "filename": stamp_path.name,
        }
    
    def resolve_missed_stamp(
        self, 
        stamp_path: Path, 
        colnect_id: str,
        notes: Optional[str] = None,
    ) -> Path:
        """
        Mark a missed stamp as resolved with manual Colnect ID.
        
        Moves from missed_stamps/ to resolved/ with colnect_id in name.
        Also saves a resolution record.
        
        Returns:
            Path to resolved file
        """
        if not stamp_path.exists():
            raise FileNotFoundError(f"Stamp not found: {stamp_path}")
        
        # Create new filename with colnect_id
        clean_id = colnect_id.replace("/", "_").replace("\\", "_")
        new_name = f"{stamp_path.stem}_resolved_{clean_id}.png"
        resolved_path = self.resolved_dir / new_name
        
        # Move file
        stamp_path.rename(resolved_path)
        logger.info(f"Resolved stamp: {stamp_path.name} -> {colnect_id}")
        
        # Save resolution record
        record = {
            "original_filename": stamp_path.name,
            "colnect_id": colnect_id,
            "resolved_at": datetime.now().isoformat(),
            "notes": notes,
        }
        record_path = self.resolved_dir / f"{stamp_path.stem}_resolution.json"
        with open(record_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
        
        return resolved_path
    
    def skip_missed_stamp(self, stamp_path: Path, reason: str = "skipped") -> None:
        """Mark a missed stamp as skipped (remove from queue)."""
        if not stamp_path.exists():
            raise FileNotFoundError(f"Stamp not found: {stamp_path}")
        
        skipped_dir = self.output_dir / "skipped"
        skipped_dir.mkdir(exist_ok=True)
        
        new_path = skipped_dir / stamp_path.name
        stamp_path.rename(new_path)
        logger.info(f"Skipped stamp: {stamp_path.name} ({reason})")
    
    def get_session_annotated_path(self, session_id: str) -> Optional[Path]:
        """Get path to annotated image for a session."""
        path = self.sessions_dir / session_id / "annotated.png"
        return path if path.exists() else None
    
    def get_session_crops_dir(self, session_id: str) -> Optional[Path]:
        """Get path to crops directory for a session."""
        path = self.sessions_dir / session_id / "crops"
        return path if path.exists() else None
    
    def cleanup_old_sessions(self, keep_days: int = 30) -> int:
        """Remove sessions older than specified days. Returns count removed."""
        import shutil
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=keep_days)
        removed = 0
        
        for session_dir in self.sessions_dir.iterdir():
            if session_dir.is_dir():
                json_path = session_dir / "session.json"
                if json_path.exists():
                    try:
                        with open(json_path, "r") as f:
                            data = json.load(f)
                            timestamp = datetime.fromisoformat(data["timestamp"])
                            if timestamp < cutoff:
                                shutil.rmtree(session_dir)
                                removed += 1
                                logger.info(f"Removed old session: {session_dir.name}")
                    except Exception as e:
                        logger.warning(f"Failed to check session {session_dir}: {e}")
        
        return removed
