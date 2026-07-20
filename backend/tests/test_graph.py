"""Tests for merging, dedup, and graph traversal (Milestone 5)."""

import pytest

from pks.config import Settings
from pks.core import KnowledgeEngine
from pks.core.errors import NotFoundError, ValidationError
from pks.core.models import VersionOperation
from pks.core.store import SqliteStore
from pks.embeddings.index import EmbeddingIndex
from pks.events import JobQueue, Worker
from pks.ingestion import intake
from pks.pipeline import build_pipeline
from pks.search.service import SearchService
from tests.fakes import ROME_MD, FakeEmbedder, FakeProvider


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
def resource(engine):
    return engine.register_resource(type="text", title="Source doc")


# ----------------------------------------------------------------------
# Engine merge
# ----------------------------------------------------------------------


def test_merge_transfers_everything(engine, resource):
    usa = engine.create_knowledge_object(
        type="place", name="USA", description="A federal republic in North America."
    )
    dup = engine.create_knowledge_object(
        type="place",
        name="United States",
        aliases=["United States of America"],
        metadata={"iso": "US"},
    )
    canada = engine.create_knowledge_object(type="place", name="Canada")
    engine.relate(dup.id, canada.id, "borders", confidence=0.8)
    engine.add_provenance(knowledge_object_id=dup.id, resource_id=resource.id, quote="the US")

    merged = engine.merge_knowledge_objects(usa.id, dup.id)

    # Names/aliases/metadata absorbed; description kept.
    assert merged.aliases == ["United States", "United States of America"]
    assert merged.description == "A federal republic in North America."
    assert merged.metadata["iso"] == "US"
    assert merged.version == usa.version + 1

    # Relationships re-pointed; provenance transferred.
    rels = engine.get_relationships(merged.id)
    assert [(r.type, r.to_id) for r in rels] == [("borders", canada.id)]
    provs = engine.get_provenance(knowledge_object_id=merged.id)
    assert [p.quote for p in provs] == ["the US"]

    # Source gone, but with its history intact and pointing at the target.
    with pytest.raises(NotFoundError):
        engine.get_knowledge_object(dup.id)
    history = engine.get_history(dup.id)
    assert history[-1].operation is VersionOperation.DELETED
    assert history[-1].snapshot["metadata"]["merged_into"] == usa.id
    assert engine.get_history(usa.id)[-1].operation is VersionOperation.UPDATED


def test_merge_keeps_higher_confidence_on_conflicting_relationships(engine):
    a = engine.create_knowledge_object(type="person", name="Caesar")
    dup = engine.create_knowledge_object(type="person", name="Julius Caesar")
    rome = engine.create_knowledge_object(type="place", name="Rome")
    engine.relate(a.id, rome.id, "lived_in", confidence=0.5)
    engine.relate(dup.id, rome.id, "lived_in", confidence=0.9)

    engine.merge_knowledge_objects(a.id, dup.id)

    [rel] = engine.get_relationships(a.id)
    assert rel.confidence == 0.9


def test_merge_drops_relationship_between_the_two(engine):
    a = engine.create_knowledge_object(type="concept", name="A")
    b = engine.create_knowledge_object(type="concept", name="B")
    engine.relate(a.id, b.id, "related_to")

    merged = engine.merge_knowledge_objects(a.id, b.id)
    assert engine.get_relationships(merged.id) == []


def test_merge_validation(engine):
    concept = engine.create_knowledge_object(type="concept", name="Thing")
    person = engine.create_knowledge_object(type="person", name="Someone")
    with pytest.raises(ValidationError):
        engine.merge_knowledge_objects(concept.id, concept.id)
    with pytest.raises(ValidationError):
        engine.merge_knowledge_objects(concept.id, person.id)


def test_add_provenance_is_idempotent(engine, resource):
    ko = engine.create_knowledge_object(type="concept", name="Thing")
    first = engine.add_provenance(
        knowledge_object_id=ko.id, resource_id=resource.id, quote="a quote"
    )
    second = engine.add_provenance(
        knowledge_object_id=ko.id, resource_id=resource.id, quote="a quote"
    )
    assert second.id == first.id
    assert len(engine.get_provenance(knowledge_object_id=ko.id)) == 1


# ----------------------------------------------------------------------
# Graph traversal
# ----------------------------------------------------------------------


def test_neighborhood_depth(engine):
    a = engine.create_knowledge_object(type="concept", name="A")
    b = engine.create_knowledge_object(type="concept", name="B")
    c = engine.create_knowledge_object(type="concept", name="C")
    engine.relate(a.id, b.id, "related_to")
    engine.relate(b.id, c.id, "related_to")

    nodes, edges = engine.get_neighborhood(a.id, depth=1)
    assert {n.name for n in nodes} == {"A", "B"}
    assert len(edges) == 1

    nodes, edges = engine.get_neighborhood(a.id, depth=2)
    assert {n.name for n in nodes} == {"A", "B", "C"}
    assert len(edges) == 2


def test_whole_graph(engine):
    a = engine.create_knowledge_object(type="concept", name="A")
    b = engine.create_knowledge_object(type="concept", name="B")
    engine.create_knowledge_object(type="concept", name="Isolated")
    engine.relate(a.id, b.id, "related_to")

    nodes, edges = engine.get_graph()
    assert {n.name for n in nodes} == {"A", "B", "Isolated"}
    assert len(edges) == 1


# ----------------------------------------------------------------------
# Dedup stage (pipeline)
# ----------------------------------------------------------------------

# Same description words → high fake-embedder similarity despite different names.
USA_DOC = b"The USA spans North America with fifty states from coast to coast."
DUP_DOC = b"The United States spans North America with fifty states from coast to coast."

USA_EXTRACTION = {
    "entities": [
        {
            "type": "place",
            "name": "USA",
            "description": "Country spanning North America with fifty states coast to coast.",
            "aliases": [],
            "quote": "The USA spans North America",
            "chunk_ordinal": 0,
        }
    ],
    "relations": [],
}

DUP_EXTRACTION = {
    "entities": [
        {
            "type": "place",
            "name": "United States",
            "description": "Country spanning North America with fifty states coast to coast.",
            "aliases": [],
            "quote": "The United States spans North America",
            "chunk_ordinal": 0,
        }
    ],
    "relations": [],
}


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


def test_dedupe_stage_merges_confirmed_duplicates(tmp_path, store, engine):
    settings = Settings(
        _env_file=None,
        data_dir=tmp_path / "data",
        anthropic_api_key=None,
        dedup_similarity_threshold=0.5,  # fake embeddings are word-overlap based
    )
    embedder = FakeEmbedder()
    first = ingest(
        settings,
        store,
        build_pipeline(FakeProvider(extraction=USA_EXTRACTION), embedder),
        "usa.txt",
        USA_DOC,
    )
    confirm = FakeProvider(
        extraction=DUP_EXTRACTION, dedup={"same_entity": True, "reason": "same country"}
    )
    second = ingest(settings, store, build_pipeline(confirm, embedder), "dup.txt", DUP_DOC)

    assert confirm.dedup_prompts, "expected the LLM to be consulted"
    places = engine.list_knowledge_objects(type="place")
    assert len(places) == 1
    merged = places[0]
    assert merged.name == "USA"  # the older object won
    assert "United States" in merged.aliases
    # Evidence from both resources survived the merge.
    provs = engine.get_provenance(knowledge_object_id=merged.id)
    assert {p.resource_id for p in provs} == {first.id, second.id}

    # Search no longer surfaces the merged-away object; target ranks first.
    result = SearchService(store, embedder).search("United States fifty states")
    names = [hit.object.name for hit in result.knowledge]
    assert names[0] == "USA"
    assert "United States" not in names


def test_dedupe_respects_llm_rejection(tmp_path, store, engine):
    settings = Settings(
        _env_file=None,
        data_dir=tmp_path / "data",
        anthropic_api_key=None,
        dedup_similarity_threshold=0.5,
    )
    embedder = FakeEmbedder()
    ingest(
        settings,
        store,
        build_pipeline(FakeProvider(extraction=USA_EXTRACTION), embedder),
        "usa.txt",
        USA_DOC,
    )
    reject = FakeProvider(extraction=DUP_EXTRACTION)  # dedup default: same_entity=False
    ingest(settings, store, build_pipeline(reject, embedder), "dup.txt", DUP_DOC)

    assert reject.dedup_prompts, "expected the LLM to be consulted"
    assert len(engine.list_knowledge_objects(type="place")) == 2  # no merge


def test_relation_to_entity_from_another_resource(settings, store, engine):
    embedder = FakeEmbedder()
    ingest(settings, store, build_pipeline(FakeProvider(), embedder), "rome.md", ROME_MD)

    # A later resource relates a new entity to "Rome", which is not in this
    # batch's entity list — the resolver must find it in the knowledge base.
    extraction = {
        "entities": [
            {
                "type": "person",
                "name": "Cicero",
                "description": "Roman statesman and orator.",
                "aliases": [],
                "quote": "Cicero spoke",
                "chunk_ordinal": 0,
            }
        ],
        "relations": [
            {"from_name": "Cicero", "to_name": "Rome", "type": "lived_in", "confidence": 0.9}
        ],
    }
    ingest(
        settings,
        store,
        build_pipeline(FakeProvider(extraction=extraction), embedder),
        "cicero.txt",
        b"Cicero spoke in the forum.",
    )

    cicero = engine.list_knowledge_objects(type="person", name_contains="Cicero")[0]
    rome = engine.list_knowledge_objects(type="place", name_contains="Rome")[0]
    assert [(r.type, r.to_id) for r in engine.get_relationships(cicero.id)] == [
        ("lived_in", rome.id)
    ]


def test_dedupe_cleans_stale_index_entries(tmp_path, store):
    settings = Settings(
        _env_file=None,
        data_dir=tmp_path / "data",
        anthropic_api_key=None,
        dedup_similarity_threshold=0.5,
    )
    embedder = FakeEmbedder()
    ingest(
        settings,
        store,
        build_pipeline(FakeProvider(extraction=USA_EXTRACTION), embedder),
        "usa.txt",
        USA_DOC,
    )
    confirm = FakeProvider(
        extraction=DUP_EXTRACTION, dedup={"same_entity": True, "reason": "same"}
    )
    ingest(settings, store, build_pipeline(confirm, embedder), "dup.txt", DUP_DOC)

    engine = KnowledgeEngine(store)
    [merged] = engine.list_knowledge_objects(type="place")
    index = EmbeddingIndex(store)
    query = embedder.embed_query("North America fifty states")
    hits = index.similar("knowledge_object", query, model="fake-embedder")
    hit_ids = [owner_id for owner_id, _ in hits]
    assert hit_ids.count(merged.id) == 1
    # No stale vectors: every indexed id still resolves to a live object.
    for hit_id in hit_ids:
        engine.get_knowledge_object(hit_id)
