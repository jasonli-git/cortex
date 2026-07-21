"""Workspace endpoints: contexts referencing knowledge (never owning it)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from pks.api.deps import EngineDep, get_store
from pks.chat.models import Conversation
from pks.chat.store import ChatStore
from pks.core.errors import NotFoundError
from pks.core.models import (
    KnowledgeObject,
    Resource,
    Workspace,
    WorkspaceRef,
    WorkspaceRefType,
)
from pks.core.store.sqlite import SqliteStore

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


def get_chat_store(store: Annotated[SqliteStore, Depends(get_store)]) -> ChatStore:
    return ChatStore(store)


ChatStoreDep = Annotated[ChatStore, Depends(get_chat_store)]


class WorkspaceIn(BaseModel):
    name: str
    description: str = ""


class WorkspacePatch(BaseModel):
    name: str | None = None
    description: str | None = None


class RefIn(BaseModel):
    object_type: WorkspaceRefType
    object_id: str


class WorkspaceDetail(BaseModel):
    workspace: Workspace
    resources: list[Resource]
    knowledge_objects: list[KnowledgeObject]
    conversations: list[Conversation]


@router.post("", response_model=Workspace)
def create_workspace(body: WorkspaceIn, engine: EngineDep) -> Workspace:
    return engine.create_workspace(name=body.name, description=body.description)


@router.get("", response_model=list[Workspace])
def list_workspaces(engine: EngineDep) -> list[Workspace]:
    return engine.list_workspaces()


@router.get("/{workspace_id}", response_model=WorkspaceDetail)
def get_workspace(
    workspace_id: str, engine: EngineDep, chat_store: ChatStoreDep
) -> WorkspaceDetail:
    """The workspace with its referenced objects hydrated (stale refs skipped)."""
    workspace = engine.get_workspace(workspace_id)
    resources: list[Resource] = []
    knowledge_objects: list[KnowledgeObject] = []
    conversations: list[Conversation] = []
    for ref in engine.get_workspace_refs(workspace_id):
        try:
            if ref.object_type is WorkspaceRefType.RESOURCE:
                resources.append(engine.get_resource(ref.object_id))
            elif ref.object_type is WorkspaceRefType.KNOWLEDGE_OBJECT:
                knowledge_objects.append(engine.get_knowledge_object(ref.object_id))
            else:
                conversation = chat_store.get_conversation(ref.object_id)
                if conversation is not None:
                    conversations.append(conversation)
        except NotFoundError:
            continue  # the underlying object was deleted; the ref is stale
    return WorkspaceDetail(
        workspace=workspace,
        resources=resources,
        knowledge_objects=knowledge_objects,
        conversations=conversations,
    )


@router.patch("/{workspace_id}", response_model=Workspace)
def update_workspace(
    workspace_id: str, body: WorkspacePatch, engine: EngineDep
) -> Workspace:
    return engine.update_workspace(
        workspace_id, name=body.name, description=body.description
    )


@router.delete("/{workspace_id}", status_code=204)
def delete_workspace(workspace_id: str, engine: EngineDep) -> Response:
    engine.delete_workspace(workspace_id)
    return Response(status_code=204)


@router.post("/{workspace_id}/refs", response_model=WorkspaceRef)
def attach(
    workspace_id: str, body: RefIn, engine: EngineDep, chat_store: ChatStoreDep
) -> WorkspaceRef:
    # Conversations belong to the chat module, so the engine can't validate them.
    if (
        body.object_type is WorkspaceRefType.CONVERSATION
        and chat_store.get_conversation(body.object_id) is None
    ):
        raise NotFoundError(f"conversation {body.object_id!r} not found")
    return engine.attach_to_workspace(workspace_id, body.object_type, body.object_id)


@router.delete("/{workspace_id}/refs/{object_type}/{object_id}", status_code=204)
def detach(
    workspace_id: str,
    object_type: WorkspaceRefType,
    object_id: str,
    engine: EngineDep,
) -> Response:
    engine.detach_from_workspace(workspace_id, object_type, object_id)
    return Response(status_code=204)
