"""End-to-end API tests: upload → pipeline → chunks, with the worker running."""

import time

import pytest
from fastapi.testclient import TestClient

from pks.api.app import create_app
from pks.config import Settings


@pytest.fixture
def client(tmp_path):
    settings = Settings(
        _env_file=None,
        data_dir=tmp_path / "data",
        worker_poll_interval=0.02,
    )
    app = create_app(settings=settings)
    with TestClient(app) as client:
        yield client


def wait_for_processing(client: TestClient, resource_id: str, timeout: float = 15.0) -> dict:
    """Poll until the pipeline finishes (ready or failed)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        resource = client.get(f"/api/resources/{resource_id}").json()
        if resource["status"] in ("ready", "failed"):
            return resource
        time.sleep(0.02)
    raise AssertionError(f"resource {resource_id} still {resource['status']} after {timeout}s")


def test_upload_text_end_to_end(client):
    response = client.post(
        "/api/resources/upload",
        files={"file": ("rome.txt", b"Rome was founded in 753 BC.\n\nIt became a republic.")},
        data={"relationship": "active_learning"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["created"] is True
    resource = body["resource"]
    assert resource["type"] == "text"
    assert resource["title"] == "rome"
    assert resource["relationship"] == "active_learning"

    finished = wait_for_processing(client, resource["id"])
    assert finished["status"] == "ready", finished["error"]

    chunks = client.get(f"/api/resources/{resource['id']}/chunks").json()
    assert len(chunks) == 1
    assert "753 BC" in chunks[0]["text"]

    status = client.get(f"/api/resources/{resource['id']}/status").json()
    assert {job["type"]: job["status"] for job in status["jobs"]} == {
        "parse": "done",
        "chunk": "done",
    }


def test_upload_markdown_preserves_structure(client):
    content = b"# Notes\n\n## Topic A\n\nAlpha text.\n\n## Topic B\n\nBeta text."
    response = client.post("/api/resources/upload", files={"file": ("notes.md", content)})
    resource = response.json()["resource"]
    assert resource["type"] == "markdown"

    assert wait_for_processing(client, resource["id"])["status"] == "ready"
    chunks = client.get(f"/api/resources/{resource['id']}/chunks").json()
    assert [c["structure_path"] for c in chunks] == ["Notes > Topic A", "Notes > Topic B"]


def test_duplicate_upload_returns_existing_resource(client):
    content = b"Identical content."
    first = client.post("/api/resources/upload", files={"file": ("a.txt", content)}).json()
    wait_for_processing(client, first["resource"]["id"])

    second = client.post("/api/resources/upload", files={"file": ("b.txt", content)}).json()
    assert second["created"] is False
    assert second["resource"]["id"] == first["resource"]["id"]
    assert len(client.get("/api/resources").json()) == 1


def test_note_end_to_end(client):
    response = client.post(
        "/api/resources/notes",
        json={"title": "Study note", "content": "# Rome\n\nThe Senate governed."},
    )
    assert response.status_code == 200
    resource = response.json()["resource"]
    assert resource["type"] == "note"
    assert resource["title"] == "Study note"

    assert wait_for_processing(client, resource["id"])["status"] == "ready"
    chunks = client.get(f"/api/resources/{resource['id']}/chunks").json()
    assert chunks[0]["structure_path"] == "Rome"


def test_unsupported_extension_rejected(client):
    response = client.post("/api/resources/upload", files={"file": ("data.docx", b"content")})
    assert response.status_code == 400
    assert "unsupported file type" in response.json()["detail"]


def test_empty_note_rejected(client):
    response = client.post("/api/resources/notes", json={"title": "x", "content": "  "})
    assert response.status_code == 400


def test_missing_resource_is_404(client):
    assert client.get("/api/resources/nope").status_code == 404
