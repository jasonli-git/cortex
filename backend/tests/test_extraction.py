"""Tests for the AI extraction stages, using a fake provider (no network)."""

import time

import pytest
from fastapi.testclient import TestClient

from pks.api.app import create_app
from pks.config import Settings
from pks.core import KnowledgeEngine
from pks.core.models import ResourceChunk
from pks.core.store import SqliteStore
from pks.events import JobQueue, Worker
from pks.extraction.extractor import batch_chunks
from pks.ingestion import intake
from pks.pipeline import build_pipeline
from pks.providers import make_provider
from pks.providers.anthropic import AnthropicProvider
from tests.fakes import (
    ROME_MD,
    FakeEmbedder,
    FakeProvider,
)


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


def ingest_and_drain(settings, store, registry, *, filename: str, content: bytes):
    engine = KnowledgeEngine(store)
    queue = JobQueue(store)
    resource, _ = intake.save_upload(
        engine, settings, registry, queue, filename=filename, content=content
    )
    worker = Worker(settings, registry)
    worker.drain()
    worker.close()
    return engine.get_resource(resource.id)


# ----------------------------------------------------------------------
# Full pipeline with extraction
# ----------------------------------------------------------------------


def test_pipeline_extracts_knowledge_with_provenance(settings, store, engine):
    fake = FakeProvider()
    registry = build_pipeline(fake, FakeEmbedder())

    resource = ingest_and_drain(settings, store, registry, filename="rome.md", content=ROME_MD)
    assert resource.status.value == "ready", resource.error

    rome = engine.list_knowledge_objects(type="place", name_contains="Rome")[0]
    republic = engine.list_knowledge_objects(type="concept", name_contains="Roman Republic")[0]
    assert republic.aliases == ["the Republic"]

    # Provenance points at the exact chunk the quote came from.
    chunks = engine.get_chunks(resource.id)
    [rome_prov] = engine.get_provenance(knowledge_object_id=rome.id)
    assert rome_prov.chunk_id == chunks[0].id
    assert rome_prov.quote == "Rome was founded in 753 BC"

    # The resolvable relation exists; the one naming an unextracted entity was skipped.
    rels = engine.get_relationships(republic.id)
    assert [(r.type, r.to_id) for r in rels] == [("located_in", rome.id)]
    assert rels[0].confidence == 0.9
    assert rels[0].created_by == "extraction"


def test_pipeline_creates_summary_object(settings, store, engine):
    registry = build_pipeline(FakeProvider(), FakeEmbedder())
    resource = ingest_and_drain(settings, store, registry, filename="rome.md", content=ROME_MD)

    [summary] = engine.list_knowledge_objects(type="summary")
    assert summary.name == "Summary of rome"
    assert "753 BC" in summary.description
    assert summary.metadata["key_points"] == ["Founded 753 BC", "Republic from 509 BC"]
    assert summary.metadata["resource_id"] == resource.id

    [prov] = engine.get_provenance(knowledge_object_id=summary.id)
    assert prov.resource_id == resource.id
    assert prov.chunk_id is None


def test_second_resource_merges_into_existing_entities(settings, store, engine):
    fake = FakeProvider(
        extraction={
            "entities": [
                {
                    # Matches the existing Roman Republic KO via its alias.
                    "type": "concept",
                    "name": "the Republic",
                    "description": "ignored, existing description wins",
                    "aliases": ["Res publica"],
                    "quote": "the Republic endured",
                    "chunk_ordinal": 0,
                },
            ],
            "relations": [],
        }
    )
    registry = build_pipeline(FakeProvider(), FakeEmbedder())
    ingest_and_drain(settings, store, registry, filename="rome.md", content=ROME_MD)

    registry2 = build_pipeline(fake, FakeEmbedder())
    second = ingest_and_drain(
        settings,
        store,
        registry2,
        filename="more.txt",
        content=b"The Republic endured for centuries.",
    )

    republics = engine.list_knowledge_objects(type="concept", name_contains="Roman Republic")
    assert len(republics) == 1
    republic = republics[0]
    # Alias set grew; existing description kept.
    assert "Res publica" in republic.aliases
    assert republic.description == "The Roman state after the monarchy, from 509 BC."
    # Evidence from both resources.
    provs = engine.get_provenance(knowledge_object_id=republic.id)
    assert {p.resource_id for p in provs} >= {second.id}
    assert len(provs) == 2


def test_extraction_is_idempotent_on_provenance(settings, store, engine):
    """Re-running extraction (e.g. after a retry) must not duplicate evidence."""
    fake = FakeProvider()
    registry = build_pipeline(fake, FakeEmbedder())
    resource = ingest_and_drain(settings, store, registry, filename="rome.md", content=ROME_MD)

    queue = JobQueue(store)
    registry.publish(queue, "resource.chunked", {"resource_id": resource.id})
    worker = Worker(settings, registry)
    worker.drain()
    worker.close()

    rome = engine.list_knowledge_objects(type="place", name_contains="Rome")[0]
    assert len(engine.get_provenance(knowledge_object_id=rome.id)) == 1


def test_pipeline_without_provider_marks_ready_after_chunk(settings, store, engine):
    registry = build_pipeline(None, FakeEmbedder())
    resource = ingest_and_drain(settings, store, registry, filename="rome.md", content=ROME_MD)
    assert resource.status.value == "ready"
    assert engine.list_knowledge_objects() == []


# ----------------------------------------------------------------------
# Extractor helpers / provider factory
# ----------------------------------------------------------------------


def test_batch_chunks_respects_budget():
    chunks = [
        ResourceChunk(id=str(i), resource_id="r", ordinal=i, text="x" * 400) for i in range(10)
    ]
    batches = batch_chunks(chunks, budget_chars=1000)
    assert [len(b) for b in batches] == [2, 2, 2, 2, 2]
    assert [c.ordinal for b in batches for c in b] == list(range(10))


def test_make_provider(settings):
    assert make_provider(settings) is None
    with_key = settings.model_copy(update={"anthropic_api_key": "sk-test"})
    assert isinstance(make_provider(with_key), AnthropicProvider)


# ----------------------------------------------------------------------
# API level (fake provider injected)
# ----------------------------------------------------------------------


def test_knowledge_api_end_to_end(tmp_path):
    settings = Settings(
        _env_file=None,
        data_dir=tmp_path / "data",
        worker_poll_interval=0.02,
        anthropic_api_key=None,
    )
    app = create_app(settings=settings, provider=FakeProvider(), embedder=FakeEmbedder())
    with TestClient(app) as client:
        resource = client.post(
            "/api/resources/upload", files={"file": ("rome.md", ROME_MD)}
        ).json()["resource"]

        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            current = client.get(f"/api/resources/{resource['id']}").json()
            if current["status"] in ("ready", "failed"):
                break
            time.sleep(0.02)
        assert current["status"] == "ready", current["error"]

        objects = client.get("/api/knowledge").json()
        assert {o["name"] for o in objects} == {"Rome", "Roman Republic", "Summary of rome"}

        rome = client.get("/api/knowledge", params={"q": "Rome", "type": "place"}).json()[0]
        detail = client.get(f"/api/knowledge/{rome['id']}").json()
        assert detail["provenance"][0]["quote"] == "Rome was founded in 753 BC"
        assert len(detail["relationships"]) == 1

        history = client.get(f"/api/knowledge/{rome['id']}/history").json()
        assert history[0]["operation"] == "created"
