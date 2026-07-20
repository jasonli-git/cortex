"""Extraction pipeline stages: chunked text → knowledge objects with provenance.

    resource.chunked → [extract_knowledge] → resource.extracted
                     → [summarize] → resource.summarized (the index stage follows)

Entity merging here is deliberately naive (case-insensitive name/alias match
within a type). Embedding-based dedup and merge arrive in Milestone 5; keeping
knowledge objects keyed by canonical name means those upgrades refine rather
than restructure.
"""

from __future__ import annotations

import logging

from pks.core.engine import KnowledgeEngine
from pks.core.models import KnowledgeObject, KnowledgeObjectType, Resource, ResourceChunk
from pks.events.bus import PipelineRegistry, StageContext
from pks.extraction import extractor
from pks.extraction.models import ExtractedEntity, ExtractedRelation
from pks.providers.base import CompletionProvider

logger = logging.getLogger(__name__)

CHANGED_BY = "extraction"


def register_stages(registry: PipelineRegistry, provider: CompletionProvider) -> None:
    @registry.stage("extract_knowledge", on="resource.chunked")
    def extract_knowledge(ctx: StageContext, payload: dict) -> None:
        resource = ctx.engine.get_resource(payload["resource_id"])
        chunks = ctx.engine.get_chunks(resource.id)
        applier = _Applier(ctx.engine, resource, chunks)

        for batch in extractor.batch_chunks(chunks):
            result = extractor.extract_batch(provider, resource.title, batch)
            applier.apply(result.entities, result.relations)

        logger.info(
            "extracted %d entities / %d relations from %r",
            applier.entities_applied,
            applier.relations_applied,
            resource.title,
        )
        ctx.emit("resource.extracted", {"resource_id": resource.id})

    @registry.stage("summarize", on="resource.extracted")
    def summarize(ctx: StageContext, payload: dict) -> None:
        resource = ctx.engine.get_resource(payload["resource_id"])
        chunks = ctx.engine.get_chunks(resource.id)

        result = extractor.summarize(provider, resource.title, chunks)
        _upsert_summary(ctx.engine, resource, result.summary, result.key_points)

        ctx.emit("resource.summarized", {"resource_id": resource.id})


def _upsert_summary(
    engine: KnowledgeEngine, resource: Resource, summary: str, key_points: list[str]
) -> None:
    name = f"Summary of {resource.title}"
    existing = next(
        (
            ko
            for ko in engine.list_knowledge_objects(type=KnowledgeObjectType.SUMMARY)
            if ko.name == name
        ),
        None,
    )
    if existing is None:
        ko = engine.create_knowledge_object(
            type=KnowledgeObjectType.SUMMARY,
            name=name,
            description=summary,
            metadata={"key_points": key_points, "resource_id": resource.id},
            changed_by=CHANGED_BY,
        )
        engine.add_provenance(knowledge_object_id=ko.id, resource_id=resource.id)
    else:
        # Re-ingest refreshes the summary in place (history keeps the old one).
        engine.update_knowledge_object(
            existing.id,
            description=summary,
            metadata={"key_points": key_points, "resource_id": resource.id},
            changed_by=CHANGED_BY,
        )


class _Applier:
    """Applies extraction results to the engine, merging by name within a type."""

    def __init__(self, engine: KnowledgeEngine, resource: Resource, chunks: list[ResourceChunk]):
        self._engine = engine
        self._resource = resource
        self._chunk_by_ordinal = {chunk.ordinal: chunk for chunk in chunks}
        self.entities_applied = 0
        self.relations_applied = 0

    def apply(
        self, entities: list[ExtractedEntity], relations: list[ExtractedRelation]
    ) -> None:
        name_to_id: dict[str, str] = {}
        for entity in entities:
            ko = self._upsert_entity(entity)
            for key in (entity.name, *entity.aliases):
                name_to_id.setdefault(key.strip().lower(), ko.id)
            self._add_provenance(ko.id, entity)
            self.entities_applied += 1

        for relation in relations:
            from_id = self._resolve(relation.from_name, name_to_id)
            to_id = self._resolve(relation.to_name, name_to_id)
            if from_id is None or to_id is None or from_id == to_id:
                logger.debug("skipping unresolvable relation %s", relation)
                continue
            self._engine.relate(
                from_id,
                to_id,
                relation.type,
                confidence=relation.confidence,
                created_by=CHANGED_BY,
            )
            self.relations_applied += 1

    def _upsert_entity(self, entity: ExtractedEntity) -> KnowledgeObject:
        existing = self._find_existing(entity)
        if existing is None:
            return self._engine.create_knowledge_object(
                type=entity.type,
                name=entity.name,
                description=entity.description,
                aliases=entity.aliases,
                changed_by=CHANGED_BY,
            )

        # Enrich rather than duplicate: fill an empty description, merge aliases.
        changes: dict = {}
        if entity.description and not existing.description:
            changes["description"] = entity.description
        known = {a.lower() for a in (existing.name, *existing.aliases)}
        new_aliases = [
            alias
            for alias in (entity.name, *entity.aliases)
            if alias.lower() not in known
        ]
        if new_aliases:
            changes["aliases"] = [*existing.aliases, *new_aliases]
        if changes:
            return self._engine.update_knowledge_object(
                existing.id, changed_by=CHANGED_BY, **changes
            )
        return existing

    def _find_existing(self, entity: ExtractedEntity) -> KnowledgeObject | None:
        wanted = {n.strip().lower() for n in (entity.name, *entity.aliases)}
        for ko in self._engine.list_knowledge_objects(type=entity.type):
            known = {n.strip().lower() for n in (ko.name, *ko.aliases)}
            if wanted & known:
                return ko
        return None

    def _add_provenance(self, ko_id: str, entity: ExtractedEntity) -> None:
        chunk = (
            self._chunk_by_ordinal.get(entity.chunk_ordinal)
            if entity.chunk_ordinal is not None
            else None
        )
        chunk_id = chunk.id if chunk else None
        quote = entity.quote or None
        # Idempotent on retries: skip an identical existing evidence link.
        for prov in self._engine.get_provenance(knowledge_object_id=ko_id):
            if (
                prov.resource_id == self._resource.id
                and prov.chunk_id == chunk_id
                and prov.quote == quote
            ):
                return
        self._engine.add_provenance(
            knowledge_object_id=ko_id,
            resource_id=self._resource.id,
            chunk_id=chunk_id,
            quote=quote,
        )

    @staticmethod
    def _resolve(name: str, name_to_id: dict[str, str]) -> str | None:
        return name_to_id.get(name.strip().lower())
