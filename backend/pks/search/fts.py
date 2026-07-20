"""Keyword (FTS5) index over chunks and knowledge objects.

Maintained explicitly by the index pipeline stage (not triggers), so keyword
indexing is a retryable stage like everything else in the pipeline.
"""

from __future__ import annotations

import re
import sqlite3

from pks.core.models import KnowledgeObject, ResourceChunk
from pks.core.store.sqlite import SqliteStore

_WORD = re.compile(r"\w+", re.UNICODE)


def fts_query(query: str) -> str | None:
    """Turn free text into a safe FTS5 MATCH expression (OR of quoted terms)."""
    terms = _WORD.findall(query)
    if not terms:
        return None
    return " OR ".join(f'"{term}"' for term in terms)


class FtsIndex:
    def __init__(self, store: SqliteStore):
        self._conn: sqlite3.Connection = store.connection

    # -- maintenance -----------------------------------------------------

    def replace_resource_chunks(self, resource_id: str, chunks: list[ResourceChunk]) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM chunks_fts WHERE resource_id = ?", (resource_id,))
            self._conn.executemany(
                "INSERT INTO chunks_fts (text, chunk_id, resource_id) VALUES (?, ?, ?)",
                [(chunk.text, chunk.id, resource_id) for chunk in chunks],
            )

    def replace_knowledge_object(self, ko: KnowledgeObject) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM ko_fts WHERE ko_id = ?", (ko.id,))
            self._conn.execute(
                "INSERT INTO ko_fts (name, aliases, description, ko_id) VALUES (?, ?, ?, ?)",
                (ko.name, " ".join(ko.aliases), ko.description, ko.id),
            )

    def delete_knowledge_object(self, ko_id: str) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM ko_fts WHERE ko_id = ?", (ko_id,))

    # -- queries ---------------------------------------------------------

    def search_chunks(self, query: str, *, top_n: int = 50) -> list[str]:
        """Chunk ids ranked by BM25 (best first)."""
        match = fts_query(query)
        if match is None:
            return []
        rows = self._conn.execute(
            "SELECT chunk_id FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY rank LIMIT ?",
            (match, top_n),
        )
        return [row["chunk_id"] for row in rows]

    def search_knowledge_objects(self, query: str, *, top_n: int = 50) -> list[str]:
        match = fts_query(query)
        if match is None:
            return []
        rows = self._conn.execute(
            "SELECT ko_id FROM ko_fts WHERE ko_fts MATCH ? ORDER BY rank LIMIT ?",
            (match, top_n),
        )
        return [row["ko_id"] for row in rows]
