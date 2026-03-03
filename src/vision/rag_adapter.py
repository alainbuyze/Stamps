"""Adapter to connect RAGSearcher to the IdentificationPipeline.

This adapter provides the interface expected by IdentificationPipeline
while using the existing RAGSearcher implementation.
"""

import logging
from typing import Optional

from src.rag.search import RAGSearcher

logger = logging.getLogger(__name__)


class RAGSearchAdapter:
    """
    Adapts RAGSearcher to the interface expected by IdentificationPipeline.

    The pipeline expects search() to return dicts, while RAGSearcher
    returns SearchResult objects. This adapter handles the conversion.
    """

    def __init__(self, searcher: Optional[RAGSearcher] = None):
        """
        Initialize the adapter.

        Args:
            searcher: Existing RAGSearcher instance, or creates new one
        """
        self.searcher = searcher or RAGSearcher()

    def search(
        self,
        query: str,
        limit: int = 5,
        country: Optional[str] = None,
        year: Optional[int] = None,
    ) -> list[dict]:
        """
        Search for stamps matching a text query.

        Args:
            query: Text description to search for
            limit: Maximum number of results to return
            country: Optional country filter
            year: Optional year filter

        Returns:
            List of dicts with stamp data and similarity scores
        """
        logger.debug(f"RAGSearchAdapter.search: {query[:50]}... limit={limit}")

        try:
            # Use the underlying searcher
            results = self.searcher.search(
                query=query,
                top_k=limit,
                country=country,
                year=year,
            )

            # Convert SearchResult objects to dicts
            output = []
            for result in results:
                entry = result.entry
                output.append({
                    "colnect_id": entry.colnect_id,
                    "colnect_url": entry.colnect_url,
                    "similarity": result.similarity,
                    "description": entry.description,
                    "country": entry.country,
                    "year": entry.year,
                    "image_url": entry.image_url,
                })

            logger.debug(f"RAGSearchAdapter: found {len(output)} results")
            return output

        except Exception as e:
            logger.error(f"RAGSearchAdapter search failed: {e}")
            raise


def create_rag_adapter() -> RAGSearchAdapter:
    """Create a RAG adapter from environment configuration."""
    return RAGSearchAdapter()
