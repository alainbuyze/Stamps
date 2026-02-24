"""RAG (Retrieval-Augmented Generation) module for stamp identification.

Components:
- embeddings: OpenAI embedding generation
- supabase_client: Supabase vector database operations
- indexer: Pipeline for indexing stamps into RAG
- search: Similarity search for stamp identification
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
