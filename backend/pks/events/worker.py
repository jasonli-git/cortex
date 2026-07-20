"""Job worker: claims queued jobs and executes their pipeline stages.

The worker owns its own database connection (SQLite connections are not shared
across threads; WAL mode lets the worker and API operate concurrently). A
stage failure is retried up to the job's max_attempts; a final failure marks
the job — and, when the payload names one, the resource — as failed.
"""

from __future__ import annotations

import contextlib
import logging
import threading

from pks.config import Settings
from pks.core.engine import KnowledgeEngine
from pks.core.errors import NotFoundError
from pks.core.store.sqlite import SqliteStore
from pks.events.bus import PipelineRegistry, StageContext
from pks.events.queue import JobQueue

logger = logging.getLogger(__name__)


class Worker:
    """Executes jobs synchronously. Create and use within a single thread."""

    def __init__(self, settings: Settings, registry: PipelineRegistry):
        self._settings = settings
        self._registry = registry
        self._store: SqliteStore | None = None

    def _ensure_open(self) -> tuple[KnowledgeEngine, JobQueue]:
        if self._store is None:
            self._store = SqliteStore(self._settings.db_path)
            self._engine = KnowledgeEngine(self._store)
            self._queue = JobQueue(self._store)
        return self._engine, self._queue

    def run_once(self) -> bool:
        """Claim and execute one job. Returns False when the queue is empty."""
        engine, queue = self._ensure_open()
        job = queue.claim_next()
        if job is None:
            return False

        try:
            handler = self._registry.get(job.type)
        except LookupError as exc:
            logger.error("job %s: %s", job.id, exc)
            queue.mark_failed(job.id, str(exc))
            self._fail_resource(engine, job.payload, str(exc))
            return True

        ctx = StageContext(
            engine=engine,
            store=self._store,
            settings=self._settings,
            emit=lambda event, payload: self._registry.publish(queue, event, payload),
        )
        try:
            handler(ctx, job.payload)
        except Exception as exc:
            logger.exception("stage %r failed (attempt %d)", job.type, job.attempts)
            if job.attempts >= job.max_attempts:
                queue.mark_failed(job.id, str(exc))
                self._fail_resource(engine, job.payload, f"stage {job.type!r}: {exc}")
            else:
                queue.requeue(job.id, str(exc))
        else:
            queue.mark_done(job.id)
        return True

    def drain(self) -> int:
        """Run until the queue is empty. Returns the number of jobs executed."""
        count = 0
        while self.run_once():
            count += 1
        return count

    def close(self) -> None:
        if self._store is not None:
            self._store.close()
            self._store = None

    @staticmethod
    def _fail_resource(engine: KnowledgeEngine, payload: dict, error: str) -> None:
        resource_id = payload.get("resource_id")
        if not isinstance(resource_id, str):
            return
        with contextlib.suppress(NotFoundError):
            engine.set_resource_status(resource_id, "failed", error=error)


class WorkerThread:
    """Runs a Worker in a daemon thread, polling until stopped."""

    def __init__(self, settings: Settings, registry: PipelineRegistry):
        self._worker = Worker(settings, registry)
        self._poll_interval = settings.worker_poll_interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="pks-worker", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=10)

    def _run(self) -> None:
        try:
            while not self._stop.is_set():
                if not self._worker.run_once():
                    self._stop.wait(self._poll_interval)
        finally:
            self._worker.close()
