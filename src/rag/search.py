"""Similarity search for stamp identification.

Provides high-level search functionality combining embeddings
and Supabase vector search for identifying stamps.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.core.config import get_settings
from src.core.errors import SearchError
from src.rag.embeddings import EmbeddingGenerator
from src.rag.supabase_client import RAGEntry, SupabaseRAG

logger = logging.getLogger(__name__)


class MatchConfidence(Enum):
    """Confidence level for a match."""

    AUTO_ACCEPT = "auto_accept"  # > 90% - High confidence
    REVIEW = "review"  # 50-90% - Needs user review
    NO_MATCH = "no_match"  # < 50% - No good match


@dataclass
class SearchResult:
    """Result from a similarity search."""

    entry: RAGEntry
    similarity: float
    rank: int

    @property
    def percentage(self) -> float:
        """Similarity as percentage (0-100)."""
        return self.similarity * 100

    @property
    def confidence(self) -> MatchConfidence:
        """Determine confidence level based on similarity."""
        settings = get_settings()

        if self.similarity >= settings.RAG_MATCH_AUTO_THRESHOLD:
            return MatchConfidence.AUTO_ACCEPT
        elif self.similarity >= settings.RAG_MATCH_MIN_THRESHOLD:
            return MatchConfidence.REVIEW
        else:
            return MatchConfidence.NO_MATCH


@dataclass
class IdentificationResult:
    """Result from stamp identification."""

    query_description: str
    top_matches: list[SearchResult]
    confidence: MatchConfidence
    auto_match: Optional[SearchResult] = None

    @property
    def has_match(self) -> bool:
        """Check if any match was found above minimum threshold."""
        return len(self.top_matches) > 0

    @property
    def best_match(self) -> Optional[SearchResult]:
        """Get the best match if available."""
        if self.auto_match:
            return self.auto_match
        return self.top_matches[0] if self.top_matches else None


class RAGSearcher:
    """Performs similarity search for stamp identification."""

    def __init__(
        self,
        embedder: Optional[EmbeddingGenerator] = None,
        supabase: Optional[SupabaseRAG] = None,
    ):
        """Initialize the searcher.

        Args:
            embedder: EmbeddingGenerator instance (creates new if not provided)
            supabase: SupabaseRAG instance (creates new if not provided)
        """
        self.embedder = embedder
        self.supabase = supabase
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Lazy initialize components."""
        if self._initialized:
            return

        if self.embedder is None:
            self.embedder = EmbeddingGenerator()
        if self.supabase is None:
            self.supabase = SupabaseRAG()

        self._initialized = True

    def search(
        self,
        query: str,
        top_k: int = 5,
        country: Optional[str] = None,
        year: Optional[int] = None,
        min_threshold: Optional[float] = None,
    ) -> list[SearchResult]:
        """Search for stamps matching a text query.

        Args:
            query: Text description to search for
            top_k: Number of results to return
            country: Optional country filter
            year: Optional year filter
            min_threshold: Minimum similarity threshold (defaults to settings)

        Returns:
            List of SearchResult sorted by similarity

        Raises:
            SearchError: If search fails
        """
        self._ensure_initialized()

        settings = get_settings()
        threshold = min_threshold if min_threshold is not None else settings.RAG_MATCH_MIN_THRESHOLD

        logger.debug(f" * search > Query: {query[:50]}... | top_k={top_k}")

        try:
            # Generate embedding for query
            embedding = self.embedder.embed(query)

            # Search in Supabase
            results = self.supabase.search(
                embedding=embedding,
                limit=top_k,
                country=country,
                year=year,
                min_similarity=threshold,
            )

            # Convert to SearchResult objects
            search_results = [
                SearchResult(entry=entry, similarity=score, rank=idx + 1)
                for idx, (entry, score) in enumerate(results)
            ]

            logger.debug(f"    -> Found {len(search_results)} matches")
            return search_results

        except Exception as e:
            error_msg = f"Search failed: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    async def search_async(
        self,
        query: str,
        top_k: int = 5,
        country: Optional[str] = None,
        year: Optional[int] = None,
        min_threshold: Optional[float] = None,
    ) -> list[SearchResult]:
        """Async wrapper for search().

        Args:
            query: Text description to search for
            top_k: Number of results to return
            country: Optional country filter
            year: Optional year filter
            min_threshold: Minimum similarity threshold

        Returns:
            List of SearchResult sorted by similarity
        """
        import asyncio
        return await asyncio.to_thread(
            self.search, query, top_k, country, year, min_threshold
        )

    def identify(
        self,
        description: str,
        top_k: int = 3,
        country: Optional[str] = None,
        year: Optional[int] = None,
    ) -> IdentificationResult:
        """Identify a stamp based on description.

        Applies threshold logic to determine confidence:
        - > 90%: Auto-accept (high confidence)
        - 50-90%: Review needed (show top matches)
        - < 50%: No match found

        Args:
            description: Text description of the stamp
            top_k: Number of candidates to return for review
            country: Optional country filter
            year: Optional year filter

        Returns:
            IdentificationResult with matches and confidence level
        """
        self._ensure_initialized()

        settings = get_settings()

        logger.info(f"Identifying stamp: {description[:100]}...")

        # Search for matches (get more than needed to filter)
        all_matches = self.search(
            query=description,
            top_k=top_k * 2,
            country=country,
            year=year,
            min_threshold=settings.RAG_MATCH_MIN_THRESHOLD,
        )

        if not all_matches:
            logger.info("No matches found above threshold")
            return IdentificationResult(
                query_description=description,
                top_matches=[],
                confidence=MatchConfidence.NO_MATCH,
            )

        # Check for auto-accept
        best = all_matches[0]
        if best.similarity >= settings.RAG_MATCH_AUTO_THRESHOLD:
            logger.info(f"Auto-accept match: {best.entry.colnect_id} ({best.percentage:.1f}%)")
            return IdentificationResult(
                query_description=description,
                top_matches=all_matches[:top_k],
                confidence=MatchConfidence.AUTO_ACCEPT,
                auto_match=best,
            )

        # Return top candidates for review
        logger.info(f"Review needed: best match {best.percentage:.1f}%")
        return IdentificationResult(
            query_description=description,
            top_matches=all_matches[:top_k],
            confidence=MatchConfidence.REVIEW,
        )

    async def identify_async(
        self,
        description: str,
        top_k: int = 3,
        country: Optional[str] = None,
        year: Optional[int] = None,
    ) -> IdentificationResult:
        """Async wrapper for identify().

        Args:
            description: Text description of the stamp
            top_k: Number of candidates to return
            country: Optional country filter
            year: Optional year filter

        Returns:
            IdentificationResult with matches and confidence level
        """
        import asyncio
        return await asyncio.to_thread(self.identify, description, top_k, country, year)

    def find_similar(
        self,
        colnect_id: str,
        top_k: int = 5,
        exclude_self: bool = True,
    ) -> list[SearchResult]:
        """Find stamps similar to an existing stamp.

        Args:
            colnect_id: ID of reference stamp
            top_k: Number of similar stamps to return
            exclude_self: Whether to exclude the reference stamp

        Returns:
            List of similar stamps

        Raises:
            SearchError: If stamp not found or search fails
        """
        self._ensure_initialized()

        logger.debug(f" * find_similar > Finding stamps similar to {colnect_id}")

        # Get the reference stamp
        entry = self.supabase.get_by_colnect_id(colnect_id)
        if not entry:
            raise SearchError(f"Stamp not found: {colnect_id}")

        if not entry.embedding:
            raise SearchError(f"Stamp has no embedding: {colnect_id}")

        # Search using its embedding
        results = self.supabase.search(
            embedding=entry.embedding,
            limit=top_k + (1 if exclude_self else 0),
        )

        # Convert and filter
        search_results = []
        for idx, (result_entry, score) in enumerate(results):
            if exclude_self and result_entry.colnect_id == colnect_id:
                continue
            search_results.append(
                SearchResult(entry=result_entry, similarity=score, rank=len(search_results) + 1)
            )
            if len(search_results) >= top_k:
                break

        logger.debug(f"    -> Found {len(search_results)} similar stamps")
        return search_results


def format_search_result(result: SearchResult) -> str:
    """Format a search result for display.

    Args:
        result: SearchResult to format

    Returns:
        Formatted string
    """
    confidence_emoji = {
        MatchConfidence.AUTO_ACCEPT: "[green][[/green]",
        MatchConfidence.REVIEW: "[yellow]?[/yellow]",
        MatchConfidence.NO_MATCH: "[red]X[/red]",
    }

    emoji = confidence_emoji.get(result.confidence, "?")
    return (
        f"{emoji} [{result.rank}] {result.entry.country} {result.entry.year} - "
        f"{result.percentage:.1f}% match\n"
        f"    ID: {result.entry.colnect_id}\n"
        f"    {result.entry.description[:100]}..."
    )


def format_identification_result(result: IdentificationResult) -> str:
    """Format an identification result for display.

    Args:
        result: IdentificationResult to format

    Returns:
        Formatted string
    """
    lines = []

    if result.confidence == MatchConfidence.AUTO_ACCEPT:
        lines.append("[bold green]Auto-Match Found![/bold green]")
        if result.auto_match:
            lines.append(format_search_result(result.auto_match))
    elif result.confidence == MatchConfidence.REVIEW:
        lines.append("[bold yellow]Review Needed[/bold yellow]")
        lines.append(f"Top {len(result.top_matches)} candidates:")
        for match in result.top_matches:
            lines.append(format_search_result(match))
    else:
        lines.append("[bold red]No Match Found[/bold red]")
        lines.append("No stamps found above the minimum similarity threshold.")

    return "\n".join(lines)
