"""The Core Knowledge Engine's public API.

Every module (ingestion, extraction, search, chat, workspaces, …) manipulates
knowledge exclusively through this class. Responsibilities per the spec:
storing knowledge, maintaining relationships, provenance, and versioning.
Semantic retrieval joins in Milestone 4 (search module).
"""

from uuid import uuid4

from pks.core.errors import NotFoundError, ValidationError
from pks.core.models import (
    KnowledgeObject,
    KnowledgeObjectType,
    KnowledgeObjectVersion,
    Provenance,
    Relationship,
    Resource,
    ResourceChunk,
    ResourceRelationship,
    ResourceStatus,
    ResourceType,
    VersionOperation,
)
from pks.core.store.db import utcnow
from pks.core.store.interfaces import Store

_KO_UPDATABLE_FIELDS = {"name", "description", "aliases", "metadata"}


def _new_id() -> str:
    return uuid4().hex


class KnowledgeEngine:
    def __init__(self, store: Store):
        self._store = store

    # ------------------------------------------------------------------
    # Knowledge objects
    # ------------------------------------------------------------------

    def create_knowledge_object(
        self,
        *,
        type: KnowledgeObjectType | str,
        name: str,
        description: str = "",
        aliases: list[str] | None = None,
        metadata: dict | None = None,
        changed_by: str = "user",
    ) -> KnowledgeObject:
        if not name.strip():
            raise ValidationError("knowledge object name must not be empty")
        now = utcnow()
        ko = KnowledgeObject(
            id=_new_id(),
            type=KnowledgeObjectType(type),
            name=name.strip(),
            description=description,
            aliases=aliases or [],
            metadata=metadata or {},
            version=1,
            created_at=now,
            updated_at=now,
        )
        with self._store.transaction():
            self._store.knowledge_objects.insert(ko)
            self._record_version(ko, VersionOperation.CREATED, changed_by)
        return ko

    def get_knowledge_object(self, ko_id: str) -> KnowledgeObject:
        ko = self._store.knowledge_objects.get(ko_id)
        if ko is None:
            raise NotFoundError(f"knowledge object {ko_id!r} not found")
        return ko

    def list_knowledge_objects(
        self,
        *,
        type: KnowledgeObjectType | str | None = None,
        name_contains: str | None = None,
    ) -> list[KnowledgeObject]:
        ko_type = KnowledgeObjectType(type) if type is not None else None
        return self._store.knowledge_objects.list(type=ko_type, name_contains=name_contains)

    def update_knowledge_object(
        self, ko_id: str, *, changed_by: str = "user", **changes: object
    ) -> KnowledgeObject:
        unknown = set(changes) - _KO_UPDATABLE_FIELDS
        if unknown:
            raise ValidationError(f"cannot update field(s): {', '.join(sorted(unknown))}")
        if not changes:
            raise ValidationError("no changes given")

        ko = self.get_knowledge_object(ko_id)
        updated = ko.model_copy(update=dict(changes))
        if not updated.name.strip():
            raise ValidationError("knowledge object name must not be empty")
        updated = updated.model_copy(
            update={"version": ko.version + 1, "updated_at": utcnow()}
        )
        with self._store.transaction():
            self._store.knowledge_objects.update(updated)
            self._record_version(updated, VersionOperation.UPDATED, changed_by)
        return updated

    def delete_knowledge_object(self, ko_id: str, *, changed_by: str = "user") -> None:
        """Delete a knowledge object (relationships and provenance cascade).

        The revision history is retained: a final 'deleted' entry snapshots the
        object's last state.
        """
        ko = self.get_knowledge_object(ko_id)
        with self._store.transaction():
            self._store.knowledge_objects.delete(ko_id)
            self._record_version(ko, VersionOperation.DELETED, changed_by)

    def get_history(self, ko_id: str) -> list[KnowledgeObjectVersion]:
        history = self._store.knowledge_objects.list_versions(ko_id)
        if not history:
            raise NotFoundError(f"no history for knowledge object {ko_id!r}")
        return history

    def _record_version(
        self, ko: KnowledgeObject, operation: VersionOperation, changed_by: str
    ) -> None:
        self._store.knowledge_objects.insert_version(
            KnowledgeObjectVersion(
                id=_new_id(),
                knowledge_object_id=ko.id,
                version=ko.version,
                operation=operation,
                snapshot=ko.model_dump(mode="json"),
                changed_by=changed_by,
                created_at=utcnow(),
            )
        )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    def relate(
        self,
        from_id: str,
        to_id: str,
        type: str,
        *,
        confidence: float = 1.0,
        created_by: str = "user",
        metadata: dict | None = None,
    ) -> Relationship:
        """Create (or refresh) a typed relationship between two knowledge objects.

        Idempotent on (from, to, type): repeating the call updates confidence
        and metadata — relationships are continuously improved, not duplicated
        (spec principle 4).
        """
        if from_id == to_id:
            raise ValidationError("a knowledge object cannot relate to itself")
        if not type.strip():
            raise ValidationError("relationship type must not be empty")
        if not 0.0 <= confidence <= 1.0:
            raise ValidationError("confidence must be between 0.0 and 1.0")
        self.get_knowledge_object(from_id)
        self.get_knowledge_object(to_id)

        now = utcnow()
        rel = Relationship(
            id=_new_id(),
            from_id=from_id,
            to_id=to_id,
            type=type.strip(),
            confidence=confidence,
            created_by=created_by,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )
        with self._store.transaction():
            return self._store.relationships.upsert(rel)

    def get_relationship(self, rel_id: str) -> Relationship:
        rel = self._store.relationships.get(rel_id)
        if rel is None:
            raise NotFoundError(f"relationship {rel_id!r} not found")
        return rel

    def unrelate(self, rel_id: str) -> None:
        with self._store.transaction():
            if not self._store.relationships.delete(rel_id):
                raise NotFoundError(f"relationship {rel_id!r} not found")

    def get_relationships(self, ko_id: str) -> list[Relationship]:
        """All relationships in which the knowledge object participates."""
        self.get_knowledge_object(ko_id)
        return self._store.relationships.list_for(ko_id)

    def get_neighbors(self, ko_id: str) -> list[KnowledgeObject]:
        """Knowledge objects directly connected to the given one."""
        neighbor_ids = {
            rel.to_id if rel.from_id == ko_id else rel.from_id
            for rel in self.get_relationships(ko_id)
        }
        return [self.get_knowledge_object(nid) for nid in sorted(neighbor_ids)]

    # ------------------------------------------------------------------
    # Provenance
    # ------------------------------------------------------------------

    def add_provenance(
        self,
        *,
        knowledge_object_id: str | None = None,
        relationship_id: str | None = None,
        resource_id: str,
        chunk_id: str | None = None,
        quote: str | None = None,
    ) -> Provenance:
        if (knowledge_object_id is None) == (relationship_id is None):
            raise ValidationError(
                "exactly one of knowledge_object_id / relationship_id must be set"
            )
        if knowledge_object_id is not None:
            self.get_knowledge_object(knowledge_object_id)
        if relationship_id is not None:
            self.get_relationship(relationship_id)
        self.get_resource(resource_id)
        if chunk_id is not None:
            chunk = self._store.resources.get_chunk(chunk_id)
            if chunk is None or chunk.resource_id != resource_id:
                raise ValidationError(f"chunk {chunk_id!r} does not belong to {resource_id!r}")

        prov = Provenance(
            id=_new_id(),
            knowledge_object_id=knowledge_object_id,
            relationship_id=relationship_id,
            resource_id=resource_id,
            chunk_id=chunk_id,
            quote=quote,
            created_at=utcnow(),
        )
        with self._store.transaction():
            self._store.provenance.insert(prov)
        return prov

    def get_provenance(
        self,
        *,
        knowledge_object_id: str | None = None,
        relationship_id: str | None = None,
    ) -> list[Provenance]:
        if (knowledge_object_id is None) == (relationship_id is None):
            raise ValidationError(
                "exactly one of knowledge_object_id / relationship_id must be set"
            )
        if knowledge_object_id is not None:
            return self._store.provenance.list_for_knowledge_object(knowledge_object_id)
        assert relationship_id is not None
        return self._store.provenance.list_for_relationship(relationship_id)

    # ------------------------------------------------------------------
    # Resources (evidence)
    # ------------------------------------------------------------------

    def register_resource(
        self,
        *,
        type: ResourceType | str,
        title: str,
        path: str | None = None,
        content_hash: str | None = None,
        relationship: ResourceRelationship | str = ResourceRelationship.REFERENCE,
        metadata: dict | None = None,
    ) -> Resource:
        if not title.strip():
            raise ValidationError("resource title must not be empty")
        now = utcnow()
        resource = Resource(
            id=_new_id(),
            type=ResourceType(type),
            title=title.strip(),
            path=path,
            content_hash=content_hash,
            status=ResourceStatus.PENDING,
            relationship=ResourceRelationship(relationship),
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )
        with self._store.transaction():
            self._store.resources.insert(resource)
        return resource

    def get_resource(self, resource_id: str) -> Resource:
        resource = self._store.resources.get(resource_id)
        if resource is None:
            raise NotFoundError(f"resource {resource_id!r} not found")
        return resource

    def list_resources(self) -> list[Resource]:
        return self._store.resources.list()

    def set_resource_status(
        self, resource_id: str, status: ResourceStatus | str, *, error: str | None = None
    ) -> Resource:
        resource = self.get_resource(resource_id)
        updated = resource.model_copy(
            update={
                "status": ResourceStatus(status),
                "error": error,
                "updated_at": utcnow(),
            }
        )
        with self._store.transaction():
            self._store.resources.update(updated)
        return updated

    def set_chunks(
        self, resource_id: str, chunks: list[tuple[int, str, str | None, int | None]]
    ) -> list[ResourceChunk]:
        """Replace a resource's chunks. Each chunk: (ordinal, text, structure_path, token_count)."""
        self.get_resource(resource_id)
        models = [
            ResourceChunk(
                id=_new_id(),
                resource_id=resource_id,
                ordinal=ordinal,
                structure_path=structure_path,
                text=text,
                token_count=token_count,
            )
            for ordinal, text, structure_path, token_count in chunks
        ]
        with self._store.transaction():
            self._store.resources.replace_chunks(resource_id, models)
        return models

    def get_chunks(self, resource_id: str) -> list[ResourceChunk]:
        self.get_resource(resource_id)
        return self._store.resources.list_chunks(resource_id)
