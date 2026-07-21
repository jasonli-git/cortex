"""Tests for workspaces: CRUD, references, hydration, and scoped retrieval."""

import time

import pytest
from fastapi.testclient import TestClient

from pks.api.app import create_app
from pks.chat.service import ChatService
from pks.config import Settings
from pks.core import KnowledgeEngine
from pks.core.errors import NotFoundError, ValidationError
from pks.core.store import SqliteStore
from pks.events import JobQueue, Worker
from pks.ingestion import intake
from pks.pipeline import build_pipeline
from tests.fakes import ROME_MD, FakeEmbedder, FakeProvider

CARTHAGE_TXT = b"Carthage was a Phoenician city in North Africa, destroyed in 146 BC."


@pytest.fixture
def settings(tmp_path):
    return Settings(_env_file=None, data_dir=tmp_path / "data", anthropic_api_key=None)


@pytest.fixture
def store(settings):
    store = SqliteStore(settings.db_path)
    yield store
    store.close()


@pytest.fixture
def engine(store):
    return KnowledgeEngine(store)


# ----------------------------------------------------------------------
# Engine: CRUD + refs
# ----------------------------------------------------------------------


def test_workspace_crud(engine):
    ws = engine.create_workspace(name="American History", description="Learning project")
    assert engine.get_workspace(ws.id).name == "American History"
    assert [w.id for w in engine.list_workspaces()] == [ws.id]

    updated = engine.update_workspace(ws.id, description="Semester project")
    assert updated.description == "Semester project"
    assert updated.name == "American History"

    engine.delete_workspace(ws.id)
    with pytest.raises(NotFoundError):
        engine.get_workspace(ws.id)


def test_workspace_names_are_unique(engine):
    engine.create_workspace(name="Investing")
    with pytest.raises(ValidationError):
        engine.create_workspace(name="Investing")
    other = engine.create_workspace(name="Photography")
    with pytest.raises(ValidationError):
        engine.update_workspace(other.id, name="Investing")


def test_attach_validates_and_is_idempotent(engine):
    ws = engine.create_workspace(name="WS")
    resource = engine.register_resource(type="text", title="Doc")
    ko = engine.create_knowledge_object(type="concept", name="Thing")

    engine.attach_to_workspace(ws.id, "resource", resource.id)
    engine.attach_to_workspace(ws.id, "resource", resource.id)  # idempotent
    engine.attach_to_workspace(ws.id, "knowledge_object", ko.id)

    refs = engine.get_workspace_refs(ws.id)
    assert len(refs) == 2
    assert engine.workspace_object_ids(ws.id, "resource") == [resource.id]

    with pytest.raises(NotFoundError):
        engine.attach_to_workspace(ws.id, "resource", "missing")
    with pytest.raises(NotFoundError):
        engine.attach_to_workspace(ws.id, "knowledge_object", "missing")


def test_detach_and_delete_leave_objects_intact(engine):
    ws = engine.create_workspace(name="WS")
    resource = engine.register_resource(type="text", title="Doc")
    engine.attach_to_workspace(ws.id, "resource", resource.id)

    engine.detach_from_workspace(ws.id, "resource", resource.id)
    assert engine.get_workspace_refs(ws.id) == []
    with pytest.raises(NotFoundError):
        engine.detach_from_workspace(ws.id, "resource", resource.id)

    engine.attach_to_workspace(ws.id, "resource", resource.id)
    engine.delete_workspace(ws.id)
    # The knowledge survives the workspace (spec: workspaces never own).
    assert engine.get_resource(resource.id).title == "Doc"


# ----------------------------------------------------------------------
# Workspace-scoped retrieval (chat)
# ----------------------------------------------------------------------


def ingest(settings, store, registry, filename, content):
    engine = KnowledgeEngine(store)
    queue = JobQueue(store)
    resource, _ = intake.save_upload(
        engine, settings, registry, queue, filename=filename, content=content
    )
    worker = Worker(settings, registry)
    worker.drain()
    worker.close()
    return engine.get_resource(resource.id)


def test_chat_scoped_to_workspace(settings, store, engine):
    embedder = FakeEmbedder()
    registry = build_pipeline(FakeProvider(), embedder)
    rome = ingest(settings, store, registry, "rome.md", ROME_MD)
    ingest(settings, store, registry, "carthage.txt", CARTHAGE_TXT)

    ws = engine.create_workspace(name="Rome studies")
    engine.attach_to_workspace(ws.id, "resource", rome.id)

    provider = FakeProvider()
    service = ChatService(store, provider, embedder, settings)
    result = service.ask("Tell me about the Phoenician city in Africa", workspace_id=ws.id)

    assert result.conversation.workspace_id == ws.id
    prompt = provider.chat_prompts[0]
    # Out-of-workspace content is not offered as a source…
    assert "Phoenician city in North Africa" not in prompt
    # …while in-workspace content is.
    assert "Roman Republic" in prompt

    # Follow-ups inherit the conversation's workspace scope.
    service.ask("more", conversation_id=result.conversation.id)
    assert "Phoenician city in North Africa" not in provider.chat_prompts[1]


def test_chat_in_empty_workspace_falls_back_unscoped(settings, store, engine):
    embedder = FakeEmbedder()
    registry = build_pipeline(FakeProvider(), embedder)
    ingest(settings, store, registry, "carthage.txt", CARTHAGE_TXT)

    ws = engine.create_workspace(name="Empty")
    provider = FakeProvider()
    service = ChatService(store, provider, embedder, settings)
    service.ask("Phoenician city", workspace_id=ws.id)

    assert "Phoenician city in North Africa" in provider.chat_prompts[0]


def test_chat_rejects_unknown_workspace(settings, store, engine):
    service = ChatService(store, FakeProvider(), FakeEmbedder(), settings)
    with pytest.raises(NotFoundError):
        service.ask("hello", workspace_id="missing")


# ----------------------------------------------------------------------
# API
# ----------------------------------------------------------------------


def test_workspace_api_end_to_end(tmp_path):
    settings = Settings(
        _env_file=None,
        data_dir=tmp_path / "data",
        worker_poll_interval=0.02,
        anthropic_api_key=None,
    )
    app = create_app(settings=settings, provider=FakeProvider(), embedder=FakeEmbedder())
    with TestClient(app) as client:
        ws = client.post(
            "/api/workspaces", json={"name": "History", "description": "Learning"}
        ).json()
        assert client.post("/api/workspaces", json={"name": "History"}).status_code == 400

        # Upload directly into the workspace.
        resource = client.post(
            "/api/resources/upload",
            files={"file": ("rome.md", ROME_MD)},
            data={"workspace_id": ws["id"]},
        ).json()["resource"]

        # A note into the workspace too.
        note = client.post(
            "/api/resources/notes",
            json={"title": "My note", "content": "Remember the Senate.", "workspace_id": ws["id"]},
        ).json()["resource"]

        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            statuses = {
                client.get(f"/api/resources/{rid}").json()["status"]
                for rid in (resource["id"], note["id"])
            }
            if statuses <= {"ready", "failed"}:
                break
            time.sleep(0.02)

        # Start a workspace conversation and attach it explicitly.
        conversation = client.post(
            "/api/chat", json={"content": "hi", "workspace_id": ws["id"]}
        ).json()["conversation"]
        assert conversation["workspace_id"] == ws["id"]
        client.post(
            f"/api/workspaces/{ws['id']}/refs",
            json={"object_type": "conversation", "object_id": conversation["id"]},
        )
        missing = client.post(
            f"/api/workspaces/{ws['id']}/refs",
            json={"object_type": "conversation", "object_id": "nope"},
        )
        assert missing.status_code == 404

        detail = client.get(f"/api/workspaces/{ws['id']}").json()
        assert {r["id"] for r in detail["resources"]} == {resource["id"], note["id"]}
        assert [c["id"] for c in detail["conversations"]] == [conversation["id"]]

        # Scoped search only sees workspace resources.
        scoped = client.get(
            "/api/search", params={"q": "Republic", "workspace_id": ws["id"]}
        ).json()
        assert scoped["chunks"]
        assert {c["resource_id"] for c in scoped["chunks"]} <= {resource["id"], note["id"]}

        # Detach, then delete the workspace; the resource must survive.
        assert (
            client.delete(
                f"/api/workspaces/{ws['id']}/refs/resource/{note['id']}"
            ).status_code
            == 204
        )
        assert client.delete(f"/api/workspaces/{ws['id']}").status_code == 204
        assert client.get(f"/api/workspaces/{ws['id']}").status_code == 404
        assert client.get(f"/api/resources/{resource['id']}").status_code == 200
