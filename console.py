"""Rich console output for scan feedback."""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from .models import ScanSession, DetectionFeedback


def display_scan_results(
    session: ScanSession, 
    console: Console,
    show_details: bool = True,
    session_path: Optional[Path] = None,
) -> None:
    """
    Display rich console feedback after scan.
    
    Args:
        session: The completed scan session
        console: Rich console instance
        show_details: Whether to show detailed stamp tables
        session_path: Path where session was saved (for display)
    """
    console.print()
    
    # Header panel
    source_info = session.source
    if session.source_path:
        source_info += f" ({session.source_path})"
    
    console.print(Panel(
        f"[bold]Session ID:[/bold] {session.session_id}\n"
        f"[bold]Source:[/bold] {source_info}\n"
        f"[bold]Time:[/bold] {session.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        title="📷 Scan Complete",
        border_style="blue"
    ))
    
    # Summary table
    summary = session.summary
    _display_summary_table(summary, console)
    
    # Detailed tables if requested
    if show_details:
        _display_identified_table(session, console)
        _display_no_match_table(session, console)
        _display_rejected_table(session, console)
    
    # Session path info
    if session_path:
        console.print()
        console.print(f"[dim]Session saved to:[/dim] {session_path}")
        console.print(f"[dim]Annotated image:[/dim] {session_path / 'annotated.png'}")
    
    # Warning for no-match stamps
    if summary["no_match"] > 0:
        console.print()
        console.print(Panel(
            f"[orange1]{summary['no_match']} stamp(s) detected but not found in RAG.[/orange1]\n\n"
            f"These crops have been saved for later review.\n"
            f"Use [bold cyan]stamp-tools review missed[/bold cyan] to process them.",
            title="⚠️ Stamps Need Review",
            border_style="orange1"
        ))


def _display_summary_table(summary: dict, console: Console) -> None:
    """Display the summary statistics table."""
    table = Table(
        title="Detection Summary",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold"
    )
    table.add_column("Status", style="bold", width=15)
    table.add_column("Count", justify="right", width=8)
    table.add_column("", width=20)
    
    # Identified
    if summary["identified"] > 0:
        bar = "[green]" + "█" * min(summary["identified"], 20) + "[/green]"
        table.add_row("✅ Identified", str(summary["identified"]), bar)
    
    # No match
    if summary["no_match"] > 0:
        bar = "[orange1]" + "█" * min(summary["no_match"], 20) + "[/orange1]"
        table.add_row("🟧 No Match", str(summary["no_match"]), bar)
    
    # Rejected
    if summary["rejected"] > 0:
        bar = "[red]" + "█" * min(summary["rejected"], 20) + "[/red]"
        table.add_row("❌ Rejected", str(summary["rejected"]), bar)
    
    # Separator and total
    table.add_row("─" * 12, "─" * 5, "")
    table.add_row(
        "[bold]Total Shapes[/bold]", 
        f"[bold]{summary['total_shapes']}[/bold]", 
        ""
    )
    
    console.print(table)


def _display_identified_table(session: ScanSession, console: Console) -> None:
    """Display table of identified stamps."""
    identified = session.identified_stamps
    if not identified:
        return
    
    console.print()
    console.print("[bold green]✅ Identified Stamps:[/bold green]")
    
    table = Table(show_header=True, box=box.SIMPLE)
    table.add_column("#", style="dim", width=4)
    table.add_column("Shape", width=12)
    table.add_column("Confidence", justify="right", width=12)
    table.add_column("Colnect ID", style="cyan", width=20)
    table.add_column("Status", width=10)
    
    for i, det in enumerate(session.detections):
        if det.status == "identified":
            conf_style = "green" if det.rag_confidence >= 0.9 else "yellow"
            status = "Auto ✓" if det.rag_confidence >= 0.9 else "Review"
            
            table.add_row(
                str(i + 1),
                det.shape_type,
                f"[{conf_style}]{det.rag_confidence:.1%}[/{conf_style}]",
                det.rag_top_match or "?",
                status
            )
    
    console.print(table)


def _display_no_match_table(session: ScanSession, console: Console) -> None:
    """Display table of stamps with no RAG match."""
    no_match = session.missed_stamps
    if not no_match:
        return
    
    console.print()
    console.print("[bold orange1]🟧 No Match Found:[/bold orange1]")
    
    table = Table(show_header=True, box=box.SIMPLE)
    table.add_column("#", style="dim", width=4)
    table.add_column("Shape", width=12)
    table.add_column("Best Score", justify="right", width=12)
    table.add_column("Crop File", width=30)
    
    for i, det in enumerate(session.detections):
        if det.status == "no_match":
            best_score = "N/A"
            if det.rag_top_3 and len(det.rag_top_3) > 0:
                best_score = f"{det.rag_top_3[0].get('score', 0):.1%}"
            
            table.add_row(
                str(i + 1),
                det.shape_type,
                best_score,
                f"{i+1:03d}_no_match_unmatched.png"
            )
    
    console.print(table)


def _display_rejected_table(session: ScanSession, console: Console) -> None:
    """Display table of rejected shapes."""
    rejected = session.rejected_shapes
    if not rejected:
        return
    
    console.print()
    console.print("[bold red]❌ Rejected Shapes:[/bold red]")
    
    table = Table(show_header=True, box=box.SIMPLE)
    table.add_column("#", style="dim", width=4)
    table.add_column("Shape", width=12)
    table.add_column("Confidence", justify="right", width=12)
    table.add_column("Reason", width=30)
    
    for i, det in enumerate(session.detections):
        if det.status == "rejected":
            table.add_row(
                str(i + 1),
                det.shape_type,
                f"{det.stage_1b_confidence:.1%}",
                det.stage_1b_reason or "Unknown"
            )
    
    console.print(table)


def display_missed_stamps_list(
    stamps: list[dict],
    console: Console,
) -> None:
    """Display list of missed stamps awaiting review."""
    if not stamps:
        console.print(Panel(
            "No stamps pending review! 🎉",
            title="Missed Stamps Queue",
            border_style="green"
        ))
        return
    
    console.print(Panel(
        f"[bold]{len(stamps)}[/bold] stamp(s) awaiting manual review",
        title="📋 Missed Stamps Queue",
        border_style="orange1"
    ))
    
    table = Table(show_header=True, box=box.ROUNDED)
    table.add_column("#", style="dim", width=4)
    table.add_column("Session", width=25)
    table.add_column("Index", width=6)
    table.add_column("Filename", width=35)
    
    for i, stamp in enumerate(stamps):
        table.add_row(
            str(i + 1),
            stamp.get("session_id", "unknown"),
            stamp.get("index", "?"),
            stamp.get("filename", "?")
        )
    
    console.print(table)


def display_session_list(
    sessions: list[dict],
    console: Console,
    limit: int = 10,
) -> None:
    """Display list of recent sessions."""
    if not sessions:
        console.print("[dim]No sessions found.[/dim]")
        return
    
    console.print(Panel(
        f"Showing {min(len(sessions), limit)} of {len(sessions)} sessions",
        title="📷 Recent Sessions",
        border_style="blue"
    ))
    
    table = Table(show_header=True, box=box.ROUNDED)
    table.add_column("Session ID", width=28)
    table.add_column("Timestamp", width=20)
    table.add_column("✅", justify="right", width=4)
    table.add_column("🟧", justify="right", width=4)
    table.add_column("❌", justify="right", width=4)
    table.add_column("Total", justify="right", width=6)
    
    for session in sessions[:limit]:
        summary = session.get("summary", {})
        table.add_row(
            session["session_id"],
            session["timestamp"][:19].replace("T", " "),
            str(summary.get("identified", 0)),
            str(summary.get("no_match", 0)),
            str(summary.get("rejected", 0)),
            str(summary.get("total_shapes", 0))
        )
    
    console.print(table)


def prompt_add_to_colnect(
    identified: list[DetectionFeedback],
    console: Console,
) -> list[DetectionFeedback]:
    """
    Prompt user to confirm adding identified stamps to Colnect.
    
    Returns:
        List of stamps user confirmed to add
    """
    if not identified:
        return []
    
    console.print()
    console.print(f"[bold]Add {len(identified)} identified stamp(s) to Colnect?[/bold]")
    
    # Show quick summary
    auto_accept = [d for d in identified if d.rag_confidence >= 0.9]
    needs_review = [d for d in identified if d.rag_confidence < 0.9]
    
    if auto_accept:
        console.print(f"  [green]• {len(auto_accept)} auto-matched (>90% confidence)[/green]")
    if needs_review:
        console.print(f"  [yellow]• {len(needs_review)} need review (<90% confidence)[/yellow]")
    
    response = console.input("\n[bold]Proceed? [Y/n/select]: [/bold]").strip().lower()
    
    if response in ("", "y", "yes"):
        return identified
    elif response in ("n", "no"):
        return []
    elif response in ("s", "select"):
        # Let user select which ones
        selected = []
        for det in identified:
            console.print(f"\n  {det.rag_top_match} ({det.rag_confidence:.1%})")
            add = console.input("  Add this stamp? [Y/n]: ").strip().lower()
            if add in ("", "y", "yes"):
                selected.append(det)
        return selected
    
    return []
