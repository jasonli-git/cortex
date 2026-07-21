"""Domain models for the Core Knowledge Engine.

Knowledge objects are the primary entities of the system (spec principle 1).
Resources are evidence: inputs that knowledge is extracted from, linked back
via provenance (spec principle 2).
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class KnowledgeObjectType(StrEnum):
    CONCEPT = "concept"
    PERSON = "person"
    ORGANIZATION = "organization"
    PLACE = "place"
    EVENT = "event"
    SUMMARY = "summary"


class ResourceType(StrEnum):
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    NOTE = "note"


class ResourceStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class ResourceRelationship(StrEnum):
    """How the user relates to a resource (spec: active learning vs. reference)."""

    ACTIVE_LEARNING = "active_learning"
    REFERENCE = "reference"


class VersionOperation(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


# Canonical relationship types. The column is a free-form string so extraction
# stages may introduce new types; these are the ones the system itself uses.
RELATED_TO = "related_to"
PART_OF = "part_of"
PARTICIPATED_IN = "participated_in"
LOCATED_IN = "located_in"
SUMMARIZES = "summarizes"


class KnowledgeObject(BaseModel):
    id: str
    type: KnowledgeObjectType
    name: str
    description: str = ""
    aliases: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    version: int = 1
    created_at: str
    updated_at: str


class KnowledgeObjectVersion(BaseModel):
    """One entry in a knowledge object's revision history.

    History is append-only and intentionally survives deletion of the object.
    """

    id: str
    knowledge_object_id: str
    version: int
    operation: VersionOperation
    snapshot: dict
    changed_by: str
    created_at: str


class Relationship(BaseModel):
    id: str
    from_id: str
    to_id: str
    type: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    created_by: str
    metadata: dict = Field(default_factory=dict)
    created_at: str
    updated_at: str


class Provenance(BaseModel):
    """Evidence link: which resource (and where in it) a piece of knowledge came from.

    Exactly one of knowledge_object_id / relationship_id is set.
    """

    id: str
    knowledge_object_id: str | None = None
    relationship_id: str | None = None
    resource_id: str
    chunk_id: str | None = None
    quote: str | None = None
    created_at: str


class Resource(BaseModel):
    id: str
    type: ResourceType
    title: str
    path: str | None = None
    content_hash: str | None = None
    status: ResourceStatus = ResourceStatus.PENDING
    relationship: ResourceRelationship = ResourceRelationship.REFERENCE
    error: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: str
    updated_at: str


class ResourceChunk(BaseModel):
    id: str
    resource_id: str
    ordinal: int
    structure_path: str | None = None
    text: str
    token_count: int | None = None


class WorkspaceRefType(StrEnum):
    RESOURCE = "resource"
    KNOWLEDGE_OBJECT = "knowledge_object"
    CONVERSATION = "conversation"


class Workspace(BaseModel):
    """A context in which knowledge is used. References knowledge; never owns it."""

    id: str
    name: str
    description: str = ""
    created_at: str
    updated_at: str


class WorkspaceRef(BaseModel):
    workspace_id: str
    object_type: WorkspaceRefType
    object_id: str
    created_at: str
