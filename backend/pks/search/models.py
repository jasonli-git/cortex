"""Search result shapes."""

from pydantic import BaseModel

from pks.core.models import KnowledgeObject, ResourceChunk


class KnowledgeHit(BaseModel):
    score: float
    object: KnowledgeObject


class ChunkHit(BaseModel):
    score: float
    chunk: ResourceChunk
    resource_id: str
    resource_title: str


class SearchResponse(BaseModel):
    query: str
    knowledge: list[KnowledgeHit]
    chunks: list[ChunkHit]
