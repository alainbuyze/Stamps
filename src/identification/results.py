"""Result display and user selection for stamp identification.

Provides Rich-formatted display of identification results
and interactive selection for review cases.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt
from rich.table import Table

from src.identification.identifier import IdentificationBatch, StampIdentification
from src.rag.search import MatchConfidence, SearchResult

logger = logging.getLogger(__name__)


@dataclass
class UserSelection:
    """User's selection for a stamp that needed review."""

    stamp_index: int
    selected_match: Optional[SearchResult]
    skipped: bool = False
    manual_id: Optional[str] = None


@dataclass
class IdentificationSession:
    """Manages an identification session with user interactions."""

    batch: IdentificationBatch
    console: Console = field(default_factory=Console)
    confirmed_matches: list[tuple[StampIdentification, SearchResult]] = field(
        default_factory=list
    )
    skipped: list[StampIdentification] = field(default_factory=list)
    user_selections: list[UserSelection] = field(default_factory=list)

    def display_summary(self) -> None:
        """Display summary of detection results."""
        self.console.print()
        self.console.print(Panel(
            f"[bold]Source:[/bold] {self.batch.source_image.source}\n"
            f"[bold]Stamps Detected:[/bold] {self.batch.total_detected}\n"
            f"[bold]Auto-matches:[/bold] {len(self.batch.auto_matches)}\n"
            f"[bold]Need Review:[/bold] {len(self.batch.review_needed)}\n"
            f"[bold]No Match:[/bold] {len(self.batch.no_matches)}",
            title="Detection Summary",
            border_style="blue",
        ))

    def display_auto_matches(self) -> None:
        """Display stamps that were auto-matched (>90% confidence)."""
        auto_matches = self.batch.auto_matches

        if not auto_matches:
            return

        self.console.print("\n[bold green]Auto-Matched Stamps (>90% confidence)[/bold green]")

        for ident in auto_matches:
            match = ident.rag_result.auto_match
            if match:
                self._display_match(ident, match, confirmed=True)
                self.confirmed_matches.append((ident, match))

    def display_review_needed(self) -> None:
        """Display stamps that need user review and collect selections."""
        review_items = self.batch.review_needed

        if not review_items:
            return

        self.console.print("\n[bold yellow]Stamps Needing Review (50-90% confidence)[/bold yellow]")

        for ident in review_items:
            selection = self._review_stamp(ident)
            self.user_selections.append(selection)

            if selection.selected_match:
                self.confirmed_matches.append((ident, selection.selected_match))
            elif selection.skipped:
                self.skipped.append(ident)

    def display_no_matches(self) -> None:
        """Display stamps with no matches found."""
        no_matches = self.batch.no_matches

        if not no_matches:
            return

        self.console.print("\n[bold red]No Matches Found (<50% confidence)[/bold red]")

        for ident in no_matches:
            self.console.print(Panel(
                f"[bold]Stamp {ident.stamp.index}[/bold]\n"
                f"[dim]Description:[/dim] {ident.description[:200]}...\n\n"
                "[red]No matches found above minimum threshold.[/red]\n"
                "[dim]Try searching manually on Colnect.[/dim]",
                border_style="red",
            ))
            self.skipped.append(ident)

    def _display_match(
        self,
        ident: StampIdentification,
        match: SearchResult,
        confirmed: bool = False,
    ) -> None:
        """Display a single match.

        Args:
            ident: StampIdentification being displayed
            match: SearchResult match
            confirmed: Whether this is a confirmed match
        """
        status = "[green]CONFIRMED[/green]" if confirmed else "[yellow]CANDIDATE[/yellow]"
        score_color = "green" if match.percentage >= 90 else "yellow"

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Key", style="dim")
        table.add_column("Value")

        table.add_row("Status", status)
        table.add_row("Score", f"[{score_color}]{match.percentage:.1f}%[/{score_color}]")
        table.add_row("Colnect ID", match.entry.colnect_id)
        table.add_row("Country", match.entry.country)
        table.add_row("Year", str(match.entry.year))
        table.add_row("URL", match.entry.colnect_url)

        self.console.print(Panel(
            table,
            title=f"Stamp {ident.stamp.index}",
            border_style="green" if confirmed else "yellow",
        ))

    def _review_stamp(self, ident: StampIdentification) -> UserSelection:
        """Interactive review for a single stamp.

        Args:
            ident: StampIdentification to review

        Returns:
            UserSelection with user's choice
        """
        self.console.print()
        self.console.print(Panel(
            f"[bold]Stamp {ident.stamp.index}[/bold]\n\n"
            f"[dim]AI Description:[/dim]\n{ident.description[:300]}...",
            title=f"Review Stamp {ident.stamp.index}",
            border_style="yellow",
        ))

        # Display candidates
        self.console.print("\n[bold]Top Candidates:[/bold]")

        table = Table(show_header=True, header_style="bold")
        table.add_column("#", justify="right", width=3)
        table.add_column("Score", justify="right", width=8)
        table.add_column("Country", width=15)
        table.add_column("Year", width=6)
        table.add_column("Colnect ID", width=20)
        table.add_column("Description", width=40)

        for idx, match in enumerate(ident.rag_result.top_matches, 1):
            score_color = "green" if match.percentage >= 80 else "yellow"
            desc = match.entry.description[:40] + "..." if len(match.entry.description) > 40 else match.entry.description

            table.add_row(
                str(idx),
                f"[{score_color}]{match.percentage:.1f}%[/{score_color}]",
                match.entry.country,
                str(match.entry.year),
                match.entry.colnect_id,
                desc,
            )

        self.console.print(table)
        self.console.print()

        # Get user selection
        choices = len(ident.rag_result.top_matches)
        self.console.print(f"[dim]Enter 1-{choices} to select a match, 0 to skip[/dim]")

        try:
            choice = IntPrompt.ask(
                "Your selection",
                default=0,
                show_default=True,
            )

            if choice == 0:
                self.console.print("[yellow]Skipped[/yellow]")
                return UserSelection(
                    stamp_index=ident.stamp.index,
                    selected_match=None,
                    skipped=True,
                )

            if 1 <= choice <= choices:
                selected = ident.rag_result.top_matches[choice - 1]
                self.console.print(f"[green]Selected: {selected.entry.colnect_id}[/green]")
                return UserSelection(
                    stamp_index=ident.stamp.index,
                    selected_match=selected,
                )

            self.console.print("[yellow]Invalid selection, skipping[/yellow]")
            return UserSelection(
                stamp_index=ident.stamp.index,
                selected_match=None,
                skipped=True,
            )

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Skipped[/yellow]")
            return UserSelection(
                stamp_index=ident.stamp.index,
                selected_match=None,
                skipped=True,
            )

    def display_final_summary(self) -> None:
        """Display final summary of all results."""
        self.console.print()
        self.console.print("=" * 50)

        table = Table(title="Session Summary", show_header=True, header_style="bold")
        table.add_column("Category")
        table.add_column("Count", justify="right")

        table.add_row("Total Detected", str(self.batch.total_detected))
        table.add_row("[green]Confirmed Matches[/green]", str(len(self.confirmed_matches)))
        table.add_row("[yellow]Skipped[/yellow]", str(len(self.skipped)))

        self.console.print(table)

        if self.confirmed_matches:
            self.console.print("\n[bold]Confirmed Stamps:[/bold]")
            for ident, match in self.confirmed_matches:
                self.console.print(
                    f"  [{ident.stamp.index}] {match.entry.country} {match.entry.year} - "
                    f"{match.entry.colnect_id} ({match.percentage:.1f}%)"
                )

    def run_interactive(self) -> list[tuple[StampIdentification, SearchResult]]:
        """Run full interactive session.

        Returns:
            List of (identification, match) tuples for confirmed stamps
        """
        self.display_summary()

        if self.batch.total_detected == 0:
            self.console.print("\n[yellow]No stamps detected. Try with a clearer image.[/yellow]")
            return []

        self.display_auto_matches()
        self.display_review_needed()
        self.display_no_matches()
        self.display_final_summary()

        return self.confirmed_matches


def display_results(
    batch: IdentificationBatch,
    console: Optional[Console] = None,
    interactive: bool = True,
) -> list[tuple[StampIdentification, SearchResult]]:
    """Display identification results.

    Args:
        batch: IdentificationBatch to display
        console: Rich Console instance (creates new if not provided)
        interactive: Whether to allow user interaction for review items

    Returns:
        List of confirmed (identification, match) tuples
    """
    if console is None:
        console = Console()

    session = IdentificationSession(batch=batch, console=console)

    if interactive:
        return session.run_interactive()
    else:
        session.display_summary()
        session.display_auto_matches()

        # In non-interactive mode, just display review items without selection
        review_items = batch.review_needed
        if review_items:
            console.print("\n[bold yellow]Stamps Needing Review[/bold yellow]")
            for ident in review_items:
                if ident.rag_result.top_matches:
                    session._display_match(ident, ident.rag_result.top_matches[0])

        session.display_no_matches()
        return session.confirmed_matches


def format_match_for_colnect(match: SearchResult) -> dict:
    """Format a match for Colnect addition.

    Args:
        match: SearchResult to format

    Returns:
        Dict with Colnect addition parameters
    """
    return {
        "colnect_id": match.entry.colnect_id,
        "colnect_url": match.entry.colnect_url,
        "country": match.entry.country,
        "year": match.entry.year,
        "confidence": match.percentage,
    }
