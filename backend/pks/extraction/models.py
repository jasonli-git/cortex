"""Validated shapes for what the extraction stages get back from the provider.

Provider output passes through these models before touching the engine, so a
malformed response fails loudly at the boundary instead of corrupting
knowledge.
"""

from pydantic import BaseModel, Field, field_validator

from pks.core.models import KnowledgeObjectType

# Entity types extraction may produce (summary objects are made by the
# summarize stage, not extracted from text).
EXTRACTABLE_TYPES = [
    KnowledgeObjectType.CONCEPT,
    KnowledgeObjectType.PERSON,
    KnowledgeObjectType.ORGANIZATION,
    KnowledgeObjectType.PLACE,
    KnowledgeObjectType.EVENT,
]


class ExtractedEntity(BaseModel):
    type: KnowledgeObjectType
    name: str
    description: str = ""
    aliases: list[str] = Field(default_factory=list)
    quote: str = ""
    chunk_ordinal: int | None = None

    @field_validator("name")
    @classmethod
    def _name_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("entity name must not be empty")
        return value.strip()


class ExtractedRelation(BaseModel):
    from_name: str
    to_name: str
    type: str = "related_to"
    confidence: float = 0.8

    @field_validator("confidence")
    @classmethod
    def _clamp(cls, value: float) -> float:
        return min(1.0, max(0.0, value))


class ExtractionResult(BaseModel):
    entities: list[ExtractedEntity] = Field(default_factory=list)
    relations: list[ExtractedRelation] = Field(default_factory=list)


class SummaryResult(BaseModel):
    summary: str
    key_points: list[str] = Field(default_factory=list)
