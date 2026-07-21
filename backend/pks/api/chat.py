"""Chat endpoints: converse with the accumulated knowledge."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel

from pks.api.deps import get_store
from pks.chat.models import ChatResult, Conversation, Message
from pks.chat.service import ChatService
from pks.core.store.sqlite import SqliteStore

router = APIRouter(prefix="/api/chat", tags=["chat"])


def get_chat_service(
    request: Request, store: Annotated[SqliteStore, Depends(get_store)]
) -> ChatService:
    state = request.app.state
    return ChatService(store, state.provider, state.embedder, state.settings)


ServiceDep = Annotated[ChatService, Depends(get_chat_service)]


class ChatIn(BaseModel):
    content: str
    conversation_id: str | None = None  # omitted: start a new conversation
    workspace_id: str | None = None  # new conversations only: scope retrieval


class ConversationDetail(BaseModel):
    conversation: Conversation
    messages: list[Message]


@router.post("", response_model=ChatResult)
def chat(body: ChatIn, service: ServiceDep) -> ChatResult:
    return service.ask(
        body.content,
        conversation_id=body.conversation_id,
        workspace_id=body.workspace_id,
    )


@router.get("/conversations", response_model=list[Conversation])
def list_conversations(service: ServiceDep) -> list[Conversation]:
    return service.list_conversations()


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str, service: ServiceDep) -> ConversationDetail:
    return ConversationDetail(
        conversation=service.get_conversation(conversation_id),
        messages=service.list_messages(conversation_id),
    )


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, service: ServiceDep) -> Response:
    service.delete_conversation(conversation_id)
    return Response(status_code=204)
