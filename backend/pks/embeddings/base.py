"""Embedding provider abstraction.

Like completion providers, embedding backends are infrastructure and must be
swappable (local sentence-transformers today; Voyage/OpenAI later) without
touching anything above this protocol.
"""

from typing import Protocol


class EmbeddingProvider(Protocol):
    @property
    def model_name(self) -> str:
        """Identifier stored with each vector; vectors from other models are ignored."""
        ...

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed documents for indexing."""
        ...

    def embed_query(self, query: str) -> list[float]:
        """Embed a search query (some models use distinct query prompts)."""
        ...
