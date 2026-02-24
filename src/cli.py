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
def scrape_colnect(themes: str, country: str, year: int, resume: bool) -> None:
    """Scrape Colnect for space-themed stamps.

    Examples:
        stamp-tools scrape colnect
        stamp-tools scrape colnect --themes "Space,Rockets"
        stamp-tools scrape colnect --country "Australia" --year 2021
        stamp-tools scrape colnect --resume
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
                    )
                return total
            except Exception as e:
                logger.error(f"Scraping failed: {e}")
                raise

    try:
        total = asyncio.run(run_scraper())
        console.print()
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


@rag.command("index")
@click.option("--country", default=None, help="Filter by country")
@click.option("--year", type=int, default=None, help="Filter by year")
@click.option("--regenerate", is_flag=True, help="Regenerate descriptions")
def rag_index(country: str, year: int, regenerate: bool) -> None:
    """Index scraped stamps into Supabase RAG.

    Examples:
        stamp-tools rag index
        stamp-tools rag index --country "Australia" --year 2021
        stamp-tools rag index --regenerate
    """
    console.print("[yellow]RAG indexer not yet implemented (Phase 3)[/yellow]")
    console.print("This will generate descriptions and embeddings for stamps.")

    if country:
        console.print(f"Country filter: {country}")
    if year:
        console.print(f"Year filter: {year}")
    if regenerate:
        console.print("Regenerating all descriptions...")


@rag.command("search")
@click.option("--query", required=True, help="Search query")
@click.option("--limit", default=5, help="Number of results")
def rag_search(query: str, limit: int) -> None:
    """Manual similarity search for testing.

    Example:
        stamp-tools rag search --query "rocket launch astronaut"
    """
    console.print("[yellow]RAG search not yet implemented (Phase 3)[/yellow]")
    console.print(f"Searching for: {query}")
    console.print(f"Limit: {limit}")


@rag.command("stats")
def rag_stats() -> None:
    """Show RAG database statistics."""
    console.print("[yellow]RAG stats not yet implemented (Phase 3)[/yellow]")
    console.print("This will show statistics about the RAG index.")


# =============================================================================
# Identify Command Group
# =============================================================================


@cli.group()
def identify() -> None:
    """Stamp identification commands."""
    pass


@identify.command("camera")
@click.option("--add-to-colnect", is_flag=True, help="Auto-add matches to Colnect")
def identify_camera(add_to_colnect: bool) -> None:
    """Identify stamps from camera.

    Captures image from camera, detects stamps, and identifies them
    using the RAG database.

    Example:
        stamp-tools identify camera
        stamp-tools identify camera --add-to-colnect
    """
    console.print("[yellow]Camera identification not yet implemented (Phase 4)[/yellow]")
    console.print("This will capture from camera and identify stamps.")

    if add_to_colnect:
        console.print("Will add confirmed matches to Colnect collection.")


@identify.command("image")
@click.option("--path", required=True, type=click.Path(exists=True), help="Image path")
@click.option("--add-to-colnect", is_flag=True, help="Auto-add matches to Colnect")
def identify_image(path: str, add_to_colnect: bool) -> None:
    """Identify stamps from image file.

    Example:
        stamp-tools identify image --path "photo.jpg"
    """
    console.print("[yellow]Image identification not yet implemented (Phase 4)[/yellow]")
    console.print(f"Processing image: {path}")

    if add_to_colnect:
        console.print("Will add confirmed matches to Colnect collection.")


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
