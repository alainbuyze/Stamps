"""RAG indexing pipeline for stamps.

Orchestrates the full indexing workflow:
1. Load stamps from SQLite database
2. Generate descriptions via Groq vision API
3. Generate embeddings via OpenAI API
4. Store in Supabase with pgvector
"""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from src.core.config import get_settings
from src.core.database import CatalogStamp, get_catalog_stamps, count_catalog_stamps
from src.core.errors import RAGError
from src.rag.embeddings import EmbeddingGenerator
from src.rag.supabase_client import RAGEntry, SupabaseRAG
from src.vision.describer import StampDescriber

logger = logging.getLogger(__name__)


@dataclass
class IndexingStats:
    """Statistics from an indexing run."""

    total_stamps: int = 0
    already_indexed: int = 0
    newly_indexed: int = 0
    description_failures: int = 0
    embedding_failures: int = 0
    storage_failures: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        attempted = self.total_stamps - self.already_indexed
        if attempted == 0:
            return 100.0
        return (self.newly_indexed / attempted) * 100


class RAGIndexer:
    """Orchestrates the RAG indexing pipeline."""

    # Batch sizes for efficiency
    DESCRIPTION_BATCH_SIZE = 10  # Groq rate limit: 30/min
    EMBEDDING_BATCH_SIZE = 100  # OpenAI can handle larger batches
    STORAGE_BATCH_SIZE = 50  # Supabase upsert batch

    def __init__(
        self,
        describer: Optional[StampDescriber] = None,
        embedder: Optional[EmbeddingGenerator] = None,
        supabase: Optional[SupabaseRAG] = None,
    ):
        """Initialize the indexer.

        Args:
            describer: StampDescriber instance (creates new if not provided)
            embedder: EmbeddingGenerator instance (creates new if not provided)
            supabase: SupabaseRAG instance (creates new if not provided)
        """
        self.describer = describer
        self.embedder = embedder
        self.supabase = supabase

        # Lazy initialization to avoid errors if API keys not configured
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Lazy initialize components."""
        if self._initialized:
            return

        if self.describer is None:
            self.describer = StampDescriber()
        if self.embedder is None:
            self.embedder = EmbeddingGenerator()
        if self.supabase is None:
            self.supabase = SupabaseRAG()

        self._initialized = True

    async def index_stamp(self, stamp: CatalogStamp) -> Optional[RAGEntry]:
        """Index a single stamp.

        Full pipeline: describe -> embed -> store

        Args:
            stamp: CatalogStamp to index

        Returns:
            RAGEntry if successful, None if failed
        """
        self._ensure_initialized()

        logger.debug(f" * index_stamp > Processing {stamp.colnect_id}")

        try:
            # Generate description
            description = await self.describer.describe_from_url(stamp.image_url)

            # Generate embedding
            embedding = await self.embedder.embed_async(description)

            # Create RAG entry
            entry = RAGEntry(
                colnect_id=stamp.colnect_id,
                colnect_url=stamp.colnect_url,
                image_url=stamp.image_url,
                description=description,
                embedding=embedding,
                country=stamp.country,
                year=stamp.year,
            )

            # Store in Supabase
            stored_entry = self.supabase.upsert(entry)
            logger.debug(f"    -> Indexed {stamp.colnect_id}")
            return stored_entry

        except Exception as e:
            logger.error(f"Failed to index {stamp.colnect_id}: {e}")
            return None

    async def index_all(
        self,
        country: Optional[str] = None,
        year: Optional[int] = None,
        regenerate: bool = False,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> IndexingStats:
        """Index all stamps matching filters.

        Args:
            country: Optional country filter
            year: Optional year filter
            regenerate: If True, re-index even if already indexed
            progress_callback: Optional callback(current, total, message)

        Returns:
            IndexingStats with results
        """
        self._ensure_initialized()

        stats = IndexingStats()

        # Get stamps to index
        stamps = get_catalog_stamps(country=country, year=year)
        stats.total_stamps = len(stamps)

        logger.info(f"Starting indexing of {stats.total_stamps} stamps")

        if not stamps:
            logger.info("No stamps to index")
            return stats

        # Get already indexed IDs (unless regenerating)
        indexed_ids: set[str] = set()
        if not regenerate:
            indexed_ids = self.supabase.get_indexed_ids()
            logger.debug(f"Found {len(indexed_ids)} already indexed stamps")

        # Process stamps
        for idx, stamp in enumerate(stamps, 1):
            # Check if already indexed
            if stamp.colnect_id in indexed_ids and not regenerate:
                stats.already_indexed += 1
                if progress_callback:
                    progress_callback(idx, stats.total_stamps, f"Skipped {stamp.colnect_id} (already indexed)")
                continue

            if progress_callback:
                progress_callback(idx, stats.total_stamps, f"Indexing {stamp.colnect_id}")

            # Index the stamp
            entry = await self.index_stamp(stamp)

            if entry:
                stats.newly_indexed += 1
            else:
                stats.description_failures += 1

        logger.info(
            f"Indexing complete: {stats.newly_indexed} new, "
            f"{stats.already_indexed} skipped, "
            f"{stats.description_failures} failed"
        )

        return stats

    async def index_batch_optimized(
        self,
        country: Optional[str] = None,
        year: Optional[int] = None,
        regenerate: bool = False,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> IndexingStats:
        """Optimized batch indexing with parallel processing.

        This version processes stamps in batches for better efficiency:
        - Descriptions are generated sequentially (rate limited)
        - Embeddings are generated in batches
        - Storage is done in batches

        Args:
            country: Optional country filter
            year: Optional year filter
            regenerate: If True, re-index even if already indexed
            progress_callback: Optional callback(current, total, message)

        Returns:
            IndexingStats with results
        """
        self._ensure_initialized()

        stats = IndexingStats()

        # Get stamps to index
        stamps = get_catalog_stamps(country=country, year=year)
        stats.total_stamps = len(stamps)

        logger.info(f"Starting optimized batch indexing of {stats.total_stamps} stamps")

        if not stamps:
            logger.info("No stamps to index")
            return stats

        # Get already indexed IDs (unless regenerating)
        indexed_ids: set[str] = set()
        if not regenerate:
            indexed_ids = self.supabase.get_indexed_ids()
            stats.already_indexed = len([s for s in stamps if s.colnect_id in indexed_ids])
            stamps = [s for s in stamps if s.colnect_id not in indexed_ids]
            logger.debug(f"Filtered to {len(stamps)} stamps needing indexing")

        if not stamps:
            logger.info("All stamps already indexed")
            return stats

        # Phase 1: Generate descriptions
        if progress_callback:
            progress_callback(0, len(stamps), "Generating descriptions...")

        descriptions: dict[str, str] = {}
        for idx, stamp in enumerate(stamps, 1):
            if progress_callback:
                progress_callback(idx, len(stamps), f"Describing {stamp.colnect_id}")

            try:
                desc = await self.describer.describe_from_url(stamp.image_url)
                descriptions[stamp.colnect_id] = desc
            except Exception as e:
                logger.error(f"Description failed for {stamp.colnect_id}: {e}")
                stats.description_failures += 1

        logger.info(f"Generated {len(descriptions)} descriptions")

        # Phase 2: Generate embeddings in batch
        if progress_callback:
            progress_callback(0, len(descriptions), "Generating embeddings...")

        stamps_with_desc = [(s.colnect_id, descriptions[s.colnect_id])
                           for s in stamps if s.colnect_id in descriptions]

        embeddings = await self.embedder.embed_with_progress(
            stamps_with_desc,
            progress_callback=lambda c, t, m: progress_callback(c, t, f"Embedding {m}") if progress_callback else None
        )

        logger.info(f"Generated {len(embeddings)} embeddings")

        # Phase 3: Store in Supabase
        if progress_callback:
            progress_callback(0, len(embeddings), "Storing in database...")

        entries_to_store: list[RAGEntry] = []
        stamp_map = {s.colnect_id: s for s in stamps}

        for colnect_id, embedding in embeddings.items():
            stamp = stamp_map.get(colnect_id)
            if stamp and colnect_id in descriptions:
                entry = RAGEntry(
                    colnect_id=colnect_id,
                    colnect_url=stamp.colnect_url,
                    image_url=stamp.image_url,
                    description=descriptions[colnect_id],
                    embedding=embedding,
                    country=stamp.country,
                    year=stamp.year,
                )
                entries_to_store.append(entry)

        # Batch upsert
        try:
            stored_count = self.supabase.upsert_batch(entries_to_store)
            stats.newly_indexed = stored_count
        except Exception as e:
            logger.error(f"Batch storage failed: {e}")
            stats.storage_failures = len(entries_to_store)

        logger.info(
            f"Batch indexing complete: {stats.newly_indexed} new, "
            f"{stats.already_indexed} skipped, "
            f"{stats.description_failures} description failures"
        )

        return stats

    def verify_setup(self) -> dict[str, bool]:
        """Verify all components are properly configured.

        Returns:
            Dict mapping component name to ready status
        """
        status = {
            "describer": False,
            "embedder": False,
            "supabase": False,
        }

        try:
            self.describer = StampDescriber()
            status["describer"] = True
        except Exception as e:
            logger.error(f"Describer not ready: {e}")

        try:
            self.embedder = EmbeddingGenerator()
            status["embedder"] = True
        except Exception as e:
            logger.error(f"Embedder not ready: {e}")

        try:
            self.supabase = SupabaseRAG()
            self.supabase.get_stats()  # Test connection
            status["supabase"] = True
        except Exception as e:
            logger.error(f"Supabase not ready: {e}")

        return status


async def quick_index(
    colnect_id: str,
    image_url: str,
    colnect_url: str,
    country: str,
    year: int,
) -> Optional[RAGEntry]:
    """Quick helper to index a single stamp without loading from database.

    Args:
        colnect_id: Stamp ID
        image_url: URL to stamp image
        colnect_url: URL to Colnect page
        country: Country name
        year: Year of issue

    Returns:
        RAGEntry if successful
    """
    indexer = RAGIndexer()

    stamp = CatalogStamp(
        colnect_id=colnect_id,
        colnect_url=colnect_url,
        image_url=image_url,
        title="",
        country=country,
        year=year,
    )

    return await indexer.index_stamp(stamp)
