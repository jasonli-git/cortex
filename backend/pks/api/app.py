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
from pks.api import resources
from pks.config import Settings, get_settings
from pks.core.errors import NotFoundError, ValidationError
from pks.core.store.sqlite import SqliteStore
from pks.events.worker import WorkerThread
from pks.ingestion import build_registry


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    registry = build_registry()

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

    app.include_router(resources.router)

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
        }

    return app


app = create_app()
