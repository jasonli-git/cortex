"""FastAPI application factory.

Routers stay thin: they translate HTTP to calls on the relevant module's
service layer (ultimately the Core Knowledge Engine). No business logic here.

The app owns the pipeline worker's lifecycle: a daemon thread with its own
database connection, started on startup and stopped on shutdown.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from pks import __version__
from pks.api import chat, knowledge, resources, search, workspaces
from pks.config import Settings, get_settings
from pks.core.errors import NotFoundError, ValidationError
from pks.core.store.sqlite import SqliteStore
from pks.embeddings import EmbeddingProvider, make_embedder
from pks.events.worker import WorkerThread
from pks.pipeline import build_pipeline
from pks.providers import CompletionProvider, make_provider


def create_app(
    settings: Settings | None = None,
    provider: CompletionProvider | None = None,
    embedder: EmbeddingProvider | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    if provider is None:
        provider = make_provider(settings)
    if embedder is None:
        embedder = make_embedder(settings)
    registry = build_pipeline(provider, embedder)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings.resources_dir.mkdir(parents=True, exist_ok=True)
        # Apply migrations once before the API and worker race to open the db.
        SqliteStore(settings.db_path).close()
        worker = WorkerThread(settings, registry)
        worker.start()
        try:
            yield
        finally:
            worker.stop()

    app = FastAPI(title="AI PKS", version=__version__, lifespan=lifespan)
    app.state.settings = settings
    app.state.registry = registry
    app.state.embedder = embedder
    app.state.provider = provider

    app.include_router(resources.router)
    app.include_router(knowledge.router)
    app.include_router(search.router)
    app.include_router(chat.router)
    app.include_router(workspaces.router)

    @app.exception_handler(NotFoundError)
    async def not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def invalid(request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.get("/api/health")
    def health() -> dict:
        return {
            "status": "ok",
            "version": __version__,
            "data_dir": str(settings.data_dir),
            "ai_enabled": provider is not None,
        }

    return app


app = create_app()
