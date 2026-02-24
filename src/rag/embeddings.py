"""OpenAI embedding generation for stamp descriptions.

Generates vector embeddings using OpenAI's text-embedding models
(default: text-embedding-3-small) for semantic search.
"""

import asyncio
import logging
from typing import Callable, Optional

from openai import OpenAI

from src.core.config import get_settings
from src.core.errors import EmbeddingError

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates embeddings via OpenAI API."""

    # OpenAI batch limits
    MAX_BATCH_SIZE = 2048
    MAX_TOKENS_PER_BATCH = 8191  # For text-embedding-3-small

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
    ):
        """Initialize the embedding generator.

        Args:
            api_key: OpenAI API key (defaults to settings)
            model: Embedding model name (defaults to settings)
            dimensions: Embedding dimensions (defaults to settings, typically 1536)
        """
        settings = get_settings()

        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise EmbeddingError("OPENAI_API_KEY not configured")

        self.model = model or settings.EMBEDDING_MODEL
        self.dimensions = dimensions or settings.EMBEDDING_DIMENSIONS
        self.client = OpenAI(api_key=self.api_key)

        logger.debug(f"Initialized EmbeddingGenerator with model={self.model}, dim={self.dimensions}")

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector

        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not text or not text.strip():
            raise EmbeddingError("Cannot embed empty text")

        logger.debug(f" * embed > Generating embedding for text of length {len(text)}")

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text.strip(),
                dimensions=self.dimensions,
            )

            embedding = response.data[0].embedding
            logger.debug(f"    -> Generated embedding of dimension {len(embedding)}")
            return embedding

        except Exception as e:
            error_msg = f"Failed to generate embedding: {e}"
            logger.error(error_msg)
            raise EmbeddingError(error_msg) from e

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors in same order as input

        Raises:
            EmbeddingError: If embedding generation fails

        Note:
            Automatically handles batching for large inputs.
            Empty texts are skipped with None placeholders.
        """
        if not texts:
            return []

        logger.debug(f" * embed_batch > Generating embeddings for {len(texts)} texts")

        # Filter out empty texts but track indices
        valid_items = [(i, text.strip()) for i, text in enumerate(texts) if text and text.strip()]

        if not valid_items:
            return [[] for _ in texts]

        # Process in batches
        all_embeddings: dict[int, list[float]] = {}
        batch_start = 0

        while batch_start < len(valid_items):
            batch_end = min(batch_start + self.MAX_BATCH_SIZE, len(valid_items))
            batch = valid_items[batch_start:batch_end]
            batch_texts = [text for _, text in batch]

            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch_texts,
                    dimensions=self.dimensions,
                )

                for j, embedding_data in enumerate(response.data):
                    original_idx = batch[j][0]
                    all_embeddings[original_idx] = embedding_data.embedding

            except Exception as e:
                error_msg = f"Failed to generate batch embeddings: {e}"
                logger.error(error_msg)
                raise EmbeddingError(error_msg) from e

            batch_start = batch_end

        # Build result list maintaining original order
        result = []
        for i in range(len(texts)):
            if i in all_embeddings:
                result.append(all_embeddings[i])
            else:
                result.append([])  # Empty embedding for empty/invalid text

        logger.debug(f"    -> Generated {len(all_embeddings)} embeddings")
        return result

    async def embed_async(self, text: str) -> list[float]:
        """Async wrapper for embed().

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        return await asyncio.to_thread(self.embed, text)

    async def embed_batch_async(self, texts: list[str]) -> list[list[float]]:
        """Async wrapper for embed_batch().

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        return await asyncio.to_thread(self.embed_batch, texts)

    async def embed_with_progress(
        self,
        items: list[tuple[str, str]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> dict[str, list[float]]:
        """Generate embeddings with progress tracking.

        Args:
            items: List of (id, text) tuples
            progress_callback: Optional callback(current, total, id)

        Returns:
            Dict mapping id to embedding vector
        """
        logger.info(f"Starting embedding generation for {len(items)} items")

        # Extract texts and embed in batch
        ids = [item_id for item_id, _ in items]
        texts = [text for _, text in items]

        # Update progress before batch processing
        if progress_callback:
            progress_callback(0, len(items), "Starting batch embedding...")

        embeddings = await self.embed_batch_async(texts)

        # Build result dict
        results = {}
        for idx, (item_id, embedding) in enumerate(zip(ids, embeddings)):
            if embedding:  # Skip empty embeddings
                results[item_id] = embedding
                if progress_callback:
                    progress_callback(idx + 1, len(items), item_id)

        logger.info(f"Embedding complete: {len(results)}/{len(items)} successful")
        return results


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors.

    Args:
        vec1: First embedding vector
        vec2: Second embedding vector

    Returns:
        Cosine similarity score between -1 and 1
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)
