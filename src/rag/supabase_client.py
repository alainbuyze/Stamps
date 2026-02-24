"""Supabase vector database operations for RAG.

Manages the stamps_rag table with pgvector for similarity search.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from supabase import create_client, Client

from src.core.config import get_settings
from src.core.errors import SupabaseError

logger = logging.getLogger(__name__)


@dataclass
class RAGEntry:
    """RAG database entry for a stamp."""

    colnect_id: str
    colnect_url: str
    image_url: str
    description: str
    embedding: list[float]
    country: str
    year: int
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SupabaseRAG:
    """Manages RAG entries in Supabase with pgvector."""

    TABLE_NAME = "stamps_rag"

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
    ):
        """Initialize Supabase client.

        Args:
            url: Supabase project URL (defaults to settings)
            key: Supabase service role key (defaults to settings)
        """
        settings = get_settings()

        self.url = url or settings.SUPABASE_URL
        self.key = key or settings.SUPABASE_KEY

        if not self.url or not self.key:
            raise SupabaseError("SUPABASE_URL and SUPABASE_KEY must be configured")

        try:
            self.client: Client = create_client(self.url, self.key)
            logger.debug(f"Initialized Supabase client for {self.url}")
        except Exception as e:
            raise SupabaseError(f"Failed to create Supabase client: {e}") from e

    def init_table(self) -> None:
        """Create stamps_rag table with vector column if not exists.

        Note:
            This requires the pgvector extension to be enabled in Supabase.
            The extension can be enabled via the Supabase dashboard.

        The table schema:
            - id: BIGSERIAL PRIMARY KEY
            - colnect_id: TEXT UNIQUE NOT NULL
            - colnect_url: TEXT NOT NULL
            - image_url: TEXT NOT NULL
            - description: TEXT NOT NULL
            - embedding: VECTOR(1536) NOT NULL
            - country: TEXT NOT NULL
            - year: INTEGER NOT NULL
            - created_at: TIMESTAMPTZ DEFAULT NOW()
            - updated_at: TIMESTAMPTZ DEFAULT NOW()
        """
        logger.info("Initializing stamps_rag table...")

        # SQL to create the table (requires pgvector extension)
        create_table_sql = """
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
        """

        try:
            # Note: Direct SQL execution requires the SQL Editor or database functions
            # For Supabase, we typically create tables via migrations or the dashboard
            # This is a placeholder - the table should be created via Supabase dashboard
            logger.info("Table creation SQL prepared. Please run in Supabase SQL Editor if table doesn't exist.")
            logger.debug(create_table_sql)

            # Verify table exists by attempting a simple query
            self.client.table(self.TABLE_NAME).select("id").limit(1).execute()
            logger.info("stamps_rag table verified")

        except Exception as e:
            if "does not exist" in str(e).lower():
                raise SupabaseError(
                    f"Table {self.TABLE_NAME} does not exist. "
                    "Please create it via Supabase SQL Editor with pgvector enabled."
                ) from e
            raise SupabaseError(f"Failed to verify table: {e}") from e

    def upsert(self, entry: RAGEntry) -> RAGEntry:
        """Insert or update a RAG entry.

        Args:
            entry: RAGEntry to upsert

        Returns:
            Updated RAGEntry with id and timestamps

        Raises:
            SupabaseError: If operation fails
        """
        logger.debug(f" * upsert > Upserting entry for {entry.colnect_id}")

        data = {
            "colnect_id": entry.colnect_id,
            "colnect_url": entry.colnect_url,
            "image_url": entry.image_url,
            "description": entry.description,
            "embedding": entry.embedding,
            "country": entry.country,
            "year": entry.year,
            "updated_at": datetime.utcnow().isoformat(),
        }

        try:
            result = (
                self.client.table(self.TABLE_NAME)
                .upsert(data, on_conflict="colnect_id")
                .execute()
            )

            if result.data:
                row = result.data[0]
                entry.id = row.get("id")
                entry.created_at = row.get("created_at")
                entry.updated_at = row.get("updated_at")
                logger.debug(f"    -> Upserted entry id={entry.id}")

            return entry

        except Exception as e:
            error_msg = f"Failed to upsert entry {entry.colnect_id}: {e}"
            logger.error(error_msg)
            raise SupabaseError(error_msg) from e

    def upsert_batch(self, entries: list[RAGEntry]) -> int:
        """Upsert multiple RAG entries.

        Args:
            entries: List of RAGEntry objects to upsert

        Returns:
            Number of successfully upserted entries

        Raises:
            SupabaseError: If operation fails
        """
        if not entries:
            return 0

        logger.debug(f" * upsert_batch > Upserting {len(entries)} entries")

        data = [
            {
                "colnect_id": entry.colnect_id,
                "colnect_url": entry.colnect_url,
                "image_url": entry.image_url,
                "description": entry.description,
                "embedding": entry.embedding,
                "country": entry.country,
                "year": entry.year,
                "updated_at": datetime.utcnow().isoformat(),
            }
            for entry in entries
        ]

        try:
            result = (
                self.client.table(self.TABLE_NAME)
                .upsert(data, on_conflict="colnect_id")
                .execute()
            )

            count = len(result.data) if result.data else 0
            logger.debug(f"    -> Upserted {count} entries")
            return count

        except Exception as e:
            error_msg = f"Failed to upsert batch: {e}"
            logger.error(error_msg)
            raise SupabaseError(error_msg) from e

    def get_by_colnect_id(self, colnect_id: str) -> Optional[RAGEntry]:
        """Get RAG entry by Colnect ID.

        Args:
            colnect_id: Colnect stamp ID

        Returns:
            RAGEntry if found, None otherwise
        """
        try:
            result = (
                self.client.table(self.TABLE_NAME)
                .select("*")
                .eq("colnect_id", colnect_id)
                .execute()
            )

            if result.data:
                return self._row_to_entry(result.data[0])
            return None

        except Exception as e:
            logger.error(f"Failed to get entry {colnect_id}: {e}")
            return None

    def exists(self, colnect_id: str) -> bool:
        """Check if RAG entry exists for Colnect ID.

        Args:
            colnect_id: Colnect stamp ID

        Returns:
            True if entry exists
        """
        try:
            result = (
                self.client.table(self.TABLE_NAME)
                .select("id")
                .eq("colnect_id", colnect_id)
                .execute()
            )
            return bool(result.data)
        except Exception:
            return False

    def search(
        self,
        embedding: list[float],
        limit: int = 10,
        country: Optional[str] = None,
        year: Optional[int] = None,
        min_similarity: float = 0.0,
    ) -> list[tuple[RAGEntry, float]]:
        """Vector similarity search.

        Args:
            embedding: Query embedding vector
            limit: Maximum number of results
            country: Optional country filter
            year: Optional year filter
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of (RAGEntry, similarity_score) tuples, sorted by similarity desc

        Raises:
            SupabaseError: If search fails
        """
        logger.debug(f" * search > Searching with limit={limit}, country={country}, year={year}")

        try:
            # Use Supabase RPC for vector similarity search
            # This requires a database function to be created
            rpc_params = {
                "query_embedding": embedding,
                "match_count": limit,
                "filter_country": country,
                "filter_year": year,
            }

            result = self.client.rpc("match_stamps", rpc_params).execute()

            entries = []
            for row in result.data or []:
                similarity = row.get("similarity", 0)
                if similarity >= min_similarity:
                    entry = self._row_to_entry(row)
                    entries.append((entry, similarity))

            logger.debug(f"    -> Found {len(entries)} matches")
            return entries

        except Exception as e:
            # If RPC doesn't exist, fall back to basic query
            if "function" in str(e).lower() and "does not exist" in str(e).lower():
                logger.warning("match_stamps RPC not found, using fallback search")
                return self._fallback_search(embedding, limit, country, year, min_similarity)

            error_msg = f"Search failed: {e}"
            logger.error(error_msg)
            raise SupabaseError(error_msg) from e

    def _fallback_search(
        self,
        embedding: list[float],
        limit: int,
        country: Optional[str],
        year: Optional[int],
        min_similarity: float,
    ) -> list[tuple[RAGEntry, float]]:
        """Fallback search when RPC is not available.

        This performs the similarity calculation client-side, which is slower
        but works without requiring database functions.
        """
        from src.rag.embeddings import cosine_similarity

        logger.debug("Using fallback client-side similarity search")

        # Build query with filters
        query = self.client.table(self.TABLE_NAME).select("*")

        if country:
            query = query.eq("country", country)
        if year:
            query = query.eq("year", year)

        # Get all matching entries (limited to reasonable size)
        query = query.limit(1000)

        try:
            result = query.execute()
        except Exception as e:
            raise SupabaseError(f"Fallback search failed: {e}") from e

        # Calculate similarities client-side
        entries_with_scores = []
        for row in result.data or []:
            entry = self._row_to_entry(row)
            if entry.embedding:
                similarity = cosine_similarity(embedding, entry.embedding)
                if similarity >= min_similarity:
                    entries_with_scores.append((entry, similarity))

        # Sort by similarity and limit
        entries_with_scores.sort(key=lambda x: x[1], reverse=True)
        return entries_with_scores[:limit]

    def get_stats(self) -> dict:
        """Get RAG database statistics.

        Returns:
            Dict with count, countries, year range, etc.
        """
        logger.debug(" * get_stats > Fetching RAG statistics")

        try:
            # Total count
            count_result = (
                self.client.table(self.TABLE_NAME)
                .select("id", count="exact")
                .execute()
            )
            total_count = count_result.count or 0

            # Get unique countries
            countries_result = (
                self.client.table(self.TABLE_NAME)
                .select("country")
                .execute()
            )
            countries = list(set(row["country"] for row in countries_result.data or []))
            countries.sort()

            # Get year range
            years_result = (
                self.client.table(self.TABLE_NAME)
                .select("year")
                .execute()
            )
            years = [row["year"] for row in years_result.data or []]
            min_year = min(years) if years else None
            max_year = max(years) if years else None

            stats = {
                "total_entries": total_count,
                "countries": countries,
                "country_count": len(countries),
                "year_range": {
                    "min": min_year,
                    "max": max_year,
                },
            }

            logger.debug(f"    -> Stats: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "total_entries": 0,
                "countries": [],
                "country_count": 0,
                "year_range": {"min": None, "max": None},
                "error": str(e),
            }

    def get_indexed_ids(self) -> set[str]:
        """Get set of all indexed Colnect IDs.

        Returns:
            Set of colnect_id values
        """
        try:
            result = (
                self.client.table(self.TABLE_NAME)
                .select("colnect_id")
                .execute()
            )
            return {row["colnect_id"] for row in result.data or []}
        except Exception as e:
            logger.error(f"Failed to get indexed IDs: {e}")
            return set()

    def delete(self, colnect_id: str) -> bool:
        """Delete RAG entry by Colnect ID.

        Args:
            colnect_id: Colnect stamp ID

        Returns:
            True if deleted, False if not found
        """
        try:
            result = (
                self.client.table(self.TABLE_NAME)
                .delete()
                .eq("colnect_id", colnect_id)
                .execute()
            )
            deleted = bool(result.data)
            if deleted:
                logger.debug(f"Deleted RAG entry: {colnect_id}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete {colnect_id}: {e}")
            return False

    def _row_to_entry(self, row: dict) -> RAGEntry:
        """Convert database row to RAGEntry."""
        return RAGEntry(
            id=row.get("id"),
            colnect_id=row["colnect_id"],
            colnect_url=row["colnect_url"],
            image_url=row["image_url"],
            description=row["description"],
            embedding=row.get("embedding", []),
            country=row["country"],
            year=row["year"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


# SQL for creating the match_stamps RPC function in Supabase
MATCH_STAMPS_SQL = """
-- Create the similarity search function
-- Run this in the Supabase SQL Editor

CREATE OR REPLACE FUNCTION match_stamps(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 10,
    filter_country TEXT DEFAULT NULL,
    filter_year INT DEFAULT NULL
)
RETURNS TABLE (
    id BIGINT,
    colnect_id TEXT,
    colnect_url TEXT,
    image_url TEXT,
    description TEXT,
    embedding VECTOR(1536),
    country TEXT,
    year INT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        stamps_rag.id,
        stamps_rag.colnect_id,
        stamps_rag.colnect_url,
        stamps_rag.image_url,
        stamps_rag.description,
        stamps_rag.embedding,
        stamps_rag.country,
        stamps_rag.year,
        stamps_rag.created_at,
        stamps_rag.updated_at,
        1 - (stamps_rag.embedding <=> query_embedding) AS similarity
    FROM stamps_rag
    WHERE
        (filter_country IS NULL OR stamps_rag.country = filter_country)
        AND (filter_year IS NULL OR stamps_rag.year = filter_year)
    ORDER BY stamps_rag.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
"""
