"""RAG (Retrieval-Augmented Generation) module for stamp identification.

This module provides vector similarity search for matching photographed stamps
to catalog entries. Uses OpenAI embeddings stored in Supabase with pgvector.

Modules
-------
embeddings.py
    EmbeddingGenerator: Generates 1536-dimensional embeddings using OpenAI's
    text-embedding-3-small model. Handles batch processing and rate limiting.

supabase_client.py
    SupabaseRAG: Client for Supabase vector database operations. Handles
    connection management, upserts, and raw SQL for pgvector queries.
    RAGEntry: Dataclass representing a stamp entry in the vector database
    (colnect_id, description, embedding, country, year, image_url).

indexer.py
    RAGIndexer: Pipeline for indexing stamps from SQLite into Supabase RAG.
    Generates descriptions via Groq vision API, creates embeddings, and
    upserts to the vector database. Supports incremental and full re-indexing.

search.py
    RAGSearcher: Performs similarity search against the vector database.
    Returns ranked matches with similarity scores for stamp identification.
    SearchResult: Container for search matches with score and metadata.

Key Exports
-----------
- EmbeddingGenerator: Text-to-embedding conversion
- SupabaseRAG, RAGEntry: Database client and data model
- RAGIndexer: Stamp indexing pipeline
- RAGSearcher, SearchResult: Similarity search
"""

# Lazy imports to avoid circular dependencies
# Import components directly from submodules when needed:
#   from src.rag.embeddings import EmbeddingGenerator
#   from src.rag.supabase_client import SupabaseRAG, RAGEntry
#   from src.rag.indexer import RAGIndexer
#   from src.rag.search import RAGSearcher, SearchResult

__all__ = [
    "EmbeddingGenerator",
    "SupabaseRAG",
    "RAGEntry",
    "RAGIndexer",
    "RAGSearcher",
    "SearchResult",
]


def __getattr__(name: str):
    """Lazy load module components."""
    if name == "EmbeddingGenerator":
        from src.rag.embeddings import EmbeddingGenerator
        return EmbeddingGenerator
    elif name == "SupabaseRAG":
        from src.rag.supabase_client import SupabaseRAG
        return SupabaseRAG
    elif name == "RAGEntry":
        from src.rag.supabase_client import RAGEntry
        return RAGEntry
    elif name == "RAGIndexer":
        from src.rag.indexer import RAGIndexer
        return RAGIndexer
    elif name == "RAGSearcher":
        from src.rag.search import RAGSearcher
        return RAGSearcher
    elif name == "SearchResult":
        from src.rag.search import SearchResult
        return SearchResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
