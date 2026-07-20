"""The index pipeline stage: embed + FTS-index a processed resource.

Chunks of the triggering resource are (re)indexed wholesale. Knowledge
objects are refreshed incrementally across the whole base: any object whose
embedded text is missing or stale gets re-embedded — cheap, because
unchanged objects are skipped via the stored text hash.
"""

from __future__ import annotations

import hashlib
import logging

from pks.core.models import KnowledgeObject
from pks.embeddings.base import EmbeddingProvider
from pks.embeddings.index import EmbeddingIndex
from pks.events.bus import PipelineRegistry, StageContext
from pks.search.fts import FtsIndex

logger = logging.getLogger(__name__)


def ko_embedding_text(ko: KnowledgeObject) -> str:
    parts = [ko.name]
    if ko.aliases:
        parts.append(", ".join(ko.aliases))
    if ko.description:
        parts.append(ko.description)
    return "\n".join(parts)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def register_stages(
    registry: PipelineRegistry, embedder: EmbeddingProvider, *, on: str
) -> None:
    @registry.stage("index", on=on)
    def index(ctx: StageContext, payload: dict) -> None:
        resource = ctx.engine.get_resource(payload["resource_id"])
        chunks = ctx.engine.get_chunks(resource.id)
        vectors = EmbeddingIndex(ctx.store)
        fts = FtsIndex(ctx.store)
        model = embedder.model_name

        # Chunks: replace this resource's entries wholesale.
        vectors.delete_for_resource(resource.id)
        fts.replace_resource_chunks(resource.id, chunks)
        if chunks:
            for chunk, vector in zip(
                chunks, embedder.embed_texts([c.text for c in chunks]), strict=True
            ):
                vectors.upsert(
                    "chunk",
                    chunk.id,
                    vector,
                    model=model,
                    text_hash=_hash(chunk.text),
                    resource_id=resource.id,
                )

        # Knowledge objects: refresh whatever is missing or stale, base-wide.
        stale: list[KnowledgeObject] = []
        for ko in ctx.engine.list_knowledge_objects():
            text_hash = _hash(ko_embedding_text(ko))
            if vectors.get_text_hash("knowledge_object", ko.id, model=model) != text_hash:
                stale.append(ko)
        if stale:
            for ko, vector in zip(
                stale,
                embedder.embed_texts([ko_embedding_text(ko) for ko in stale]),
                strict=True,
            ):
                vectors.upsert(
                    "knowledge_object",
                    ko.id,
                    vector,
                    model=model,
                    text_hash=_hash(ko_embedding_text(ko)),
                )
                fts.replace_knowledge_object(ko)

        logger.info(
            "indexed %d chunks and %d knowledge objects for %r",
            len(chunks),
            len(stale),
            resource.title,
        )
        ctx.engine.set_resource_status(resource.id, "ready")
        ctx.emit("resource.indexed", {"resource_id": resource.id})
