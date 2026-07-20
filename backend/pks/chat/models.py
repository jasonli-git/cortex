"""Chat domain models.

The transparency principle (spec #7) is structural here: an assistant answer
is a sequence of segments, each labeled with where it came from — the user's
PKS (with numbered citations) or the model's general knowledge.
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class Segment(BaseModel):
    text: str
    source: Literal["pks", "model"]
    source_numbers: list[int] = Field(default_factory=list)


class Citation(BaseModel):
    number: int
    kind: Literal["chunk", "knowledge_object"]
    id: str
    title: str  # resource title (chunk) or object name
    resource_id: str | None = None
    structure_path: str | None = None
    excerpt: str | None = None


class Message(BaseModel):
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    segments: list[Segment] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    created_at: str


class Conversation(BaseModel):
    id: str
    workspace_id: str | None = None
    title: str
    created_at: str
    updated_at: str


class ChatResult(BaseModel):
    conversation: Conversation
    user_message: Message
    assistant_message: Message
