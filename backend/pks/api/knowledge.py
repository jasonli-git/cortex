"""Knowledge endpoints: browse extracted knowledge objects.

Minimal read surface for now — richer graph traversal arrives with
Milestone 5 and search with Milestone 4.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from pks.api.deps import EngineDep
from pks.core.models import (
    KnowledgeObject,
    KnowledgeObjectType,
    KnowledgeObjectVersion,
    Provenance,
    Relationship,
)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class KnowledgeObjectDetail(BaseModel):
    object: KnowledgeObject
    relationships: list[Relationship]
    provenance: list[Provenance]


@router.get("", response_model=list[KnowledgeObject])
def list_knowledge_objects(
    engine: EngineDep,
    type: KnowledgeObjectType | None = None,
    q: str | None = None,
) -> list[KnowledgeObject]:
    return engine.list_knowledge_objects(type=type, name_contains=q)


@router.get("/{ko_id}", response_model=KnowledgeObjectDetail)
def get_knowledge_object(ko_id: str, engine: EngineDep) -> KnowledgeObjectDetail:
    return KnowledgeObjectDetail(
        object=engine.get_knowledge_object(ko_id),
        relationships=engine.get_relationships(ko_id),
        provenance=engine.get_provenance(knowledge_object_id=ko_id),
    )


@router.get("/{ko_id}/history", response_model=list[KnowledgeObjectVersion])
def get_knowledge_object_history(ko_id: str, engine: EngineDep) -> list[KnowledgeObjectVersion]:
    return engine.get_history(ko_id)
