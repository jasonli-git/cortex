"""Local embedding provider via sentence-transformers.

Free, offline, and private — the right default for a personal knowledge
system. The model loads lazily on first use (it can take seconds, and the
first ever use downloads the weights), and encode calls are serialized with a
lock because the API thread and the worker thread share one instance.
"""

from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)


class SentenceTransformerProvider:
    def __init__(self, model_name: str):
        self._model_name = model_name
        self._model = None
        self._lock = threading.Lock()

    @property
    def model_name(self) -> str:
        return self._model_name

    def _ensure_model(self):
        if self._model is None:
            # Imported here: pulling in torch takes noticeable time and isn't
            # needed unless embeddings are actually used.
            from sentence_transformers import SentenceTransformer

            logger.info("loading embedding model %s", self._model_name)
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        with self._lock:
            model = self._ensure_model()
            vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [vector.tolist() for vector in vectors]

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]
