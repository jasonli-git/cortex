"""Tests for embeddings, FTS, and hybrid search (fake embedder — no models)."""

import time

import pytest
from fastapi.testclient import TestClient

from pks.api.app import create_app
from pks.config import Settings
from pks.core import KnowledgeEngine
from pks.core.store import SqliteStore
from pks.embeddings.index import EmbeddingIndex
from pks.events import JobQueue, Worker
from pks.ingestion import intake
from pks.pipeline import build_pipeline
from pks.search.fts import FtsIndex, fts_query
from pks.search.service import SearchService, rrf_fuse
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


@pytest.fixture
def embedder():
    return FakeEmbedder()


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


# ----------------------------------------------------------------------
# Building blocks
# ----------------------------------------------------------------------


def test_rrf_fuse_rewards_agreement():
    fused = rrf_fuse([["a", "b", "c"], ["b", "a"]])
    # 'a' and 'b' both appear in both rankings and beat 'c'.
    assert {fused[0][0], fused[1][0]} == {"a", "b"}
    assert fused[2][0] == "c"


def test_fts_query_sanitizes():
    assert fts_query("roman-republic!") == '"roman" OR "republic"'
    assert fts_query("...") is None


def test_embedding_index_similarity_and_model_isolation(store, embedder):
    index = EmbeddingIndex(store)
    for owner_id, text in [("c1", "roman republic senate"), ("c2", "carthage africa trade")]:
        index.upsert(
            "chunk", owner_id, embedder.embed_query(text), model="fake-embedder", text_hash="h"
        )
    # A vector from a different model must never be returned.
    index.upsert("chunk", "c3", embedder.embed_query("roman"), model="other-model", text_hash="h")

    hits = index.similar("chunk", embedder.embed_query("roman senate"), model="fake-embedder")
    assert [owner_id for owner_id, _ in hits] == ["c1", "c2"]


def test_fts_index_roundtrip(store, engine):
    resource = engine.register_resource(type="text", title="Doc")
    chunks = engine.set_chunks(resource.id, [(0, "the roman senate met", None, None)])
    fts = FtsIndex(store)
    fts.replace_resource_chunks(resource.id, chunks)

    assert fts.search_chunks("senate") == [chunks[0].id]
    # Replacement removes the old rows.
    new_chunks = engine.set_chunks(resource.id, [(0, "different text now", None, None)])
    fts.replace_resource_chunks(resource.id, new_chunks)
    assert fts.search_chunks("senate") == []


# ----------------------------------------------------------------------
# Pipeline indexing + hybrid search
# ----------------------------------------------------------------------


def test_search_finds_relevant_chunks_and_knowledge(settings, store, engine, embedder):
    registry = build_pipeline(FakeProvider(), embedder)
    ingest(settings, store, registry, "rome.md", ROME_MD)
    ingest(settings, store, registry, "carthage.txt", CARTHAGE_TXT)

    service = SearchService(store, embedder)
    result = service.search("roman republic")

    assert result.chunks, "expected chunk hits"
    assert "Roman Republic" in result.chunks[0].chunk.text
    assert result.chunks[0].resource_title == "rome"
    assert result.knowledge[0].object.name == "Roman Republic"

    carthage = service.search("Phoenician city in Africa")
    assert "Carthage" in carthage.chunks[0].chunk.text


def test_search_skips_stale_knowledge_entries(settings, store, engine, embedder):
    registry = build_pipeline(FakeProvider(), embedder)
    ingest(settings, store, registry, "rome.md", ROME_MD)

    service = SearchService(store, embedder)
    before = {hit.object.name for hit in service.search("Roman Republic").knowledge}
    assert "Roman Republic" in before

    republic = engine.list_knowledge_objects(type="concept", name_contains="Roman Republic")[0]
    engine.delete_knowledge_object(republic.id)

    after = {hit.object.name for hit in service.search("Roman Republic").knowledge}
    assert "Roman Republic" not in after  # stale index entry skipped, no error


def test_reindex_skips_unchanged_knowledge_objects(settings, store, embedder):
    registry = build_pipeline(FakeProvider(), embedder)
    ingest(settings, store, registry, "rome.md", ROME_MD)
    ko_texts_first = [t for t in embedder.embedded_texts if "Rome" in t or "Republic" in t]
    assert ko_texts_first, "expected knowledge objects to be embedded on first ingest"

    embedder.embedded_texts.clear()
    # Same entities re-extracted → knowledge unchanged → no re-embedding of KOs.
    ingest(settings, store, registry, "rome2.txt", b"Rome and the Roman Republic, again.")
    reembedded_kos = [
        t for t in embedder.embedded_texts if t.startswith(("Rome\n", "Roman Republic\n"))
    ]
    assert reembedded_kos == []


def test_empty_query_returns_nothing(store, embedder):
    service = SearchService(store, embedder)
    result = service.search("   ")
    assert result.knowledge == [] and result.chunks == []


# ----------------------------------------------------------------------
# API
# ----------------------------------------------------------------------


def test_search_api_end_to_end(tmp_path):
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

        body = client.get("/api/search", params={"q": "roman republic"}).json()
        assert body["query"] == "roman republic"
        assert body["knowledge"][0]["object"]["name"] == "Roman Republic"
        assert "Roman Republic" in body["chunks"][0]["chunk"]["text"]
        assert body["chunks"][0]["resource_title"] == "rome"

        assert client.get("/api/search", params={"q": ""}).status_code == 422
