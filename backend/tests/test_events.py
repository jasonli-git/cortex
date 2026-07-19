"""Tests for the durable job queue, pipeline registry, and worker."""

import pytest

from pks.config import Settings
from pks.core import KnowledgeEngine
from pks.core.store import SqliteStore
from pks.events import JobQueue, JobStatus, PipelineRegistry, Worker


@pytest.fixture
def settings(tmp_path):
    return Settings(_env_file=None, data_dir=tmp_path / "data")


@pytest.fixture
def store(settings):
    store = SqliteStore(settings.db_path)
    yield store
    store.close()


@pytest.fixture
def queue(store):
    return JobQueue(store)


# ----------------------------------------------------------------------
# Queue
# ----------------------------------------------------------------------


def test_enqueue_claim_done_lifecycle(queue):
    job = queue.enqueue("parse", {"resource_id": "r1"})
    assert job.status is JobStatus.QUEUED

    claimed = queue.claim_next()
    assert claimed.id == job.id
    assert claimed.status is JobStatus.RUNNING
    assert claimed.attempts == 1
    assert queue.claim_next() is None  # nothing else queued

    queue.mark_done(job.id)
    assert queue.get(job.id).status is JobStatus.DONE


def test_claim_is_fifo(queue):
    first = queue.enqueue("parse", {"resource_id": "a"})
    second = queue.enqueue("parse", {"resource_id": "b"})
    assert queue.claim_next().id == first.id
    assert queue.claim_next().id == second.id


def test_list_for_resource(queue):
    queue.enqueue("parse", {"resource_id": "target"})
    queue.enqueue("chunk", {"resource_id": "target"})
    queue.enqueue("parse", {"resource_id": "other"})
    jobs = queue.list_for_resource("target")
    assert [j.type for j in jobs] == ["parse", "chunk"]


# ----------------------------------------------------------------------
# Registry
# ----------------------------------------------------------------------


def test_publish_enqueues_only_subscribed_stages(queue):
    registry = PipelineRegistry()
    registry.register("stage_a", "some.event", lambda ctx, payload: None)
    registry.register("stage_b", "some.event", lambda ctx, payload: None)
    registry.register("stage_c", "other.event", lambda ctx, payload: None)

    jobs = registry.publish(queue, "some.event", {"x": 1})
    assert {j.type for j in jobs} == {"stage_a", "stage_b"}
    assert all(j.payload == {"x": 1} for j in jobs)


def test_duplicate_stage_name_rejected():
    registry = PipelineRegistry()
    registry.register("stage_a", "some.event", lambda ctx, payload: None)
    with pytest.raises(ValueError):
        registry.register("stage_a", "other.event", lambda ctx, payload: None)


# ----------------------------------------------------------------------
# Worker
# ----------------------------------------------------------------------


def test_worker_chains_stages_via_events(settings, store, queue):
    seen: list[str] = []
    registry = PipelineRegistry()

    @registry.stage("first", on="start.event")
    def first(ctx, payload):
        seen.append("first")
        ctx.emit("mid.event", payload)

    @registry.stage("second", on="mid.event")
    def second(ctx, payload):
        seen.append("second")

    registry.publish(queue, "start.event", {})
    worker = Worker(settings, registry)
    executed = worker.drain()
    worker.close()

    assert executed == 2
    assert seen == ["first", "second"]
    assert all(j.status is JobStatus.DONE for j in queue.list())


def test_worker_retries_then_succeeds(settings, queue):
    calls = {"n": 0}
    registry = PipelineRegistry()

    @registry.stage("flaky", on="go")
    def flaky(ctx, payload):
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("transient")

    registry.publish(queue, "go", {})
    worker = Worker(settings, registry)
    worker.drain()
    worker.close()

    job = queue.list()[0]
    assert job.status is JobStatus.DONE
    assert job.attempts == 2


def test_worker_fails_job_and_resource_after_max_attempts(settings, store, queue):
    engine = KnowledgeEngine(store)
    resource = engine.register_resource(type="text", title="Doomed")

    registry = PipelineRegistry()

    @registry.stage("broken", on="go")
    def broken(ctx, payload):
        raise RuntimeError("permanent")

    registry.publish(queue, "go", {"resource_id": resource.id})
    worker = Worker(settings, registry)
    worker.drain()
    worker.close()

    job = queue.list()[0]
    assert job.status is JobStatus.FAILED
    assert job.attempts == job.max_attempts
    assert "permanent" in job.error

    failed = engine.get_resource(resource.id)
    assert failed.status.value == "failed"
    assert "permanent" in failed.error


def test_worker_fails_unknown_stage(settings, queue):
    queue.enqueue("no_such_stage", {})
    worker = Worker(settings, PipelineRegistry())
    worker.drain()
    worker.close()

    job = queue.list()[0]
    assert job.status is JobStatus.FAILED
    assert "no_such_stage" in job.error
