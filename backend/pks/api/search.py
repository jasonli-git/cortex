"""Search endpoint: hybrid semantic + keyword retrieval."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from pks.api.deps import EngineDep, get_store
from pks.core.models import WorkspaceRefType
from pks.core.store.sqlite import SqliteStore
from pks.search.models import SearchResponse
from pks.search.service import SearchService

router = APIRouter(prefix="/api/search", tags=["search"])


def get_search_service(
    request: Request, store: Annotated[SqliteStore, Depends(get_store)]
) -> SearchService:
    return SearchService(store, request.app.state.embedder)


@router.get("", response_model=SearchResponse)
def search(
    service: Annotated[SearchService, Depends(get_search_service)],
    engine: EngineDep,
    q: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
    workspace_id: str | None = None,
) -> SearchResponse:
    resource_ids: set[str] | None = None
    ko_ids: set[str] | None = None
    if workspace_id is not None:
        resources = set(engine.workspace_object_ids(workspace_id, WorkspaceRefType.RESOURCE))
        kos = set(
            engine.workspace_object_ids(workspace_id, WorkspaceRefType.KNOWLEDGE_OBJECT)
        )
        for resource_id in resources:
            kos.update(engine.knowledge_object_ids_for_resource(resource_id))
        if resources or kos:
            resource_ids, ko_ids = resources, kos
    return service.search(q, limit=limit, resource_ids=resource_ids, knowledge_object_ids=ko_ids)
