"""Search endpoint: hybrid semantic + keyword retrieval."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from pks.api.deps import get_store
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
    q: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
) -> SearchResponse:
    return service.search(q, limit=limit)
