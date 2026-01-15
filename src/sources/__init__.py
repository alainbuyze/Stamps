"""Source adapters for different tutorial websites."""

from src.sources.base import BaseSourceAdapter, ExtractedContent
from src.sources.elecfreaks import ElecfreaksAdapter

__all__ = [
    "BaseSourceAdapter",
    "ExtractedContent",
    "ElecfreaksAdapter",
]
