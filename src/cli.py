"""Click CLI entry point for Stamp Collection Toolset.

Commands:
    init        Initialize database and verify connections
    scrape      Web scraping commands (colnect, lastdodo)
    rag         RAG database commands (index, search, stats)
    identify    Stamp identification (camera, image)
    migrate     LASTDODO migration (match, import, review, status)
    config      Configuration commands (show, validate)
"""

import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.config import get_settings
from src.core.database import get_database_stats, init_database
from src.core.logging import setup_logging

console = Console()
logger = logging.getLogger(__name__)


# =============================================================================
# Main CLI Group
# =============================================================================


@click.group()
@click.version_option(version="0.1.0", prog_name="stamp-tools")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def cli(debug: bool) -> None:
    """Stamp Collection Toolset - AI-powered stamp management.

    Build a searchable RAG database from Colnect, identify physical stamps
    via camera, and migrate collections from LASTDODO.
    """
    # Initialize logging
    log_level = "DEBUG" if debug else None
    setup_logging(level=log_level)

    if debug:
        console.print("[dim]Debug mode enabled[/dim]")


# =============================================================================
# Init Command
# =============================================================================


@cli.command()
def init() -> None:
    """Initialize database and verify connections.

    This command:
    - Creates the data directory
    - Initializes the SQLite database with schema
    - Downloads YOLOv8 model (if not present)
    - Verifies API key configuration
    - Tests Supabase connection (if configured)
    """
    console.print(Panel("Initializing Stamp Collection Toolset", style="bold blue"))

    settings = get_settings()
    errors = []

    # Step 1: Create directories
    console.print("\n[bold]1. Creating directories...[/bold]")
    try:
        data_dir = Path(settings.DATABASE_PATH).parent
        data_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"   [green]✓[/green] Created {data_dir}")

        log_dir = Path(settings.LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"   [green]✓[/green] Created {log_dir}")

        models_dir = Path(settings.YOLO_MODEL_PATH).parent
        models_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"   [green]✓[/green] Created {models_dir}")
    except Exception as e:
        console.print(f"   [red]✗[/red] Failed to create directories: {e}")
        errors.append(f"Directory creation: {e}")

    # Step 2: Initialize database
    console.print("\n[bold]2. Initializing database...[/bold]")
    try:
        init_database()
        console.print(f"   [green]✓[/green] Database initialized at {settings.DATABASE_PATH}")
    except Exception as e:
        console.print(f"   [red]✗[/red] Database initialization failed: {e}")
        errors.append(f"Database: {e}")

    # Step 3: Check YOLO model
    console.print("\n[bold]3. Checking YOLO model...[/bold]")
    yolo_path = Path(settings.YOLO_MODEL_PATH)
    if yolo_path.exists():
        console.print(f"   [green]✓[/green] YOLO model found at {yolo_path}")
    else:
        console.print(f"   [yellow]![/yellow] YOLO model not found at {yolo_path}")
        console.print("   [dim]   Model will be auto-downloaded on first use[/dim]")

    # Step 4: Verify API keys
    console.print("\n[bold]4. Verifying API keys...[/bold]")
    api_status = settings.validate_api_keys()

    for api, configured in api_status.items():
        if configured:
            console.print(f"   [green]✓[/green] {api.upper()} API key configured")
        else:
            console.print(f"   [yellow]![/yellow] {api.upper()} API key not configured")
            console.print(f"   [dim]   Add to .env.keys file[/dim]")

    # Step 5: Test Supabase connection (if configured)
    console.print("\n[bold]5. Testing Supabase connection...[/bold]")
    if api_status["supabase"]:
        try:
            from supabase import create_client

            client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            # Simple health check
            client.table("stamps_rag").select("id").limit(1).execute()
            console.print("   [green]✓[/green] Supabase connection successful")
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg.lower() or "404" in error_msg:
                console.print("   [yellow]![/yellow] Supabase connected, but stamps_rag table not found")
                console.print("   [dim]   Run 'stamp-tools rag init' to create table[/dim]")
            else:
                console.print(f"   [red]✗[/red] Supabase connection failed: {e}")
                errors.append(f"Supabase: {e}")
    else:
        console.print("   [yellow]![/yellow] Supabase not configured, skipping")

    # Step 6: Check vision prompt
    console.print("\n[bold]6. Checking vision prompt...[/bold]")
    prompt_path = Path(settings.VISION_PROMPT_FILE)
    if prompt_path.exists():
        console.print(f"   [green]✓[/green] Vision prompt found at {prompt_path}")
    else:
        console.print(f"   [red]✗[/red] Vision prompt not found at {prompt_path}")
        errors.append(f"Vision prompt missing: {prompt_path}")

    # Summary
    console.print("\n" + "=" * 50)
    if errors:
        console.print(Panel(
            f"[yellow]Initialization completed with {len(errors)} warning(s)[/yellow]\n"
            + "\n".join(f"  - {e}" for e in errors),
            title="Summary",
            style="yellow",
        ))
    else:
        console.print(Panel(
            "[green]Initialization completed successfully![/green]",
            title="Summary",
            style="green",
        ))


# =============================================================================
# Scrape Command Group
# =============================================================================


@cli.group()
def scrape() -> None:
    """Web scraping commands."""
    pass


@scrape.command("colnect")
@click.option(
    "--themes",
    default=None,
    help="Comma-separated themes to scrape (default: Space,Astronomy,...)",
)
@click.option("--country", default=None, help="Filter by country")
@click.option("--year", type=int, default=None, help="Filter by year")
@click.option("--resume", is_flag=True, help="Resume from checkpoint")
@click.option("--dry-run", is_flag=True, help="Show scraped data without saving to database")
@click.option("--limit", type=int, default=None, help="Limit number of stamps to scrape")
def scrape_colnect(themes: str, country: str, year: int, resume: bool, dry_run: bool, limit: int) -> None:
    """Scrape Colnect for space-themed stamps.

    Examples:
        stamp-tools scrape colnect
        stamp-tools scrape colnect --themes "Space,Rockets"
        stamp-tools scrape colnect --country "Australia" --year 2021
        stamp-tools scrape colnect --resume
        stamp-tools scrape colnect --dry-run --limit 5
        # Preview 3 stamps without saving
        stamp-tools scrape colnect --themes "Rockets" --country "Ascension Island" --dry-run --limit 3

        # Or with debug logging to see full details
        stamp-tools --debug scrape colnect --themes "Rockets" --country "Ascension Island" --dry-run --limit 3
    """
    import asyncio

    from rich.progress import Progress, SpinnerColumn, TextColumn

    from src.scraping.colnect import ColnectScraper

    settings = get_settings()
    theme_list = [t.strip() for t in themes.split(",")] if themes else settings.themes_list

    console.print(Panel("Colnect Stamp Scraper", style="bold blue"))
    console.print(f"[bold]Themes:[/bold] {', '.join(theme_list)}")
    if country:
        console.print(f"[bold]Country filter:[/bold] {country}")
    if year:
        console.print(f"[bold]Year filter:[/bold] {year}")
    if resume:
        console.print("[bold]Mode:[/bold] Resuming from checkpoint")
    if dry_run:
        console.print("[bold]Mode:[/bold] [yellow]DRY RUN - not saving to database[/yellow]")
    if limit:
        console.print(f"[bold]Limit:[/bold] {limit} stamps")

    console.print()

    async def run_scraper():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Starting scraper...", total=None)

            def on_progress(count: int, message: str):
                progress.update(task, description=f"[{count}] {message}")

            try:
                async with ColnectScraper() as scraper:
                    total = await scraper.scrape_themes(
                        themes=theme_list,
                        resume=resume,
                        country_filter=country,
                        year_filter=year,
                        progress_callback=on_progress,
                        dry_run=dry_run,
                        limit=limit,
                    )
                return total
            except Exception as e:
                logger.error(f"Scraping failed: {e}")
                raise

    try:
        total = asyncio.run(run_scraper())
        console.print()
        if dry_run:
            console.print(Panel(
                f"[yellow]DRY RUN complete![/yellow]\n"
                f"Total stamps found: {total}\n"
                f"[dim]No data was saved to database[/dim]",
                title="Summary",
                style="yellow",
            ))
        else:
            console.print(Panel(
                f"[green]Scraping complete![/green]\n"
                f"Total stamps scraped: {total}",
                title="Summary",
                style="green",
            ))
    except KeyboardInterrupt:
        console.print("\n[yellow]Scraping interrupted. Progress saved to checkpoint.[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Scraping failed: {e}[/red]")
        sys.exit(1)


@scrape.command("lastdodo")
def scrape_lastdodo() -> None:
    """Scrape LASTDODO collection.

    Requires Chrome with logged-in LASTDODO session via CDP.

    Example:
        stamp-tools scrape lastdodo
    """
    console.print("[yellow]LASTDODO scraper not yet implemented (Phase 6)[/yellow]")
    console.print("This will scrape your LASTDODO collection.")


# =============================================================================
# RAG Command Group
# =============================================================================


@cli.group()
def rag() -> None:
    """RAG database commands."""
    pass


@rag.command("init")
def rag_init() -> None:
    """Initialize RAG table in Supabase.

    Creates the stamps_rag table with pgvector support if it doesn't exist.
    Also shows the SQL needed to create the similarity search function.

    Example:
        stamp-tools rag init
    """
    from src.rag.supabase_client import SupabaseRAG, MATCH_STAMPS_SQL

    console.print(Panel("RAG Database Initialization", style="bold blue"))

    try:
        supabase = SupabaseRAG()
        console.print("[dim]Connected to Supabase[/dim]\n")

        console.print("[bold]1. Verifying stamps_rag table...[/bold]")
        try:
            supabase.init_table()
            console.print("   [green]✓[/green] Table exists and is accessible")
        except Exception as e:
            console.print(f"   [red]✗[/red] Table verification failed: {e}")
            console.print("\n[yellow]Please create the table manually in Supabase SQL Editor:[/yellow]")
            console.print("""
CREATE TABLE IF NOT EXISTS stamps_rag (
    id BIGSERIAL PRIMARY KEY,
    colnect_id TEXT UNIQUE NOT NULL,
    colnect_url TEXT NOT NULL,
    image_url TEXT NOT NULL,
    description TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    country TEXT NOT NULL,
    year INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stamps_rag_colnect_id ON stamps_rag(colnect_id);
CREATE INDEX IF NOT EXISTS idx_stamps_rag_country ON stamps_rag(country);
CREATE INDEX IF NOT EXISTS idx_stamps_rag_year ON stamps_rag(year);
""")
            sys.exit(1)

        console.print("\n[bold]2. Similarity search function[/bold]")
        console.print("   For optimal performance, create this function in Supabase SQL Editor:")
        console.print()
        console.print(Panel(MATCH_STAMPS_SQL, title="match_stamps function", border_style="dim"))

        console.print(Panel(
            "[green]RAG database ready![/green]\n"
            "Run 'stamp-tools rag index' to start indexing stamps.",
            title="Summary",
            style="green",
        ))

    except Exception as e:
        console.print(f"[red]Initialization failed: {e}[/red]")
        console.print("[dim]Check your Supabase configuration in .env.keys[/dim]")
        sys.exit(1)


@rag.command("index")
@click.option("--country", default=None, help="Filter by country")
@click.option("--year", type=int, default=None, help="Filter by year")
@click.option("--regenerate", is_flag=True, help="Regenerate descriptions")
@click.option("--batch", is_flag=True, help="Use optimized batch processing")
def rag_index(country: str, year: int, regenerate: bool, batch: bool) -> None:
    """Index scraped stamps into Supabase RAG.

    Generates descriptions via Groq vision API and embeddings via OpenAI,
    then stores in Supabase for vector similarity search.

    Examples:
        stamp-tools rag index
        stamp-tools rag index --country "Australia" --year 2021
        stamp-tools rag index --regenerate
        stamp-tools rag index --batch
    """
    import asyncio

    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

    from src.rag.indexer import RAGIndexer

    console.print(Panel("RAG Indexer", style="bold blue"))

    if country:
        console.print(f"[bold]Country filter:[/bold] {country}")
    if year:
        console.print(f"[bold]Year filter:[/bold] {year}")
    if regenerate:
        console.print("[bold]Mode:[/bold] Regenerating all descriptions")
    if batch:
        console.print("[bold]Mode:[/bold] Optimized batch processing")

    console.print()

    # Verify setup first
    indexer = RAGIndexer()
    console.print("[dim]Verifying API connections...[/dim]")

    try:
        status = indexer.verify_setup()
        all_ready = all(status.values())

        for component, ready in status.items():
            if ready:
                console.print(f"   [green]✓[/green] {component}")
            else:
                console.print(f"   [red]✗[/red] {component}")

        if not all_ready:
            console.print("\n[red]Cannot proceed - some components not ready.[/red]")
            console.print("[dim]Check your API keys in .env.keys[/dim]")
            sys.exit(1)

    except Exception as e:
        console.print(f"\n[red]Setup verification failed: {e}[/red]")
        sys.exit(1)

    console.print()

    async def run_indexing():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Starting indexer...", total=None)

            def on_progress(current: int, total: int, message: str):
                progress.update(task, total=total, completed=current, description=message)

            try:
                if batch:
                    stats = await indexer.index_batch_optimized(
                        country=country,
                        year=year,
                        regenerate=regenerate,
                        progress_callback=on_progress,
                    )
                else:
                    stats = await indexer.index_all(
                        country=country,
                        year=year,
                        regenerate=regenerate,
                        progress_callback=on_progress,
                    )
                return stats
            except Exception as e:
                logger.error(f"Indexing failed: {e}")
                raise

    try:
        stats = asyncio.run(run_indexing())
        console.print()

        # Show results
        table = Table(show_header=True, header_style="bold")
        table.add_column("Metric")
        table.add_column("Count", justify="right")

        table.add_row("Total stamps", str(stats.total_stamps))
        table.add_row("Already indexed", str(stats.already_indexed))
        table.add_row("Newly indexed", str(stats.newly_indexed))
        table.add_row("Description failures", str(stats.description_failures))
        table.add_row("Success rate", f"{stats.success_rate:.1f}%")

        console.print(table)

        if stats.newly_indexed > 0:
            console.print(Panel(
                f"[green]Indexing complete![/green]\n"
                f"Indexed {stats.newly_indexed} new stamps",
                title="Summary",
                style="green",
            ))
        else:
            console.print(Panel(
                "[yellow]No new stamps to index[/yellow]",
                title="Summary",
                style="yellow",
            ))

    except KeyboardInterrupt:
        console.print("\n[yellow]Indexing interrupted.[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Indexing failed: {e}[/red]")
        sys.exit(1)


@rag.command("search")
@click.option("--query", required=True, help="Search query")
@click.option("--limit", default=5, help="Number of results")
@click.option("--country", default=None, help="Filter by country")
@click.option("--year", type=int, default=None, help="Filter by year")
def rag_search(query: str, limit: int, country: str, year: int) -> None:
    """Manual similarity search for testing.

    Search the RAG database using natural language queries.

    Examples:
        stamp-tools rag search --query "rocket launch astronaut"
        stamp-tools rag search --query "Soviet space dog" --country "Russia"
        stamp-tools rag search --query "Apollo mission" --year 1969
    """
    from src.rag.search import RAGSearcher, MatchConfidence

    console.print(Panel("RAG Search", style="bold blue"))
    console.print(f"[bold]Query:[/bold] {query}")
    if country:
        console.print(f"[bold]Country filter:[/bold] {country}")
    if year:
        console.print(f"[bold]Year filter:[/bold] {year}")
    console.print()

    try:
        searcher = RAGSearcher()
        results = searcher.search(
            query=query,
            top_k=limit,
            country=country,
            year=year,
        )

        if not results:
            console.print("[yellow]No matching stamps found.[/yellow]")
            console.print("[dim]Try a different query or adjust filters.[/dim]")
            return

        console.print(f"[bold]Found {len(results)} matches:[/bold]\n")

        for result in results:
            # Color based on confidence
            if result.confidence == MatchConfidence.AUTO_ACCEPT:
                score_style = "green"
            elif result.confidence == MatchConfidence.REVIEW:
                score_style = "yellow"
            else:
                score_style = "red"

            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Key", style="dim")
            table.add_column("Value")

            table.add_row("Rank", f"#{result.rank}")
            table.add_row("Score", f"[{score_style}]{result.percentage:.1f}%[/{score_style}]")
            table.add_row("ID", result.entry.colnect_id)
            table.add_row("Country", result.entry.country)
            table.add_row("Year", str(result.entry.year))
            table.add_row("URL", result.entry.colnect_url)

            # Truncate description
            desc = result.entry.description
            if len(desc) > 200:
                desc = desc[:200] + "..."
            table.add_row("Description", desc)

            console.print(Panel(table, title=f"Match #{result.rank}", border_style=score_style))
            console.print()

    except Exception as e:
        console.print(f"[red]Search failed: {e}[/red]")
        sys.exit(1)


@rag.command("stats")
def rag_stats() -> None:
    """Show RAG database statistics.

    Displays information about the indexed stamps in Supabase.

    Example:
        stamp-tools rag stats
    """
    from src.rag.supabase_client import SupabaseRAG

    console.print(Panel("RAG Database Statistics", style="bold blue"))

    try:
        supabase = SupabaseRAG()
        stats = supabase.get_stats()

        if "error" in stats:
            console.print(f"[yellow]Warning: {stats['error']}[/yellow]\n")

        table = Table(show_header=True, header_style="bold")
        table.add_column("Metric")
        table.add_column("Value", justify="right")

        table.add_row("Total indexed stamps", str(stats["total_entries"]))
        table.add_row("Number of countries", str(stats["country_count"]))

        year_range = stats["year_range"]
        if year_range["min"] and year_range["max"]:
            table.add_row("Year range", f"{year_range['min']} - {year_range['max']}")
        else:
            table.add_row("Year range", "N/A")

        console.print(table)

        # Show countries if not too many
        countries = stats.get("countries", [])
        if countries:
            console.print(f"\n[bold]Countries ({len(countries)}):[/bold]")
            if len(countries) <= 20:
                console.print(", ".join(countries))
            else:
                console.print(", ".join(countries[:20]) + f" ... and {len(countries) - 20} more")

        # Also show local database stats for comparison
        console.print("\n[bold]Local Database Comparison:[/bold]")
        db_stats = get_database_stats()

        compare_table = Table(show_header=True, header_style="bold")
        compare_table.add_column("Source")
        compare_table.add_column("Count", justify="right")
        compare_table.add_column("Status")

        local_count = db_stats["catalog_stamps"]
        rag_count = stats["total_entries"]

        if local_count == 0:
            status = "[dim]No stamps scraped[/dim]"
        elif rag_count == local_count:
            status = "[green]Fully indexed[/green]"
        elif rag_count > 0:
            pct = (rag_count / local_count) * 100
            status = f"[yellow]{pct:.1f}% indexed[/yellow]"
        else:
            status = "[red]Not indexed[/red]"

        compare_table.add_row("Local SQLite", str(local_count), "")
        compare_table.add_row("Supabase RAG", str(rag_count), status)

        console.print(compare_table)

    except Exception as e:
        console.print(f"[red]Failed to get stats: {e}[/red]")
        console.print("[dim]Check your Supabase configuration in .env.keys[/dim]")
        sys.exit(1)


# =============================================================================
# Identify Command Group
# =============================================================================


@cli.group()
def identify() -> None:
    """Stamp identification commands."""
    pass


@identify.command("camera")
@click.option("--add-to-colnect", is_flag=True, help="Auto-add matches to Colnect")
@click.option("--camera", type=int, default=None, help="Camera device index")
@click.option("--no-preview", is_flag=True, help="Skip preview, capture immediately")
@click.option("--save-annotated", type=click.Path(), default=None, help="Save annotated image")
def identify_camera(add_to_colnect: bool, camera: int, no_preview: bool, save_annotated: str) -> None:
    """Identify stamps from camera.

    Captures image from camera, detects stamps, and identifies them
    using the RAG database.

    Example:
        stamp-tools identify camera
        stamp-tools identify camera --add-to-colnect
        stamp-tools identify camera --camera 1
        stamp-tools identify camera --no-preview
    """
    import asyncio
    from pathlib import Path

    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

    from src.identification.identifier import StampIdentifier
    from src.identification.results import display_results

    console.print(Panel("Stamp Identification - Camera", style="bold blue"))

    # Verify setup
    identifier = StampIdentifier()
    console.print("[dim]Verifying setup...[/dim]")

    status = identifier.verify_setup()
    all_ready = all(status.values())

    for component, ready in status.items():
        if ready:
            console.print(f"   [green]✓[/green] {component}")
        else:
            console.print(f"   [red]✗[/red] {component}")

    if not all_ready:
        console.print("\n[red]Cannot proceed - some components not ready.[/red]")
        console.print("[dim]Check your configuration with 'stamp-tools config validate'[/dim]")
        sys.exit(1)

    console.print()

    async def run_identification():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Starting...", total=None)

            def on_progress(current: int, total: int, message: str):
                progress.update(task, total=total, completed=current, description=message)

            try:
                batch = await identifier.identify_from_camera(
                    camera_index=camera,
                    use_preview=not no_preview,
                    progress_callback=on_progress,
                )
                return batch
            except Exception as e:
                logger.error(f"Identification failed: {e}")
                raise

    try:
        batch = asyncio.run(run_identification())

        if batch is None:
            console.print("\n[yellow]Capture cancelled.[/yellow]")
            return

        # Save annotated image if requested
        if save_annotated and batch.total_detected > 0:
            save_path = Path(save_annotated)
            batch.detection_result.save_annotated(save_path)
            console.print(f"\n[dim]Saved annotated image to {save_path}[/dim]")

        # Display results interactively
        confirmed = display_results(batch, console=console, interactive=True)

        if add_to_colnect and confirmed:
            console.print("\n[yellow]Colnect automation not yet implemented (Phase 5)[/yellow]")
            console.print(f"Would add {len(confirmed)} stamps to Colnect collection.")

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Identification failed: {e}[/red]")
        sys.exit(1)


@identify.command("image")
@click.option("--path", required=True, type=click.Path(exists=True), help="Image path")
@click.option("--add-to-colnect", is_flag=True, help="Auto-add matches to Colnect")
@click.option("--save-annotated", type=click.Path(), default=None, help="Save annotated image")
@click.option("--non-interactive", is_flag=True, help="Skip user selection prompts")
@click.option("--detector", type=click.Choice(["yolo", "contour", "auto"]), default="auto",
              help="Detection method: yolo (ML), contour (classical CV), auto (try both)")
def identify_image(path: str, add_to_colnect: bool, save_annotated: str, non_interactive: bool, detector: str) -> None:
    """Identify stamps from image file.

    Loads an image, detects stamps, and identifies them using the RAG database.

    Detector options:
        - auto: YOLO first, falls back to treating whole image as stamp (default)
        - contour: Classical CV contour detection - good for album pages
        - yolo: YOLO object detection only

    Example:
        stamp-tools identify image --path "photo.jpg"
        stamp-tools identify image --path "stamps.png" --detector contour
        stamp-tools identify image --path "album_page.jpg" --detector contour --save-annotated "result.jpg"
    """
    import asyncio
    from pathlib import Path as PathLib

    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

    from src.identification.identifier import StampIdentifier
    from src.identification.results import display_results

    console.print(Panel("Stamp Identification - Image", style="bold blue"))
    console.print(f"[bold]Image:[/bold] {path}")
    console.print(f"[bold]Detector:[/bold] {detector}")
    console.print()

    # Verify setup
    identifier = StampIdentifier(detector_type=detector)
    console.print("[dim]Verifying setup...[/dim]")

    status = identifier.verify_setup()
    all_ready = all(status.values())

    for component, ready in status.items():
        if ready:
            console.print(f"   [green]✓[/green] {component}")
        else:
            console.print(f"   [red]✗[/red] {component}")

    if not all_ready:
        console.print("\n[red]Cannot proceed - some components not ready.[/red]")
        console.print("[dim]Check your configuration with 'stamp-tools config validate'[/dim]")
        sys.exit(1)

    console.print()

    async def run_identification():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Starting...", total=None)

            def on_progress(current: int, total: int, message: str):
                progress.update(task, total=total, completed=current, description=message)

            try:
                batch = await identifier.identify_from_file(
                    PathLib(path),
                    progress_callback=on_progress,
                )
                return batch
            except Exception as e:
                logger.error(f"Identification failed: {e}")
                raise

    try:
        batch = asyncio.run(run_identification())

        # Save annotated image if requested
        if save_annotated and batch.total_detected > 0:
            save_path = PathLib(save_annotated)
            batch.detection_result.save_annotated(save_path)
            console.print(f"\n[dim]Saved annotated image to {save_path}[/dim]")

        # Display results
        confirmed = display_results(
            batch,
            console=console,
            interactive=not non_interactive,
        )

        if add_to_colnect and confirmed:
            console.print("\n[yellow]Colnect automation not yet implemented (Phase 5)[/yellow]")
            console.print(f"Would add {len(confirmed)} stamps to Colnect collection.")

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Identification failed: {e}[/red]")
        sys.exit(1)


# =============================================================================
# Train Command Group
# =============================================================================


@cli.group()
def train() -> None:
    """YOLO model training commands for stamp detection."""
    pass


@train.command("prepare")
@click.option("--source", type=click.Path(exists=True), required=True, help="Directory with raw images")
@click.option("--output", type=click.Path(), default="data/training", help="Output dataset directory")
def train_prepare(source: str, output: str) -> None:
    """Prepare images for annotation.

    Copies images to training directory and creates import file for Label Studio.

    Example:
        stamp-tools train prepare --source "C:\\Photos\\AlbumPages"
    """
    from pathlib import Path as PathLib

    from src.training.dataset import prepare_dataset
    from src.training.labelstudio import create_import_file, generate_project_setup_instructions

    console.print(Panel("Prepare Training Dataset", style="bold blue"))

    source_path = PathLib(source)
    output_path = PathLib(output)

    console.print(f"[bold]Source:[/bold] {source_path}")
    console.print(f"[bold]Output:[/bold] {output_path}")
    console.print()

    # Prepare dataset structure
    dataset = prepare_dataset(source_path, output_path)
    stats = dataset.get_stats()

    console.print(f"[green]✓[/green] Copied images to {output_path / 'raw'}")

    # Create Label Studio import file
    import_file = create_import_file(output_path / "raw")
    console.print(f"[green]✓[/green] Created import file: {import_file}")

    # Show instructions
    instructions = generate_project_setup_instructions(output_path / "raw")
    console.print(Panel(instructions, title="Next Steps", border_style="yellow"))


@train.command("labelstudio")
@click.option("--port", default=8080, help="Port to run Label Studio on")
@click.option("--data-dir", type=click.Path(), default="data/training/raw", help="Directory with images")
def train_labelstudio(port: int, data_dir: str) -> None:
    """Start Label Studio for annotation.

    Opens Label Studio in browser for labeling stamp images.

    Example:
        stamp-tools train labelstudio
        stamp-tools train labelstudio --port 8081
    """
    from pathlib import Path as PathLib

    from src.training.labelstudio import check_labelstudio_installed, install_labelstudio, start_labelstudio

    console.print(Panel("Label Studio", style="bold blue"))

    # Check if installed
    if not check_labelstudio_installed():
        console.print("[yellow]Label Studio not installed.[/yellow]")
        if click.confirm("Install Label Studio now?", default=True):
            if not install_labelstudio():
                console.print("[red]Installation failed. Install manually: pip install label-studio[/red]")
                sys.exit(1)
        else:
            sys.exit(1)

    data_path = PathLib(data_dir)
    if not data_path.exists():
        console.print(f"[red]Data directory not found: {data_path}[/red]")
        console.print("[dim]Run 'stamp-tools train prepare' first.[/dim]")
        sys.exit(1)

    console.print(f"Starting Label Studio on port {port}...")
    console.print(f"Data directory: {data_path.absolute()}")
    console.print()
    console.print("[yellow]Press Ctrl+C to stop Label Studio[/yellow]")

    try:
        process = start_labelstudio(data_path, port, open_browser=True)
        process.wait()
    except KeyboardInterrupt:
        console.print("\n[yellow]Label Studio stopped.[/yellow]")


@train.command("import")
@click.option("--annotations", type=click.Path(exists=True), required=True, help="Label Studio JSON export")
@click.option("--images", type=click.Path(exists=True), default="data/training/raw", help="Images directory")
@click.option("--output", type=click.Path(), default="data/training", help="Output dataset directory")
@click.option("--split", type=float, default=0.8, help="Train/val split ratio")
def train_import(annotations: str, images: str, output: str, split: float) -> None:
    """Import Label Studio annotations to YOLO format.

    Converts exported annotations to YOLO training format.

    Example:
        stamp-tools train import --annotations "data/training/annotations.json"
    """
    from pathlib import Path as PathLib

    from src.training.labelstudio import export_to_yolo_format

    console.print(Panel("Import Annotations", style="bold blue"))

    annotations_path = PathLib(annotations)
    images_path = PathLib(images)
    output_path = PathLib(output)

    console.print(f"[bold]Annotations:[/bold] {annotations_path}")
    console.print(f"[bold]Images:[/bold] {images_path}")
    console.print(f"[bold]Output:[/bold] {output_path}")
    console.print(f"[bold]Train/Val split:[/bold] {split:.0%} / {1-split:.0%}")
    console.print()

    stats = export_to_yolo_format(
        annotations_path,
        images_path,
        output_path,
        train_split=split,
    )

    table = Table(show_header=True, header_style="bold")
    table.add_column("Metric")
    table.add_column("Count", justify="right")

    table.add_row("Training images", str(stats["train"]))
    table.add_row("Validation images", str(stats["val"]))
    table.add_row("Total bounding boxes", str(stats["total_boxes"]))

    console.print(table)
    console.print(Panel(
        f"[green]Import complete![/green]\n"
        f"Dataset ready at: {output_path}\n"
        f"Run 'stamp-tools train run' to start training.",
        style="green",
    ))


@train.command("run")
@click.option("--dataset", type=click.Path(exists=True), default="data/training", help="Dataset directory")
@click.option("--epochs", default=100, help="Number of training epochs")
@click.option("--batch", default=16, help="Batch size")
@click.option("--model-size", type=click.Choice(["n", "s", "m", "l"]), default="n",
              help="Model size: n=nano, s=small, m=medium, l=large")
@click.option("--device", default="cpu", help="Device: cpu, 0 (GPU), 0,1 (multi-GPU)")
def train_run(dataset: str, epochs: int, batch: int, model_size: str, device: str) -> None:
    """Train YOLO model on stamp dataset.

    Trains a YOLOv8 model for stamp detection.

    Example:
        stamp-tools train run --epochs 50
        stamp-tools train run --device 0 --batch 32  # GPU training
    """
    from pathlib import Path as PathLib

    from src.training.trainer import StampTrainer, TrainingConfig

    console.print(Panel("YOLO Training", style="bold blue"))

    dataset_path = PathLib(dataset)
    dataset_yaml = dataset_path / "dataset.yaml"

    if not dataset_yaml.exists():
        console.print(f"[red]Dataset config not found: {dataset_yaml}[/red]")
        console.print("[dim]Run 'stamp-tools train import' first.[/dim]")
        sys.exit(1)

    # Check dataset stats
    from src.training.dataset import StampDataset
    ds = StampDataset(dataset_path)
    stats = ds.get_stats()

    if stats["total_images"] < 10:
        console.print(f"[yellow]Warning: Only {stats['total_images']} images in dataset.[/yellow]")
        console.print("[dim]For good results, label at least 100-200 images.[/dim]")
        if not click.confirm("Continue anyway?", default=False):
            sys.exit(0)

    console.print(f"[bold]Dataset:[/bold] {dataset_yaml}")
    console.print(f"[bold]Images:[/bold] {stats['total_images']} ({stats['train_images']} train, {stats['val_images']} val)")
    console.print(f"[bold]Model:[/bold] YOLOv8{model_size}")
    console.print(f"[bold]Epochs:[/bold] {epochs}")
    console.print(f"[bold]Batch size:[/bold] {batch}")
    console.print(f"[bold]Device:[/bold] {device}")
    console.print()

    config = TrainingConfig(
        dataset_yaml=dataset_yaml,
        base_model=f"yolov8{model_size}.pt",
        epochs=epochs,
        batch_size=batch,
        device=device,
    )

    console.print("[yellow]Starting training... This may take a while.[/yellow]")
    console.print("[dim]Training progress will be shown by YOLO.[/dim]")
    console.print()

    try:
        trainer = StampTrainer(config)
        result = trainer.train()

        console.print()
        console.print(Panel(
            f"[green]Training complete![/green]\n\n"
            f"[bold]Best model:[/bold] {result.best_model_path}\n"
            f"[bold]mAP50:[/bold] {result.map50:.3f}\n"
            f"[bold]mAP50-95:[/bold] {result.map50_95:.3f}\n\n"
            f"To use this model:\n"
            f"  stamp-tools train export --model {result.best_model_path}",
            title="Training Results",
            style="green",
        ))

    except KeyboardInterrupt:
        console.print("\n[yellow]Training interrupted.[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Training failed: {e}[/red]")
        sys.exit(1)


@train.command("export")
@click.option("--model", type=click.Path(exists=True), required=True, help="Path to trained model")
@click.option("--output", type=click.Path(), default=None, help="Output path (default: models/stamp_detector.pt)")
def train_export(model: str, output: str) -> None:
    """Export trained model for use in detection.

    Copies the trained model to the models directory for use with identify commands.

    Example:
        stamp-tools train export --model "runs/detect/stamp_detection/train/weights/best.pt"
    """
    from pathlib import Path as PathLib

    from src.training.trainer import StampTrainer

    console.print(Panel("Export Model", style="bold blue"))

    model_path = PathLib(model)
    output_path = PathLib(output) if output else None

    trainer = StampTrainer()
    exported = trainer.export_model(model_path, output_path)

    console.print(f"[green]✓[/green] Model exported to: {exported}")
    console.print()
    console.print("[bold]To use the trained model:[/bold]")
    console.print(f"  Update YOLO_MODEL_PATH in .env.app to: {exported}")
    console.print("  Or use: stamp-tools identify image --path photo.jpg")


@train.command("evaluate")
@click.option("--model", type=click.Path(exists=True), required=True, help="Path to trained model")
@click.option("--dataset", type=click.Path(exists=True), default="data/training", help="Dataset directory")
def train_evaluate(model: str, dataset: str) -> None:
    """Evaluate trained model on validation set.

    Example:
        stamp-tools train evaluate --model "models/stamp_detector.pt"
    """
    from pathlib import Path as PathLib

    from src.training.trainer import StampTrainer

    console.print(Panel("Evaluate Model", style="bold blue"))

    model_path = PathLib(model)
    dataset_path = PathLib(dataset)
    dataset_yaml = dataset_path / "dataset.yaml"

    if not dataset_yaml.exists():
        console.print(f"[red]Dataset config not found: {dataset_yaml}[/red]")
        sys.exit(1)

    trainer = StampTrainer()
    metrics = trainer.evaluate(model_path, dataset_yaml)

    table = Table(show_header=True, header_style="bold")
    table.add_column("Metric")
    table.add_column("Value", justify="right")

    table.add_row("mAP@50", f"{metrics['mAP50']:.3f}")
    table.add_row("mAP@50-95", f"{metrics['mAP50-95']:.3f}")
    table.add_row("Precision", f"{metrics['precision']:.3f}")
    table.add_row("Recall", f"{metrics['recall']:.3f}")

    console.print(table)


@train.command("test")
@click.option("--model", type=click.Path(exists=True), required=True, help="Path to trained model")
@click.option("--image", type=click.Path(exists=True), required=True, help="Test image path")
@click.option("--save", type=click.Path(), default=None, help="Save annotated result")
def train_test(model: str, image: str, save: str) -> None:
    """Test model on a single image.

    Example:
        stamp-tools train test --model "models/stamp_detector.pt" --image "test.jpg"
    """
    from pathlib import Path as PathLib

    import cv2

    from src.training.trainer import StampTrainer

    console.print(Panel("Test Model", style="bold blue"))

    model_path = PathLib(model)
    image_path = PathLib(image)

    trainer = StampTrainer()
    result = trainer.predict_test(model_path, image_path)

    console.print(f"[bold]Image:[/bold] {image_path}")
    console.print(f"[bold]Stamps detected:[/bold] {result['count']}")
    console.print()

    for i, det in enumerate(result["detections"]):
        bbox = det["bbox"]
        conf = det["confidence"]
        console.print(f"  [{i+1}] Box: ({bbox[0]}, {bbox[1]}) - ({bbox[2]}, {bbox[3]}) | Confidence: {conf:.0%}")

    if save and result["count"] > 0:
        # Draw boxes and save
        img = cv2.imread(str(image_path))
        for det in result["detections"]:
            x1, y1, x2, y2 = det["bbox"]
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, f"{det['confidence']:.0%}", (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imwrite(save, img)
        console.print(f"\n[green]✓[/green] Saved annotated image to: {save}")


@train.command("status")
@click.option("--dataset", type=click.Path(), default="data/training", help="Dataset directory")
def train_status(dataset: str) -> None:
    """Show training dataset status.

    Example:
        stamp-tools train status
    """
    from pathlib import Path as PathLib

    console.print(Panel("Training Status", style="bold blue"))

    dataset_path = PathLib(dataset)

    if not dataset_path.exists():
        console.print(f"[yellow]Dataset directory not found: {dataset_path}[/yellow]")
        console.print("[dim]Run 'stamp-tools train prepare' to get started.[/dim]")
        return

    # Check for raw images
    raw_dir = dataset_path / "raw"
    raw_images = 0
    if raw_dir.exists():
        raw_images = len(list(raw_dir.glob("*.[jJ][pP]*"))) + len(list(raw_dir.glob("*.[pP][nN][gG]")))

    # Check for YOLO dataset
    from src.training.dataset import StampDataset
    try:
        ds = StampDataset(dataset_path)
        stats = ds.get_stats()
    except Exception:
        stats = {"train_images": 0, "val_images": 0, "total_images": 0, "total_annotations": 0}

    # Check for trained models
    models_dir = PathLib("runs/detect/stamp_detection")
    trained_models = []
    if models_dir.exists():
        for run_dir in models_dir.iterdir():
            best_model = run_dir / "weights" / "best.pt"
            if best_model.exists():
                trained_models.append(best_model)

    table = Table(show_header=True, header_style="bold")
    table.add_column("Stage")
    table.add_column("Status")
    table.add_column("Details")

    # Raw images
    if raw_images > 0:
        table.add_row("1. Raw Images", "[green]Ready[/green]", f"{raw_images} images in {raw_dir}")
    else:
        table.add_row("1. Raw Images", "[yellow]Pending[/yellow]", "Run: stamp-tools train prepare --source <dir>")

    # Annotations
    annotations_file = dataset_path / "raw" / "annotations.json"
    if annotations_file.exists():
        table.add_row("2. Annotations", "[green]Exported[/green]", str(annotations_file))
    elif raw_images > 0:
        table.add_row("2. Annotations", "[yellow]Pending[/yellow]", "Run: stamp-tools train labelstudio")
    else:
        table.add_row("2. Annotations", "[dim]Waiting[/dim]", "Need raw images first")

    # YOLO Dataset
    if stats["total_images"] > 0:
        table.add_row("3. YOLO Dataset", "[green]Ready[/green]",
                     f"{stats['total_images']} images, {stats['total_annotations']} boxes")
    elif annotations_file.exists():
        table.add_row("3. YOLO Dataset", "[yellow]Pending[/yellow]", "Run: stamp-tools train import --annotations ...")
    else:
        table.add_row("3. YOLO Dataset", "[dim]Waiting[/dim]", "Need annotations first")

    # Trained Model
    if trained_models:
        table.add_row("4. Trained Model", "[green]Available[/green]", str(trained_models[-1]))
    elif stats["total_images"] > 0:
        table.add_row("4. Trained Model", "[yellow]Pending[/yellow]", "Run: stamp-tools train run")
    else:
        table.add_row("4. Trained Model", "[dim]Waiting[/dim]", "Need YOLO dataset first")

    console.print(table)


# =============================================================================
# Migrate Command Group
# =============================================================================


@cli.group()
def migrate() -> None:
    """LASTDODO migration commands."""
    pass


@migrate.command("match")
def migrate_match() -> None:
    """Match LASTDODO items to Colnect catalog.

    Matches by catalog number (Michel, Yvert, Scott, SG, Fisher).

    Example:
        stamp-tools migrate match
    """
    console.print("[yellow]Migration matching not yet implemented (Phase 6)[/yellow]")
    console.print("This will match LASTDODO items to Colnect stamps.")


@migrate.command("import")
@click.option("--dry-run", is_flag=True, default=True, help="Simulate without updating")
def migrate_import(dry_run: bool) -> None:
    """Import matched items to Colnect.

    Example:
        stamp-tools migrate import --dry-run
        stamp-tools migrate import  # Live import
    """
    console.print("[yellow]Migration import not yet implemented (Phase 6)[/yellow]")

    if dry_run:
        console.print("DRY RUN - No changes will be made to Colnect.")
    else:
        console.print("LIVE MODE - Will update Colnect collection.")


@migrate.command("review")
def migrate_review() -> None:
    """Manual review queue for unmatched items.

    Example:
        stamp-tools migrate review
    """
    console.print("[yellow]Migration review not yet implemented (Phase 6)[/yellow]")
    console.print("This will show unmatched items for manual review.")


@migrate.command("status")
def migrate_status() -> None:
    """Show migration status."""
    console.print(Panel("Migration Status", style="bold blue"))

    try:
        stats = get_database_stats()

        table = Table(show_header=True, header_style="bold")
        table.add_column("Category")
        table.add_column("Count", justify="right")

        table.add_row("Catalog Stamps", str(stats["catalog_stamps"]))
        table.add_row("LASTDODO Items", str(stats["lastdodo_items"]))
        table.add_row("Import Tasks", str(stats["import_tasks"]))

        console.print(table)

        if stats["import_task_breakdown"]:
            console.print("\n[bold]Import Task Breakdown:[/bold]")
            breakdown_table = Table(show_header=True, header_style="bold")
            breakdown_table.add_column("Status")
            breakdown_table.add_column("Count", justify="right")

            for status, count in sorted(stats["import_task_breakdown"].items()):
                breakdown_table.add_row(status, str(count))

            console.print(breakdown_table)
    except Exception as e:
        console.print(f"[red]Error getting status: {e}[/red]")
        console.print("[dim]Run 'stamp-tools init' to initialize the database.[/dim]")


# =============================================================================
# Config Command Group
# =============================================================================


@cli.group()
def config() -> None:
    """Configuration commands."""
    pass


@config.command("show")
def config_show() -> None:
    """Show current configuration."""
    settings = get_settings()

    console.print(Panel("Current Configuration", style="bold blue"))

    table = Table(show_header=True, header_style="bold")
    table.add_column("Setting")
    table.add_column("Value")

    # Database
    table.add_row("[bold]Database[/bold]", "")
    table.add_row("DATABASE_PATH", settings.DATABASE_PATH)

    # Scraping
    table.add_row("[bold]Scraping[/bold]", "")
    table.add_row("SCRAPE_DELAY_SECONDS", str(settings.SCRAPE_DELAY_SECONDS))
    table.add_row("SCRAPE_RETRY_COUNT", str(settings.SCRAPE_RETRY_COUNT))
    table.add_row("SCRAPE_ERROR_BEHAVIOR", settings.SCRAPE_ERROR_BEHAVIOR)

    # RAG
    table.add_row("[bold]RAG[/bold]", "")
    table.add_row("RAG_MATCH_AUTO_THRESHOLD", str(settings.RAG_MATCH_AUTO_THRESHOLD))
    table.add_row("RAG_MATCH_MIN_THRESHOLD", str(settings.RAG_MATCH_MIN_THRESHOLD))
    table.add_row("EMBEDDING_MODEL", settings.EMBEDDING_MODEL)

    # Vision
    table.add_row("[bold]Vision[/bold]", "")
    table.add_row("GROQ_MODEL", settings.GROQ_MODEL)
    table.add_row("GROQ_RATE_LIMIT_PER_MINUTE", str(settings.GROQ_RATE_LIMIT_PER_MINUTE))

    # YOLO
    table.add_row("[bold]Object Detection[/bold]", "")
    table.add_row("YOLO_MODEL_PATH", settings.YOLO_MODEL_PATH)
    table.add_row("YOLO_CONFIDENCE_THRESHOLD", str(settings.YOLO_CONFIDENCE_THRESHOLD))

    # Browser
    table.add_row("[bold]Browser Automation[/bold]", "")
    table.add_row("CHROME_CDP_URL", settings.CHROME_CDP_URL)

    # API Keys (masked)
    table.add_row("[bold]API Keys[/bold]", "")
    api_status = settings.validate_api_keys()
    for api, configured in api_status.items():
        status = "[green]configured[/green]" if configured else "[yellow]not set[/yellow]"
        table.add_row(f"{api.upper()}_API_KEY", status)

    console.print(table)


@config.command("validate")
def config_validate() -> None:
    """Validate all settings and connections."""
    console.print(Panel("Validating Configuration", style="bold blue"))

    settings = get_settings()
    issues = []

    # Check required paths
    console.print("\n[bold]Checking paths...[/bold]")

    prompt_path = Path(settings.VISION_PROMPT_FILE)
    if prompt_path.exists():
        console.print(f"   [green]✓[/green] Vision prompt: {prompt_path}")
    else:
        console.print(f"   [red]✗[/red] Vision prompt missing: {prompt_path}")
        issues.append("Vision prompt file not found")

    # Check API keys
    console.print("\n[bold]Checking API keys...[/bold]")
    api_status = settings.validate_api_keys()

    required_apis = ["supabase", "openai", "groq"]
    for api in required_apis:
        if api_status.get(api):
            console.print(f"   [green]✓[/green] {api.upper()} configured")
        else:
            console.print(f"   [red]✗[/red] {api.upper()} not configured")
            issues.append(f"{api.upper()} API key missing")

    # Check thresholds
    console.print("\n[bold]Checking thresholds...[/bold]")
    if 0 <= settings.RAG_MATCH_AUTO_THRESHOLD <= 1:
        console.print(f"   [green]✓[/green] RAG_MATCH_AUTO_THRESHOLD: {settings.RAG_MATCH_AUTO_THRESHOLD}")
    else:
        console.print(f"   [red]✗[/red] RAG_MATCH_AUTO_THRESHOLD out of range")
        issues.append("RAG_MATCH_AUTO_THRESHOLD must be between 0 and 1")

    if 0 <= settings.RAG_MATCH_MIN_THRESHOLD <= 1:
        console.print(f"   [green]✓[/green] RAG_MATCH_MIN_THRESHOLD: {settings.RAG_MATCH_MIN_THRESHOLD}")
    else:
        console.print(f"   [red]✗[/red] RAG_MATCH_MIN_THRESHOLD out of range")
        issues.append("RAG_MATCH_MIN_THRESHOLD must be between 0 and 1")

    if settings.RAG_MATCH_MIN_THRESHOLD < settings.RAG_MATCH_AUTO_THRESHOLD:
        console.print("   [green]✓[/green] Threshold ordering correct")
    else:
        console.print("   [red]✗[/red] MIN_THRESHOLD should be less than AUTO_THRESHOLD")
        issues.append("Threshold ordering incorrect")

    # Summary
    console.print("\n" + "=" * 50)
    if issues:
        console.print(Panel(
            f"[red]Validation failed with {len(issues)} issue(s)[/red]\n"
            + "\n".join(f"  - {i}" for i in issues),
            title="Result",
            style="red",
        ))
        sys.exit(1)
    else:
        console.print(Panel(
            "[green]All validations passed![/green]",
            title="Result",
            style="green",
        ))


# =============================================================================
# Entry Point
# =============================================================================


def main() -> None:
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
