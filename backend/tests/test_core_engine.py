"""Unit tests for the Core Knowledge Engine (Milestone 1)."""

import pytest

from pks.core import KnowledgeEngine
from pks.core.errors import NotFoundError, ValidationError
from pks.core.models import (
    KnowledgeObjectType,
    ResourceStatus,
    VersionOperation,
)
from pks.core.store import SqliteStore


@pytest.fixture
def store(tmp_path):
    store = SqliteStore(tmp_path / "test.db")
    yield store
    store.close()


@pytest.fixture
def engine(store):
    return KnowledgeEngine(store)


@pytest.fixture
def resource(engine):
    return engine.register_resource(type="text", title="A History of Rome")


# ----------------------------------------------------------------------
# Migrations
# ----------------------------------------------------------------------


def test_migrations_are_idempotent(tmp_path):
    db_path = tmp_path / "test.db"
    first = SqliteStore(db_path)
    first.close()
    # Re-opening re-runs the migration check; nothing new should apply.
    second = SqliteStore(db_path)
    tables = {
        row["name"]
        for row in second._conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    second.close()
    assert {
        "resources",
        "resource_chunks",
        "knowledge_objects",
        "ko_versions",
        "relationships",
        "provenance",
        "schema_migrations",
    } <= tables


# ----------------------------------------------------------------------
# Knowledge objects
# ----------------------------------------------------------------------


def test_create_and_get_knowledge_object(engine):
    ko = engine.create_knowledge_object(
        type="concept",
        name="Roman Republic",
        description="The era of classical Roman civilization before the Empire.",
        aliases=["Res publica Romana"],
        metadata={"period": "509 BC - 27 BC"},
    )
    fetched = engine.get_knowledge_object(ko.id)
    assert fetched == ko
    assert fetched.type is KnowledgeObjectType.CONCEPT
    assert fetched.version == 1
    assert fetched.aliases == ["Res publica Romana"]
    assert fetched.metadata["period"] == "509 BC - 27 BC"


def test_create_rejects_empty_name(engine):
    with pytest.raises(ValidationError):
        engine.create_knowledge_object(type="concept", name="   ")


def test_get_missing_knowledge_object_raises(engine):
    with pytest.raises(NotFoundError):
        engine.get_knowledge_object("nope")


def test_update_bumps_version_and_records_history(engine):
    ko = engine.create_knowledge_object(type="person", name="Julius Caesar")
    updated = engine.update_knowledge_object(
        ko.id, description="Roman general and statesman.", changed_by="extraction"
    )
    assert updated.version == 2
    assert updated.description == "Roman general and statesman."
    assert updated.created_at == ko.created_at

    history = engine.get_history(ko.id)
    assert [(v.version, v.operation) for v in history] == [
        (1, VersionOperation.CREATED),
        (2, VersionOperation.UPDATED),
    ]
    assert history[0].snapshot["description"] == ""
    assert history[1].snapshot["description"] == "Roman general and statesman."
    assert history[1].changed_by == "extraction"


def test_update_rejects_unknown_and_empty_changes(engine):
    ko = engine.create_knowledge_object(type="concept", name="Aqueducts")
    with pytest.raises(ValidationError):
        engine.update_knowledge_object(ko.id, type="event")
    with pytest.raises(ValidationError):
        engine.update_knowledge_object(ko.id)


def test_delete_keeps_history(engine):
    ko = engine.create_knowledge_object(type="concept", name="Latifundia")
    engine.delete_knowledge_object(ko.id)

    with pytest.raises(NotFoundError):
        engine.get_knowledge_object(ko.id)
    operations = [v.operation for v in engine.get_history(ko.id)]
    assert operations == [VersionOperation.CREATED, VersionOperation.DELETED]


def test_list_filters(engine):
    engine.create_knowledge_object(type="person", name="Cicero")
    engine.create_knowledge_object(type="concept", name="Rhetoric")
    engine.create_knowledge_object(
        type="person", name="Octavian", aliases=["Augustus", "Gaius Octavius"]
    )

    assert {ko.name for ko in engine.list_knowledge_objects(type="person")} == {
        "Cicero",
        "Octavian",
    }
    # Matches by name…
    assert [ko.name for ko in engine.list_knowledge_objects(name_contains="rhet")] == ["Rhetoric"]
    # …and by alias.
    assert [ko.name for ko in engine.list_knowledge_objects(name_contains="Augustus")] == [
        "Octavian"
    ]


# ----------------------------------------------------------------------
# Relationships
# ----------------------------------------------------------------------


def test_relate_and_neighbors(engine):
    caesar = engine.create_knowledge_object(type="person", name="Julius Caesar")
    rubicon = engine.create_knowledge_object(type="event", name="Crossing the Rubicon")
    rome = engine.create_knowledge_object(type="place", name="Rome")

    engine.relate(caesar.id, rubicon.id, "participated_in", created_by="extraction")
    engine.relate(rubicon.id, rome.id, "located_in", created_by="extraction")

    assert len(engine.get_relationships(rubicon.id)) == 2
    assert {n.name for n in engine.get_neighbors(rubicon.id)} == {"Julius Caesar", "Rome"}
    assert {n.name for n in engine.get_neighbors(caesar.id)} == {"Crossing the Rubicon"}


def test_relate_is_idempotent_and_refreshes(engine):
    a = engine.create_knowledge_object(type="concept", name="Senate")
    b = engine.create_knowledge_object(type="concept", name="Republic")

    first = engine.relate(a.id, b.id, "part_of", confidence=0.6)
    second = engine.relate(a.id, b.id, "part_of", confidence=0.9)

    assert second.id == first.id
    assert second.confidence == 0.9
    assert len(engine.get_relationships(a.id)) == 1


def test_relate_validation(engine):
    a = engine.create_knowledge_object(type="concept", name="Senate")
    b = engine.create_knowledge_object(type="concept", name="Republic")

    with pytest.raises(ValidationError):
        engine.relate(a.id, a.id, "related_to")
    with pytest.raises(ValidationError):
        engine.relate(a.id, b.id, "  ")
    with pytest.raises(ValidationError):
        engine.relate(a.id, b.id, "related_to", confidence=1.5)
    with pytest.raises(NotFoundError):
        engine.relate(a.id, "missing", "related_to")


def test_unrelate(engine):
    a = engine.create_knowledge_object(type="concept", name="Senate")
    b = engine.create_knowledge_object(type="concept", name="Republic")
    rel = engine.relate(a.id, b.id, "part_of")

    engine.unrelate(rel.id)
    assert engine.get_relationships(a.id) == []
    with pytest.raises(NotFoundError):
        engine.unrelate(rel.id)


def test_deleting_ko_cascades_relationships(engine):
    a = engine.create_knowledge_object(type="concept", name="Senate")
    b = engine.create_knowledge_object(type="concept", name="Republic")
    rel = engine.relate(a.id, b.id, "part_of")

    engine.delete_knowledge_object(b.id)
    with pytest.raises(NotFoundError):
        engine.get_relationship(rel.id)
    assert engine.get_relationships(a.id) == []


# ----------------------------------------------------------------------
# Provenance
# ----------------------------------------------------------------------


def test_provenance_round_trip(engine, resource):
    ko = engine.create_knowledge_object(type="concept", name="Punic Wars")
    chunks = engine.set_chunks(
        resource.id, [(0, "The Punic Wars were fought between Rome and Carthage.", "Ch 1", 12)]
    )

    prov = engine.add_provenance(
        knowledge_object_id=ko.id,
        resource_id=resource.id,
        chunk_id=chunks[0].id,
        quote="fought between Rome and Carthage",
    )
    stored = engine.get_provenance(knowledge_object_id=ko.id)
    assert stored == [prov]
    assert stored[0].chunk_id == chunks[0].id


def test_provenance_for_relationship(engine, resource):
    a = engine.create_knowledge_object(type="person", name="Hannibal")
    b = engine.create_knowledge_object(type="event", name="Battle of Cannae")
    rel = engine.relate(a.id, b.id, "participated_in")

    engine.add_provenance(relationship_id=rel.id, resource_id=resource.id)
    assert len(engine.get_provenance(relationship_id=rel.id)) == 1


def test_provenance_validation(engine, resource):
    ko = engine.create_knowledge_object(type="concept", name="Punic Wars")
    other = engine.register_resource(type="text", title="Unrelated")
    other_chunks = engine.set_chunks(other.id, [(0, "text", None, None)])

    with pytest.raises(ValidationError):
        engine.add_provenance(resource_id=resource.id)  # no target
    with pytest.raises(NotFoundError):
        engine.add_provenance(knowledge_object_id=ko.id, resource_id="missing")
    with pytest.raises(ValidationError):
        # Chunk belongs to a different resource.
        engine.add_provenance(
            knowledge_object_id=ko.id,
            resource_id=resource.id,
            chunk_id=other_chunks[0].id,
        )


def test_deleting_ko_cascades_provenance(engine, resource):
    ko = engine.create_knowledge_object(type="concept", name="Punic Wars")
    engine.add_provenance(knowledge_object_id=ko.id, resource_id=resource.id)

    engine.delete_knowledge_object(ko.id)
    assert engine.get_provenance(knowledge_object_id=ko.id) == []


# ----------------------------------------------------------------------
# Resources
# ----------------------------------------------------------------------


def test_register_resource_defaults(engine):
    resource = engine.register_resource(type="pdf", title="  My Book  ")
    assert resource.title == "My Book"
    assert resource.status is ResourceStatus.PENDING
    assert resource.relationship.value == "reference"
    assert engine.list_resources() == [resource]


def test_resource_status_transitions(engine, resource):
    processing = engine.set_resource_status(resource.id, "processing")
    assert processing.status is ResourceStatus.PROCESSING

    failed = engine.set_resource_status(resource.id, "failed", error="parser exploded")
    assert failed.status is ResourceStatus.FAILED
    assert failed.error == "parser exploded"

    ready = engine.set_resource_status(resource.id, "ready")
    assert ready.status is ResourceStatus.READY
    assert ready.error is None


def test_set_chunks_replaces(engine, resource):
    engine.set_chunks(resource.id, [(0, "old text", None, None)])
    engine.set_chunks(resource.id, [(0, "new text", "Ch 1", 2), (1, "more", "Ch 1 > §2", 1)])

    chunks = engine.get_chunks(resource.id)
    assert [(c.ordinal, c.text, c.structure_path) for c in chunks] == [
        (0, "new text", "Ch 1"),
        (1, "more", "Ch 1 > §2"),
    ]


def test_chunks_require_existing_resource(engine):
    with pytest.raises(NotFoundError):
        engine.set_chunks("missing", [(0, "text", None, None)])
