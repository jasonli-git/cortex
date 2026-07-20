"""Embedding providers and vector storage."""

from pks.config import Settings
from pks.embeddings.base import EmbeddingProvider
from pks.embeddings.index import EmbeddingIndex
from pks.embeddings.local import SentenceTransformerProvider


def make_embedder(settings: Settings) -> EmbeddingProvider:
    return SentenceTransformerProvider(settings.embedding_model)


__all__ = ["EmbeddingIndex", "EmbeddingProvider", "SentenceTransformerProvider", "make_embedder"]
