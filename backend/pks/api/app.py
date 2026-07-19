"""FastAPI application factory.

Routers stay thin: they translate HTTP to calls on the relevant module's
service layer (ultimately the Core Knowledge Engine). No business logic here.
"""

from fastapi import FastAPI

from pks import __version__
from pks.config import get_settings


def create_app() -> FastAPI:
    app = FastAPI(title="AI PKS", version=__version__)

    @app.get("/api/health")
    def health() -> dict:
        settings = get_settings()
        return {
            "status": "ok",
            "version": __version__,
            "data_dir": str(settings.data_dir),
        }

    return app


app = create_app()
