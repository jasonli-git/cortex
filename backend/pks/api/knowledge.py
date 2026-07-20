"""Knowledge endpoints: browse extracted knowledge objects.

Minimal read surface for now — richer graph traversal arrives with
Milestone 5 and search with Milestone 4.
"""

from fastapi import APIRouter, Query
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


class GraphOut(BaseModel):
    nodes: list[KnowledgeObject]
    edges: list[Relationship]


@router.get("", response_model=list[KnowledgeObject])
def list_knowledge_objects(
    engine: EngineDep,
    type: KnowledgeObjectType | None = None,
    q: str | None = None,
) -> list[KnowledgeObject]:
    return engine.list_knowledge_objects(type=type, name_contains=q)


# NB: declared before /{ko_id} so 'graph' isn't captured as an id.
@router.get("/graph", response_model=GraphOut)
def get_graph(engine: EngineDep, limit: int = Query(default=500, ge=1, le=2000)) -> GraphOut:
    """The whole knowledge graph (capped), for overview visualisation."""
    nodes, edges = engine.get_graph(limit=limit)
    return GraphOut(nodes=nodes, edges=edges)


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


@router.get("/{ko_id}/graph", response_model=GraphOut)
def get_neighborhood(
    ko_id: str, engine: EngineDep, depth: int = Query(default=1, ge=1, le=3)
) -> GraphOut:
    """The object's neighborhood within `depth` hops."""
    nodes, edges = engine.get_neighborhood(ko_id, depth=depth)
    return GraphOut(nodes=nodes, edges=edges)
