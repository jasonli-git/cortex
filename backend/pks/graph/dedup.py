"""Duplicate detection: embedding candidates, LLM confirmation, engine merge.

Runs after indexing (it reads the freshly stored knowledge-object vectors).
Candidates are same-type objects whose embeddings exceed a similarity
threshold; a heavy-tier model then confirms identity before anything is
merged — similarity alone is never trusted (spec: quality verification is
heavy-model work). Merges go through the engine, so history, provenance, and
relationships are all preserved.
"""

from __future__ import annotations

import hashlib
import logging

from pks.core.errors import NotFoundError
from pks.core.models import KnowledgeObject
from pks.embeddings.base import EmbeddingProvider
from pks.embeddings.index import EmbeddingIndex
from pks.events.bus import PipelineRegistry, StageContext
from pks.providers.base import CompletionProvider
from pks.search.fts import FtsIndex
from pks.search.stages import ko_embedding_text

logger = logging.getLogger(__name__)

DEDUP_SYSTEM = (
    "You are the duplicate-detection stage of a personal knowledge system. "
    "You decide whether two knowledge objects refer to the same real-world "
    "entity or concept. Be conservative: related or similar is not the same."
)

DEDUP_SCHEMA = {
    "type": "object",
    "properties": {
        "same_entity": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": ["same_entity", "reason"],
    "additionalProperties": False,
}


def dedup_prompt(a: KnowledgeObject, b: KnowledgeObject) -> str:
    def render(ko: KnowledgeObject) -> str:
        aliases = f" (also known as: {', '.join(ko.aliases)})" if ko.aliases else ""
        return f"- {ko.type.value}: {ko.name}{aliases}\n  {ko.description or '(no description)'}"

    return f"""Do these two knowledge objects refer to the same entity?

{render(a)}

{render(b)}

Answer same_entity=true only if they are genuinely the same entity or concept
(possibly under different names), not merely related, similar, or one part of
the other."""


def register_stages(
    registry: PipelineRegistry, provider: CompletionProvider, embedder: EmbeddingProvider
) -> None:
    @registry.stage("dedupe", on="resource.indexed")
    def dedupe(ctx: StageContext, payload: dict) -> None:
        resource = ctx.engine.get_resource(payload["resource_id"])
        threshold = getattr(ctx.settings, "dedup_similarity_threshold", 0.86)
        vectors = EmbeddingIndex(ctx.store)
        fts = FtsIndex(ctx.store)
        model = embedder.model_name

        merges = 0
        merged_away: set[str] = set()
        for ko_id in ctx.engine.knowledge_object_ids_for_resource(resource.id):
            if ko_id in merged_away:
                continue
            try:
                ko = ctx.engine.get_knowledge_object(ko_id)
            except NotFoundError:
                continue  # already merged away in an earlier run
            vector = vectors.get_vector("knowledge_object", ko_id, model=model)
            if vector is None:
                continue

            for other_id, score in vectors.similar(
                "knowledge_object", vector, model=model, top_n=6
            ):
                if other_id == ko.id or other_id in merged_away or score < threshold:
                    continue
                try:
                    other = ctx.engine.get_knowledge_object(other_id)
                except NotFoundError:
                    continue
                if other.type != ko.type:
                    continue
                if not _confirm_same(provider, ko, other):
                    continue

                # The older object is the established one; it absorbs the newer.
                target, source = (
                    (ko, other) if ko.created_at <= other.created_at else (other, ko)
                )
                merged = ctx.engine.merge_knowledge_objects(
                    target.id, source.id, changed_by="dedup"
                )
                merged_away.add(source.id)
                merges += 1
                logger.info(
                    "merged %r into %r (similarity %.3f)", source.name, target.name, score
                )

                # Refresh the target's index entries; drop the source's.
                vectors.delete("knowledge_object", source.id)
                fts.delete_knowledge_object(source.id)
                text = ko_embedding_text(merged)
                vectors.upsert(
                    "knowledge_object",
                    merged.id,
                    embedder.embed_texts([text])[0],
                    model=model,
                    text_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                )
                fts.replace_knowledge_object(merged)

                if source.id == ko.id:
                    break  # the object we were examining no longer exists

        if merges:
            logger.info("dedup after %r: %d merge(s)", resource.title, merges)
        ctx.emit("resource.deduped", {"resource_id": resource.id})


def _confirm_same(
    provider: CompletionProvider, a: KnowledgeObject, b: KnowledgeObject
) -> bool:
    verdict = provider.extract_structured(
        prompt=dedup_prompt(a, b),
        schema=DEDUP_SCHEMA,
        system=DEDUP_SYSTEM,
        tier="heavy",
        max_tokens=1024,
    )
    return bool(verdict.get("same_entity"))
