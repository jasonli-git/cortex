"""Vector storage and similarity lookup over the embeddings table.

Vectors are float32 BLOBs compared with numpy (linear scan). This class is
the seam where sqlite-vec or pgvector would slot in if scale ever demands it.
"""

from __future__ import annotations

import sqlite3

import numpy as np

from pks.core.store.db import utcnow
from pks.core.store.sqlite import SqliteStore

OwnerType = str  # 'chunk' | 'knowledge_object'


def _to_blob(vector: list[float]) -> bytes:
    return np.asarray(vector, dtype=np.float32).tobytes()


class EmbeddingIndex:
    def __init__(self, store: SqliteStore):
        self._conn: sqlite3.Connection = store.connection

    def upsert(
        self,
        owner_type: OwnerType,
        owner_id: str,
        vector: list[float],
        *,
        model: str,
        text_hash: str,
        resource_id: str | None = None,
    ) -> None:
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO embeddings
                    (owner_type, owner_id, resource_id, model, text_hash, dim, vector, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (owner_type, owner_id) DO UPDATE SET
                    resource_id = excluded.resource_id,
                    model = excluded.model,
                    text_hash = excluded.text_hash,
                    dim = excluded.dim,
                    vector = excluded.vector,
                    created_at = excluded.created_at
                """,
                (
                    owner_type,
                    owner_id,
                    resource_id,
                    model,
                    text_hash,
                    len(vector),
                    _to_blob(vector),
                    utcnow(),
                ),
            )

    def get_vector(self, owner_type: OwnerType, owner_id: str, *, model: str) -> list[float] | None:
        row = self._conn.execute(
            "SELECT vector FROM embeddings WHERE owner_type = ? AND owner_id = ? AND model = ?",
            (owner_type, owner_id, model),
        ).fetchone()
        if row is None:
            return None
        return np.frombuffer(row["vector"], dtype=np.float32).tolist()

    def get_text_hash(self, owner_type: OwnerType, owner_id: str, *, model: str) -> str | None:
        """The hash of the text currently embedded for this owner (None if not embedded)."""
        row = self._conn.execute(
            "SELECT text_hash FROM embeddings WHERE owner_type = ? AND owner_id = ? AND model = ?",
            (owner_type, owner_id, model),
        ).fetchone()
        return row["text_hash"] if row else None

    def delete_for_resource(self, resource_id: str) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM embeddings WHERE resource_id = ?", (resource_id,))

    def delete(self, owner_type: OwnerType, owner_id: str) -> None:
        with self._conn:
            self._conn.execute(
                "DELETE FROM embeddings WHERE owner_type = ? AND owner_id = ?",
                (owner_type, owner_id),
            )

    def similar(
        self, owner_type: OwnerType, query_vector: list[float], *, model: str, top_n: int = 50
    ) -> list[tuple[str, float]]:
        """Owner ids ranked by cosine similarity to the query (best first)."""
        rows = self._conn.execute(
            "SELECT owner_id, vector FROM embeddings WHERE owner_type = ? AND model = ?",
            (owner_type, model),
        ).fetchall()
        if not rows:
            return []

        matrix = np.stack(
            [np.frombuffer(row["vector"], dtype=np.float32) for row in rows]
        )
        query = np.asarray(query_vector, dtype=np.float32)

        # Cosine similarity (vectors may or may not be pre-normalized).
        norms = np.linalg.norm(matrix, axis=1) * (np.linalg.norm(query) or 1.0)
        norms[norms == 0] = 1.0
        scores = (matrix @ query) / norms

        order = np.argsort(-scores)[:top_n]
        return [(rows[i]["owner_id"], float(scores[i])) for i in order]
