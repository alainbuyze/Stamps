"""Inspection tools for analyzing pipeline results.

Provides CLI and programmatic access to inspection data.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Generator
import webbrowser

import cv2
import numpy as np

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class InspectionSession:
    """Loaded inspection session data."""
    
    session_id: str
    timestamp: datetime
    session_dir: Path
    data: dict
    
    @property
    def summary(self) -> dict:
        return self.data.get("summary", {})
    
    @property
    def mode(self) -> str:
        return self.data.get("mode", "unknown")
    
    @property
    def detection_result(self) -> Optional[dict]:
        return self.data.get("detection_result")
    
    @property
    def identifications(self) -> list:
        return self.data.get("identifications", [])
    
    def get_image_path(self, name: str) -> Optional[Path]:
        """Get path to an image file."""
        for ext in ['.jpg', '.png']:
            path = self.session_dir / f"{name}{ext}"
            if path.exists():
                return path
        return None
    
    def get_original(self) -> Optional[np.ndarray]:
        """Load original image."""
        path = self.get_image_path("original")
        if path:
            return cv2.imread(str(path))
        return None
    
    def get_annotated(self, name: str = "final_result") -> Optional[np.ndarray]:
        """Load annotated image."""
        path = self.session_dir / "annotated" / f"{name}.jpg"
        if path.exists():
            return cv2.imread(str(path))
        return None
    
    def get_crop(self, identification_id: str) -> Optional[np.ndarray]:
        """Load a crop image."""
        path = self.session_dir / "crops" / f"{identification_id}.jpg"
        if path.exists():
            return cv2.imread(str(path))
        return None
    
    def list_crops(self) -> list[Path]:
        """List all crop files."""
        crops_dir = self.session_dir / "crops"
        if crops_dir.exists():
            return sorted(crops_dir.glob("*.jpg"))
        return []


class InspectionViewer:
    """View and analyze inspection data.

    Uses inspection_path from settings directly - no parameters needed.
    """

    def __init__(self):
        settings = get_settings()
        self.inspection_dir = settings.inspection_path
        self.console = Console()
    
    def list_sessions(self, limit: int = 20) -> list[InspectionSession]:
        """List available inspection sessions."""
        sessions = []
        
        for session_dir in sorted(self.inspection_dir.iterdir(), reverse=True):
            if not session_dir.is_dir():
                continue
            
            session_json = session_dir / "session.json"
            if not session_json.exists():
                continue
            
            try:
                with open(session_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                sessions.append(InspectionSession(
                    session_id=data.get("session_id", session_dir.name),
                    timestamp=datetime.fromisoformat(data.get("timestamp", "2000-01-01")),
                    session_dir=session_dir,
                    data=data,
                ))
            except Exception as e:
                logger.warning(f"Failed to load session {session_dir}: {e}")
            
            if len(sessions) >= limit:
                break
        
        return sessions
    
    def load_session(self, session_id: str) -> Optional[InspectionSession]:
        """Load a specific session."""
        session_dir = self.inspection_dir / session_id
        if not session_dir.exists():
            return None
        
        session_json = session_dir / "session.json"
        if not session_json.exists():
            return None
        
        with open(session_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return InspectionSession(
            session_id=session_id,
            timestamp=datetime.fromisoformat(data.get("timestamp", "2000-01-01")),
            session_dir=session_dir,
            data=data,
        )
    
    def display_sessions_list(self, sessions: list[InspectionSession]) -> None:
        """Display list of sessions in console."""
        table = Table(title="Inspection Sessions", box=box.ROUNDED)
        table.add_column("Session ID", style="cyan")
        table.add_column("Timestamp", style="dim")
        table.add_column("Mode")
        table.add_column("Stamps", justify="right")
        table.add_column("Identified", justify="right", style="green")
        table.add_column("No Match", justify="right", style="orange1")
        
        for session in sessions:
            summary = session.summary
            table.add_row(
                session.session_id,
                session.timestamp.strftime("%Y-%m-%d %H:%M"),
                session.mode,
                str(summary.get("total_stamps", 0)),
                str(summary.get("identified", 0)),
                str(summary.get("no_match", 0)),
            )
        
        self.console.print(table)
    
    def display_session_detail(self, session: InspectionSession) -> None:
        """Display detailed session information."""
        # Header
        self.console.print(Panel(
            f"[bold]Session:[/bold] {session.session_id}\n"
            f"[bold]Mode:[/bold] {session.mode}\n"
            f"[bold]Timestamp:[/bold] {session.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            title="📋 Session Details",
            border_style="blue"
        ))
        
        # Summary
        summary = session.summary
        self.console.print(f"\n[bold]Summary:[/bold]")
        self.console.print(f"  Total stamps: {summary.get('total_stamps', 0)}")
        self.console.print(f"  Identified: [green]{summary.get('identified', 0)}[/green]")
        self.console.print(f"  Needs review: [yellow]{summary.get('needs_review', 0)}[/yellow]")
        self.console.print(f"  No match: [orange1]{summary.get('no_match', 0)}[/orange1]")
        
        # Detection info
        det = session.detection_result
        if det:
            self.console.print(f"\n[bold]Detection:[/bold]")
            self.console.print(f"  Provider: {det.get('provider_used', 'N/A')}")
            self.console.print(f"  Fallback triggered: {det.get('fallback_triggered', False)}")
            if det.get('fallback_reason'):
                self.console.print(f"  Fallback reason: {det.get('fallback_reason')}")
            self.console.print(f"  Latency: {det.get('primary_latency_ms', 0)}ms")
        
        # Identifications table
        if session.identifications:
            self.console.print()
            table = Table(title="Identifications", box=box.SIMPLE)
            table.add_column("ID", style="dim")
            table.add_column("Status")
            table.add_column("Score", justify="right")
            table.add_column("Match")
            table.add_column("Desc Latency", justify="right")
            table.add_column("RAG Latency", justify="right")
            
            status_colors = {
                "identified": "green",
                "needs_review": "yellow",
                "no_match": "orange1",
                "pending": "dim",
            }
            
            for ident in session.identifications:
                status = ident.get("status", "unknown")
                color = status_colors.get(status, "white")
                
                top_match = ident.get("top_match")
                match_text = top_match.get("colnect_id", "")[:20] if top_match else "-"
                
                table.add_row(
                    ident.get("identification_id", "?")[:8],
                    f"[{color}]{status}[/{color}]",
                    f"{ident.get('best_score', 0):.1%}",
                    match_text,
                    f"{ident.get('description_latency_ms', 0)}ms",
                    f"{ident.get('rag_latency_ms', 0)}ms",
                )
            
            self.console.print(table)
        
        # Files
        self.console.print(f"\n[bold]Files:[/bold]")
        self.console.print(f"  Session dir: {session.session_dir}")
        
        crops = session.list_crops()
        self.console.print(f"  Crops: {len(crops)} files")
        
        annotated = session.session_dir / "annotated"
        if annotated.exists():
            ann_files = list(annotated.glob("*.jpg"))
            self.console.print(f"  Annotated: {len(ann_files)} files")
    
    def display_identification_detail(
        self,
        session: InspectionSession,
        identification_id: str,
    ) -> None:
        """Display detailed identification information."""
        ident = None
        for i in session.identifications:
            if i.get("identification_id", "").startswith(identification_id):
                ident = i
                break
        
        if not ident:
            self.console.print(f"[red]Identification {identification_id} not found[/red]")
            return
        
        self.console.print(Panel(
            f"[bold]ID:[/bold] {ident.get('identification_id')}\n"
            f"[bold]Status:[/bold] {ident.get('status')}\n"
            f"[bold]Mode:[/bold] {ident.get('mode')}",
            title="🔍 Identification Details",
            border_style="cyan"
        ))
        
        # Description
        self.console.print(f"\n[bold]Description:[/bold]")
        desc = ident.get("description", "N/A")
        if desc:
            # Truncate for display
            if len(desc) > 500:
                desc = desc[:500] + "..."
            self.console.print(f"  {desc}")
        self.console.print(f"  [dim]Provider: {ident.get('description_provider', 'N/A')}[/dim]")
        self.console.print(f"  [dim]Latency: {ident.get('description_latency_ms', 0)}ms[/dim]")
        
        # RAG matches
        self.console.print(f"\n[bold]RAG Matches:[/bold]")
        matches = ident.get("top_3_matches", [])
        if matches:
            for i, match in enumerate(matches):
                score = match.get("similarity_score", 0)
                style = "green" if score >= 0.9 else "yellow" if score >= 0.5 else "red"
                self.console.print(
                    f"  {i+1}. [{style}]{score:.1%}[/{style}] "
                    f"{match.get('colnect_id', 'N/A')} "
                    f"({match.get('country', '?')}, {match.get('year', '?')})"
                )
        else:
            self.console.print("  [dim]No matches found[/dim]")
        
        # Errors
        if ident.get("description_error"):
            self.console.print(f"\n[red]Description error: {ident.get('description_error')}[/red]")
        if ident.get("rag_error"):
            self.console.print(f"\n[red]RAG error: {ident.get('rag_error')}[/red]")
    
    def open_images(self, session: InspectionSession) -> None:
        """Open session images in default viewer."""
        # Try to open annotated image
        annotated = session.get_image_path("annotated/final_result")
        if annotated:
            webbrowser.open(str(annotated))
        else:
            original = session.get_image_path("original")
            if original:
                webbrowser.open(str(original))
    
    def compare_preprocessing(self, image_path: Path) -> dict:
        """
        Run preprocessing comparison on an image.

        Generates all variants and comparison report.
        Output goes to inspection_path/preprocessing_test.
        """
        from .preprocessing import PreprocessingTester, PreprocessingStrategy

        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        output_dir = self.inspection_dir / "preprocessing_test"
        tester = PreprocessingTester(output_dir)
        
        # Generate variants
        variants = tester.generate_all_variants(image, save_images=True)
        
        # Create report
        report = tester.create_comparison_report(variants)
        
        # Create visual comparison
        comparison = tester.create_visual_comparison(
            variants,
            output_dir / "comparison.jpg"
        )
        
        # Display report
        self.console.print(Panel("Preprocessing Comparison", style="bold"))
        
        table = Table(box=box.ROUNDED)
        table.add_column("Strategy")
        table.add_column("Resolution")
        table.add_column("File Size", justify="right")
        table.add_column("Est. Tokens", justify="right")
        
        for name, data in report.items():
            table.add_row(
                name,
                data["processed_resolution"],
                f"{data['file_size_kb']} KB",
                str(data["estimated_tokens"]),
            )
        
        self.console.print(table)
        self.console.print(f"\n[dim]Variants saved to: {output_dir}[/dim]")
        self.console.print(f"[dim]Comparison image: {output_dir / 'comparison.jpg'}[/dim]")
        
        return report


def create_inspection_cli():
    """Create CLI commands for inspection.

    All paths come from settings - no CLI overrides needed.
    """
    import click

    @click.group()
    def inspect():
        """Inspection tools for analyzing pipeline results."""
        pass

    @inspect.command()
    @click.option('--limit', '-n', default=20, help='Number of sessions to show')
    def sessions(limit: int):
        """List inspection sessions."""
        viewer = InspectionViewer()
        sessions_list = viewer.list_sessions(limit=limit)
        viewer.display_sessions_list(sessions_list)

    @inspect.command()
    @click.argument('session_id')
    def session(session_id: str):
        """Show session details."""
        viewer = InspectionViewer()
        session_data = viewer.load_session(session_id)
        if session_data:
            viewer.display_session_detail(session_data)
        else:
            click.echo(f"Session not found: {session_id}")

    @inspect.command()
    @click.argument('session_id')
    @click.argument('identification_id')
    def identification(session_id: str, identification_id: str):
        """Show identification details."""
        viewer = InspectionViewer()
        session_data = viewer.load_session(session_id)
        if session_data:
            viewer.display_identification_detail(session_data, identification_id)
        else:
            click.echo(f"Session not found: {session_id}")

    @inspect.command()
    @click.argument('session_id')
    def open_images(session_id: str):
        """Open session images in viewer."""
        viewer = InspectionViewer()
        session_data = viewer.load_session(session_id)
        if session_data:
            viewer.open_images(session_data)
        else:
            click.echo(f"Session not found: {session_id}")

    @inspect.command()
    @click.argument('image_path', type=click.Path(exists=True))
    def preprocess_test(image_path: str):
        """Test preprocessing strategies on an image."""
        viewer = InspectionViewer()
        viewer.compare_preprocessing(Path(image_path))

    return inspect
