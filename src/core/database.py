"""SQLite database operations for Stamp Collection Toolset.

Tables:
- catalog_stamps: Stamps scraped from Colnect
- lastdodo_items: Items scraped from LASTDODO collection
- import_tasks: Migration tracking from LASTDODO to Colnect
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from src.core.config import get_settings
from src.core.errors import DatabaseError, DuplicateRecordError, RecordNotFoundError

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class CatalogStamp:
    """Stamp data scraped from Colnect catalog."""

    colnect_id: str
    colnect_url: str
    title: str
    country: str
    year: int
    image_url: str
    themes: list[str] = field(default_factory=list)
    catalog_codes: dict[str, str] = field(default_factory=dict)
    scraped_at: Optional[datetime] = None


@dataclass
class LastdodoItem:
    """Item scraped from LASTDODO collection."""

    lastdodo_id: str
    title: str
    condition: str
    condition_mapped: str
    quantity: int = 1
    country: Optional[str] = None
    year: Optional[int] = None
    michel_number: Optional[str] = None
    yvert_number: Optional[str] = None
    scott_number: Optional[str] = None
    sg_number: Optional[str] = None
    fisher_number: Optional[str] = None
    value_eur: Optional[float] = None
    image_url: Optional[str] = None
    scraped_at: Optional[datetime] = None


@dataclass
class ImportTask:
    """Migration task tracking LASTDODO to Colnect import."""

    id: str
    lastdodo_id: str
    status: str = "pending"  # pending, matched, needs_review, imported, failed, skipped
    colnect_id: Optional[str] = None
    match_method: Optional[str] = None  # michel, yvert, scott, sg, fisher, manual
    condition_final: Optional[str] = None
    quantity_final: Optional[int] = None
    comment: Optional[str] = None
    error_message: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    imported_at: Optional[datetime] = None
    dry_run: bool = False


# =============================================================================
# Schema Definition
# =============================================================================

SCHEMA_SQL = """
-- CatalogStamp: Stamps scraped from Colnect
CREATE TABLE IF NOT EXISTS catalog_stamps (
    colnect_id TEXT PRIMARY KEY,
    colnect_url TEXT NOT NULL,
    title TEXT NOT NULL,
    country TEXT NOT NULL,
    year INTEGER NOT NULL,
    themes TEXT,
    image_url TEXT NOT NULL,
    catalog_codes TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LastdodoItem: Items scraped from LASTDODO collection
CREATE TABLE IF NOT EXISTS lastdodo_items (
    lastdodo_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    country TEXT,
    year INTEGER,
    michel_number TEXT,
    yvert_number TEXT,
    scott_number TEXT,
    sg_number TEXT,
    fisher_number TEXT,
    condition TEXT NOT NULL,
    condition_mapped TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    value_eur REAL,
    image_url TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ImportTask: Migration tracking
CREATE TABLE IF NOT EXISTS import_tasks (
    id TEXT PRIMARY KEY,
    lastdodo_id TEXT NOT NULL,
    colnect_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    match_method TEXT,
    condition_final TEXT,
    quantity_final INTEGER,
    comment TEXT,
    error_message TEXT,
    reviewed_at TIMESTAMP,
    imported_at TIMESTAMP,
    dry_run INTEGER DEFAULT 0,
    FOREIGN KEY (lastdodo_id) REFERENCES lastdodo_items(lastdodo_id),
    FOREIGN KEY (colnect_id) REFERENCES catalog_stamps(colnect_id),
    CHECK (status IN ('pending', 'matched', 'needs_review', 'imported', 'failed', 'skipped'))
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_catalog_country_year ON catalog_stamps(country, year);
CREATE INDEX IF NOT EXISTS idx_catalog_country ON catalog_stamps(country);
CREATE INDEX IF NOT EXISTS idx_catalog_year ON catalog_stamps(year);
CREATE INDEX IF NOT EXISTS idx_import_status ON import_tasks(status);
CREATE INDEX IF NOT EXISTS idx_lastdodo_michel ON lastdodo_items(michel_number);
CREATE INDEX IF NOT EXISTS idx_lastdodo_yvert ON lastdodo_items(yvert_number);
CREATE INDEX IF NOT EXISTS idx_lastdodo_scott ON lastdodo_items(scott_number);
"""


# =============================================================================
# Database Connection
# =============================================================================


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Get SQLite database connection as context manager.

    Returns:
        SQLite connection with row factory set to sqlite3.Row

    Example:
        with get_connection() as conn:
            cursor = conn.execute("SELECT * FROM catalog_stamps")
            rows = cursor.fetchall()
    """
    settings = get_settings()
    db_path = Path(settings.DATABASE_PATH)

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise DatabaseError(f"Database operation failed: {e}") from e
    finally:
        conn.close()


def init_database() -> None:
    """Initialize database with schema.

    Creates tables and indexes if they don't exist.
    """
    settings = get_settings()
    db_path = Path(settings.DATABASE_PATH)

    logger.info(f"Initializing database at {db_path}")

    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)

    logger.info("Database initialized successfully")


# =============================================================================
# CatalogStamp Operations
# =============================================================================


def upsert_catalog_stamp(stamp: CatalogStamp) -> None:
    """Insert or update a catalog stamp.

    Args:
        stamp: CatalogStamp to upsert
    """
    sql = """
    INSERT INTO catalog_stamps (
        colnect_id, colnect_url, title, country, year,
        themes, image_url, catalog_codes, scraped_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(colnect_id) DO UPDATE SET
        colnect_url = excluded.colnect_url,
        title = excluded.title,
        country = excluded.country,
        year = excluded.year,
        themes = excluded.themes,
        image_url = excluded.image_url,
        catalog_codes = excluded.catalog_codes,
        scraped_at = excluded.scraped_at
    """

    with get_connection() as conn:
        conn.execute(
            sql,
            (
                stamp.colnect_id,
                stamp.colnect_url,
                stamp.title,
                stamp.country,
                stamp.year,
                json.dumps(stamp.themes) if stamp.themes else None,
                stamp.image_url,
                json.dumps(stamp.catalog_codes) if stamp.catalog_codes else None,
                stamp.scraped_at or datetime.now(),
            ),
        )

    logger.debug(f"Upserted catalog stamp: {stamp.colnect_id}")


def get_catalog_stamp(colnect_id: str) -> CatalogStamp:
    """Get a catalog stamp by ID.

    Args:
        colnect_id: Colnect stamp ID

    Returns:
        CatalogStamp

    Raises:
        RecordNotFoundError: If stamp not found
    """
    sql = "SELECT * FROM catalog_stamps WHERE colnect_id = ?"

    with get_connection() as conn:
        row = conn.execute(sql, (colnect_id,)).fetchone()

    if not row:
        raise RecordNotFoundError(f"Catalog stamp not found: {colnect_id}")

    return _row_to_catalog_stamp(row)


def get_catalog_stamps(
    country: Optional[str] = None,
    year: Optional[int] = None,
    limit: Optional[int] = None,
    offset: int = 0,
) -> list[CatalogStamp]:
    """Query catalog stamps with optional filters.

    Args:
        country: Filter by country name
        year: Filter by year of issue
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of CatalogStamp objects
    """
    sql = "SELECT * FROM catalog_stamps WHERE 1=1"
    params: list = []

    if country:
        sql += " AND country = ?"
        params.append(country)

    if year:
        sql += " AND year = ?"
        params.append(year)

    sql += " ORDER BY country, year, title"

    if limit:
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [_row_to_catalog_stamp(row) for row in rows]


def count_catalog_stamps(
    country: Optional[str] = None,
    year: Optional[int] = None,
) -> int:
    """Count catalog stamps with optional filters.

    Args:
        country: Filter by country name
        year: Filter by year of issue

    Returns:
        Number of matching stamps
    """
    sql = "SELECT COUNT(*) FROM catalog_stamps WHERE 1=1"
    params: list = []

    if country:
        sql += " AND country = ?"
        params.append(country)

    if year:
        sql += " AND year = ?"
        params.append(year)

    with get_connection() as conn:
        result = conn.execute(sql, params).fetchone()

    return result[0] if result else 0


def get_catalog_countries() -> list[str]:
    """Get list of unique countries in catalog."""
    sql = "SELECT DISTINCT country FROM catalog_stamps ORDER BY country"

    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()

    return [row[0] for row in rows]


def get_catalog_years() -> list[int]:
    """Get list of unique years in catalog."""
    sql = "SELECT DISTINCT year FROM catalog_stamps ORDER BY year"

    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()

    return [row[0] for row in rows]


def _row_to_catalog_stamp(row: sqlite3.Row) -> CatalogStamp:
    """Convert database row to CatalogStamp."""
    return CatalogStamp(
        colnect_id=row["colnect_id"],
        colnect_url=row["colnect_url"],
        title=row["title"],
        country=row["country"],
        year=row["year"],
        image_url=row["image_url"],
        themes=json.loads(row["themes"]) if row["themes"] else [],
        catalog_codes=json.loads(row["catalog_codes"]) if row["catalog_codes"] else {},
        scraped_at=datetime.fromisoformat(row["scraped_at"])
        if row["scraped_at"]
        else None,
    )


# =============================================================================
# LastdodoItem Operations
# =============================================================================


def upsert_lastdodo_item(item: LastdodoItem) -> None:
    """Insert or update a LASTDODO item.

    Args:
        item: LastdodoItem to upsert
    """
    sql = """
    INSERT INTO lastdodo_items (
        lastdodo_id, title, country, year,
        michel_number, yvert_number, scott_number, sg_number, fisher_number,
        condition, condition_mapped, quantity, value_eur, image_url, scraped_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(lastdodo_id) DO UPDATE SET
        title = excluded.title,
        country = excluded.country,
        year = excluded.year,
        michel_number = excluded.michel_number,
        yvert_number = excluded.yvert_number,
        scott_number = excluded.scott_number,
        sg_number = excluded.sg_number,
        fisher_number = excluded.fisher_number,
        condition = excluded.condition,
        condition_mapped = excluded.condition_mapped,
        quantity = excluded.quantity,
        value_eur = excluded.value_eur,
        image_url = excluded.image_url,
        scraped_at = excluded.scraped_at
    """

    with get_connection() as conn:
        conn.execute(
            sql,
            (
                item.lastdodo_id,
                item.title,
                item.country,
                item.year,
                item.michel_number,
                item.yvert_number,
                item.scott_number,
                item.sg_number,
                item.fisher_number,
                item.condition,
                item.condition_mapped,
                item.quantity,
                item.value_eur,
                item.image_url,
                item.scraped_at or datetime.now(),
            ),
        )

    logger.debug(f"Upserted LASTDODO item: {item.lastdodo_id}")


def get_lastdodo_item(lastdodo_id: str) -> LastdodoItem:
    """Get a LASTDODO item by ID.

    Args:
        lastdodo_id: LASTDODO item ID

    Returns:
        LastdodoItem

    Raises:
        RecordNotFoundError: If item not found
    """
    sql = "SELECT * FROM lastdodo_items WHERE lastdodo_id = ?"

    with get_connection() as conn:
        row = conn.execute(sql, (lastdodo_id,)).fetchone()

    if not row:
        raise RecordNotFoundError(f"LASTDODO item not found: {lastdodo_id}")

    return _row_to_lastdodo_item(row)


def get_lastdodo_items(limit: Optional[int] = None, offset: int = 0) -> list[LastdodoItem]:
    """Get all LASTDODO items.

    Args:
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of LastdodoItem objects
    """
    sql = "SELECT * FROM lastdodo_items ORDER BY title"
    params: list = []

    if limit:
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [_row_to_lastdodo_item(row) for row in rows]


def count_lastdodo_items() -> int:
    """Count total LASTDODO items."""
    sql = "SELECT COUNT(*) FROM lastdodo_items"

    with get_connection() as conn:
        result = conn.execute(sql).fetchone()

    return result[0] if result else 0


def _row_to_lastdodo_item(row: sqlite3.Row) -> LastdodoItem:
    """Convert database row to LastdodoItem."""
    return LastdodoItem(
        lastdodo_id=row["lastdodo_id"],
        title=row["title"],
        country=row["country"],
        year=row["year"],
        michel_number=row["michel_number"],
        yvert_number=row["yvert_number"],
        scott_number=row["scott_number"],
        sg_number=row["sg_number"],
        fisher_number=row["fisher_number"],
        condition=row["condition"],
        condition_mapped=row["condition_mapped"],
        quantity=row["quantity"],
        value_eur=row["value_eur"],
        image_url=row["image_url"],
        scraped_at=datetime.fromisoformat(row["scraped_at"])
        if row["scraped_at"]
        else None,
    )


# =============================================================================
# ImportTask Operations
# =============================================================================


def create_import_task(task: ImportTask) -> None:
    """Create a new import task.

    Args:
        task: ImportTask to create

    Raises:
        DuplicateRecordError: If task with same ID exists
    """
    sql = """
    INSERT INTO import_tasks (
        id, lastdodo_id, colnect_id, status, match_method,
        condition_final, quantity_final, comment, error_message,
        reviewed_at, imported_at, dry_run
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    try:
        with get_connection() as conn:
            conn.execute(
                sql,
                (
                    task.id,
                    task.lastdodo_id,
                    task.colnect_id,
                    task.status,
                    task.match_method,
                    task.condition_final,
                    task.quantity_final,
                    task.comment,
                    task.error_message,
                    task.reviewed_at,
                    task.imported_at,
                    1 if task.dry_run else 0,
                ),
            )
    except sqlite3.IntegrityError as e:
        raise DuplicateRecordError(f"Import task already exists: {task.id}") from e

    logger.debug(f"Created import task: {task.id}")


def update_import_task(task_id: str, **fields) -> None:
    """Update import task fields.

    Args:
        task_id: Task ID to update
        **fields: Fields to update (status, colnect_id, etc.)

    Raises:
        RecordNotFoundError: If task not found
    """
    if not fields:
        return

    # Build dynamic UPDATE statement
    set_clauses = [f"{key} = ?" for key in fields.keys()]
    sql = f"UPDATE import_tasks SET {', '.join(set_clauses)} WHERE id = ?"

    values = list(fields.values())
    values.append(task_id)

    with get_connection() as conn:
        cursor = conn.execute(sql, values)

    if cursor.rowcount == 0:
        raise RecordNotFoundError(f"Import task not found: {task_id}")

    logger.debug(f"Updated import task {task_id}: {fields}")


def get_import_task(task_id: str) -> ImportTask:
    """Get an import task by ID.

    Args:
        task_id: Import task ID

    Returns:
        ImportTask

    Raises:
        RecordNotFoundError: If task not found
    """
    sql = "SELECT * FROM import_tasks WHERE id = ?"

    with get_connection() as conn:
        row = conn.execute(sql, (task_id,)).fetchone()

    if not row:
        raise RecordNotFoundError(f"Import task not found: {task_id}")

    return _row_to_import_task(row)


def get_import_tasks(
    status: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
) -> list[ImportTask]:
    """Get import tasks with optional status filter.

    Args:
        status: Filter by status (pending, matched, etc.)
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of ImportTask objects
    """
    sql = "SELECT * FROM import_tasks WHERE 1=1"
    params: list = []

    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY id"

    if limit:
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [_row_to_import_task(row) for row in rows]


def count_import_tasks(status: Optional[str] = None) -> int:
    """Count import tasks with optional status filter.

    Args:
        status: Filter by status

    Returns:
        Number of matching tasks
    """
    sql = "SELECT COUNT(*) FROM import_tasks WHERE 1=1"
    params: list = []

    if status:
        sql += " AND status = ?"
        params.append(status)

    with get_connection() as conn:
        result = conn.execute(sql, params).fetchone()

    return result[0] if result else 0


def get_import_task_stats() -> dict[str, int]:
    """Get import task statistics by status.

    Returns:
        Dict mapping status to count
    """
    sql = "SELECT status, COUNT(*) FROM import_tasks GROUP BY status"

    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()

    return {row[0]: row[1] for row in rows}


def _row_to_import_task(row: sqlite3.Row) -> ImportTask:
    """Convert database row to ImportTask."""
    return ImportTask(
        id=row["id"],
        lastdodo_id=row["lastdodo_id"],
        colnect_id=row["colnect_id"],
        status=row["status"],
        match_method=row["match_method"],
        condition_final=row["condition_final"],
        quantity_final=row["quantity_final"],
        comment=row["comment"],
        error_message=row["error_message"],
        reviewed_at=datetime.fromisoformat(row["reviewed_at"])
        if row["reviewed_at"]
        else None,
        imported_at=datetime.fromisoformat(row["imported_at"])
        if row["imported_at"]
        else None,
        dry_run=bool(row["dry_run"]),
    )


# =============================================================================
# Utility Functions
# =============================================================================


def get_database_stats() -> dict:
    """Get database statistics.

    Returns:
        Dict with counts for each table
    """
    return {
        "catalog_stamps": count_catalog_stamps(),
        "lastdodo_items": count_lastdodo_items(),
        "import_tasks": count_import_tasks(),
        "import_task_breakdown": get_import_task_stats(),
    }


def find_catalog_stamp_by_catalog_code(
    catalog_type: str,
    catalog_number: str,
) -> Optional[CatalogStamp]:
    """Find a catalog stamp by catalog code.

    Args:
        catalog_type: Type of catalog (michel, yvert, scott, sg, fisher)
        catalog_number: Catalog number to search for

    Returns:
        CatalogStamp if found, None otherwise
    """
    # Search in JSON catalog_codes field
    sql = """
    SELECT * FROM catalog_stamps
    WHERE json_extract(catalog_codes, ?) = ?
    LIMIT 1
    """

    json_path = f"$.{catalog_type}"

    with get_connection() as conn:
        row = conn.execute(sql, (json_path, catalog_number)).fetchone()

    if row:
        return _row_to_catalog_stamp(row)

    return None
