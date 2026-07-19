"""Milestone 0 smoke tests: the app builds, configures, and serves."""

from fastapi.testclient import TestClient

from pks import __version__
from pks.api.app import create_app
from pks.config import Settings


def test_health_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == __version__


def test_settings_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.db_path.name == "pks.db"
    assert settings.resources_dir.parent == settings.data_dir
    assert settings.heavy_model
    assert settings.fast_model
