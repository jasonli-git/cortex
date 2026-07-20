"""Hybrid search: semantic (vector) + keyword (FTS5), fused by reciprocal rank.

RRF is rank-based, so the incomparable score scales of cosine similarity and
BM25 never need calibrating against each other. Hits whose underlying object
has since been deleted are silently skipped (indexes are cleaned lazily).
"""

from __future__ import annotations

from pks.core.engine import KnowledgeEngine
from pks.core.errors import NotFoundError
from pks.core.store.sqlite import SqliteStore
from pks.embeddings.base import EmbeddingProvider
from pks.embeddings.index import EmbeddingIndex
from pks.search.fts import FtsIndex
from pks.search.models import ChunkHit, KnowledgeHit, SearchResponse

RRF_K = 60
CANDIDATES = 50


def rrf_fuse(rankings: list[list[str]], *, k: int = RRF_K) -> list[tuple[str, float]]:
    """Fuse ranked id lists: score(id) = Σ 1 / (k + rank). Best first."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item_id in enumerate(ranking):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda pair: -pair[1])


class SearchService:
    def __init__(self, store: SqliteStore, embedder: EmbeddingProvider):
        self._store = store
        self._engine = KnowledgeEngine(store)
        self._vectors = EmbeddingIndex(store)
        self._fts = FtsIndex(store)
        self._embedder = embedder

    def search(self, query: str, *, limit: int = 10) -> SearchResponse:
        query = query.strip()
        if not query:
            return SearchResponse(query=query, knowledge=[], chunks=[])

        query_vector = self._embedder.embed_query(query)
        model = self._embedder.model_name

        ko_semantic = [
            owner_id
            for owner_id, _ in self._vectors.similar(
                "knowledge_object", query_vector, model=model, top_n=CANDIDATES
            )
        ]
        chunk_semantic = [
            owner_id
            for owner_id, _ in self._vectors.similar(
                "chunk", query_vector, model=model, top_n=CANDIDATES
            )
        ]
        ko_keyword = self._fts.search_knowledge_objects(query, top_n=CANDIDATES)
        chunk_keyword = self._fts.search_chunks(query, top_n=CANDIDATES)

        knowledge = self._hydrate_knowledge(rrf_fuse([ko_semantic, ko_keyword]), limit)
        chunks = self._hydrate_chunks(rrf_fuse([chunk_semantic, chunk_keyword]), limit)
        return SearchResponse(query=query, knowledge=knowledge, chunks=chunks)

    def _hydrate_knowledge(
        self, ranked: list[tuple[str, float]], limit: int
    ) -> list[KnowledgeHit]:
        hits: list[KnowledgeHit] = []
        for ko_id, score in ranked:
            if len(hits) >= limit:
                break
            try:
                ko = self._engine.get_knowledge_object(ko_id)
            except NotFoundError:
                continue  # stale index entry
            hits.append(KnowledgeHit(score=score, object=ko))
        return hits

    def _hydrate_chunks(self, ranked: list[tuple[str, float]], limit: int) -> list[ChunkHit]:
        titles: dict[str, str] = {}
        hits: list[ChunkHit] = []
        for chunk_id, score in ranked:
            if len(hits) >= limit:
                break
            chunk = self._store.resources.get_chunk(chunk_id)
            if chunk is None:
                continue  # stale index entry
            if chunk.resource_id not in titles:
                try:
                    titles[chunk.resource_id] = self._engine.get_resource(chunk.resource_id).title
                except NotFoundError:
                    continue
            hits.append(
                ChunkHit(
                    score=score,
                    chunk=chunk,
                    resource_id=chunk.resource_id,
                    resource_title=titles[chunk.resource_id],
                )
            )
        return hits
