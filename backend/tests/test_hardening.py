"""Tests for Milestone 9: reprocessing, jobs view, learning events."""

import time

import pytest
from fastapi.testclient import TestClient

from pks.api.app import create_app
from pks.chat.service import ChatService
from pks.config import Settings
from pks.core import KnowledgeEngine
from pks.core.store import SqliteStore
from pks.events import JobQueue, Worker
from pks.ingestion import intake
from pks.pipeline import build_pipeline
from tests.fakes import ROME_MD, FakeEmbedder, FakeProvider


@pytest.fixture
def settings(tmp_path):
    return Settings(
        _env_file=None,
        data_dir=tmp_path / "data",
        worker_poll_interval=0.02,
        anthropic_api_key=None,
    )


@pytest.fixture
def client(settings):
    app = create_app(settings=settings, provider=FakeProvider(), embedder=FakeEmbedder())
    with TestClient(app) as client:
        yield client


def wait_ready(client: TestClient, resource_id: str, timeout: float = 15.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        resource = client.get(f"/api/resources/{resource_id}").json()
        if resource["status"] in ("ready", "failed"):
            return resource
        time.sleep(0.02)
    raise AssertionError("timed out waiting for pipeline")


# ----------------------------------------------------------------------
# Reprocessing
# ----------------------------------------------------------------------


def test_reprocess_rebuilds_without_duplicating_knowledge(settings, client):
    resource = client.post(
        "/api/resources/upload", files={"file": ("rome.md", ROME_MD)}
    ).json()["resource"]
    assert wait_ready(client, resource["id"])["status"] == "ready"

    store = SqliteStore(settings.db_path)
    engine = KnowledgeEngine(store)
    old_chunk_ids = {c.id for c in engine.get_chunks(resource["id"])}
    rome = engine.list_knowledge_objects(type="place", name_contains="Rome")[0]
    provs_before = engine.get_provenance(knowledge_object_id=rome.id)

    reprocessed = client.post(f"/api/resources/{resource['id']}/reprocess")
    assert reprocessed.status_code == 200
    assert wait_ready(client, resource["id"])["status"] == "ready"

    new_chunks = engine.get_chunks(resource["id"])
    assert {c.id for c in new_chunks} & old_chunk_ids == set()  # chunks rebuilt

    # Same knowledge, same amount of evidence — re-pointed at the new chunks.
    assert len(engine.list_knowledge_objects(type="place", name_contains="Rome")) == 1
    provs_after = engine.get_provenance(knowledge_object_id=rome.id)
    assert len(provs_after) == len(provs_before) == 1
    assert provs_after[0].chunk_id in {c.id for c in new_chunks}

    # Two full pipeline runs are visible in the job history.
    jobs = client.get(f"/api/resources/{resource['id']}/status").json()["jobs"]
    assert [j["type"] for j in jobs].count("parse") == 2
    store.close()


def test_reprocess_requires_original_file(settings, client):
    resource = client.post(
        "/api/resources/upload", files={"file": ("rome.md", ROME_MD)}
    ).json()["resource"]
    assert wait_ready(client, resource["id"])["status"] == "ready"

    original = settings.resources_dir / resource["path"]
    original.unlink()
    response = client.post(f"/api/resources/{resource['id']}/reprocess")
    assert response.status_code == 400
    assert "original file is missing" in response.json()["detail"]


# ----------------------------------------------------------------------
# Jobs view
# ----------------------------------------------------------------------


def test_jobs_endpoint_reports_counts_and_recent_jobs(client):
    resource = client.post(
        "/api/resources/upload", files={"file": ("rome.md", ROME_MD)}
    ).json()["resource"]
    wait_ready(client, resource["id"])

    body = client.get("/api/jobs").json()
    assert body["counts"]["done"] >= 3
    assert body["counts"]["failed"] == 0
    assert {"queued", "running", "done", "failed"} <= set(body["counts"])
    # Newest first: the last stage of the run leads the list.
    assert body["jobs"][0]["type"] in ("dedupe", "index")

    failed_only = client.get("/api/jobs", params={"status": "failed"}).json()
    assert failed_only["jobs"] == []


# ----------------------------------------------------------------------
# Learning events
# ----------------------------------------------------------------------


def test_learning_events_accumulate(settings, tmp_path):
    store = SqliteStore(settings.db_path)
    engine = KnowledgeEngine(store)
    embedder = FakeEmbedder()
    registry = build_pipeline(FakeProvider(), embedder)
    queue = JobQueue(store)

    intake.save_upload(
        engine, settings, registry, queue, filename="rome.md", content=ROME_MD
    )
    intake.create_note(engine, settings, registry, queue, title="Note", content="# N\n\nBody")
    Worker(settings, registry).drain()

    chat = ChatService(store, FakeProvider(), embedder, settings)
    chat.ask("When did the Republic begin?")

    kinds = [e.kind.value for e in engine.list_learning_events()]
    assert kinds.count("resource_ingested") == 1
    assert kinds.count("note_written") == 1
    assert kinds.count("question_asked") == 1

    questions = engine.list_learning_events(kind="question_asked")
    assert questions[0].detail["question"] == "When did the Republic begin?"
    assert questions[0].subject_type == "conversation"
    store.close()
