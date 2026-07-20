"""Pipeline registry: which stages run in response to which events.

Stages subscribe to event types; publishing an event enqueues one durable job
per subscribed stage. Stage handlers receive a StageContext and may emit
follow-up events, chaining the pipeline.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from pks.core.engine import KnowledgeEngine
from pks.core.store.sqlite import SqliteStore
from pks.events.models import Job
from pks.events.queue import JobQueue


@dataclass
class StageContext:
    """What a pipeline stage gets to work with."""

    engine: KnowledgeEngine
    store: SqliteStore  # for module-local indexes (embeddings, FTS) on the worker's connection
    settings: object  # pks.config.Settings; typed loosely to keep events config-free
    emit: Callable[[str, dict], None]  # publish a follow-up event


StageHandler = Callable[[StageContext, dict], None]


class PipelineRegistry:
    def __init__(self) -> None:
        self._stages: dict[str, tuple[str, StageHandler]] = {}

    def stage(self, name: str, *, on: str) -> Callable[[StageHandler], StageHandler]:
        """Decorator: register a stage handler triggered by event type `on`."""

        def decorator(fn: StageHandler) -> StageHandler:
            self.register(name, on, fn)
            return fn

        return decorator

    def register(self, name: str, on: str, fn: StageHandler) -> None:
        if name in self._stages:
            raise ValueError(f"stage {name!r} is already registered")
        self._stages[name] = (on, fn)

    def get(self, name: str) -> StageHandler:
        if name not in self._stages:
            raise LookupError(f"no stage registered with name {name!r}")
        return self._stages[name][1]

    def stages_for(self, event_type: str) -> list[str]:
        return [name for name, (on, _) in self._stages.items() if on == event_type]

    def publish(self, queue: JobQueue, event_type: str, payload: dict) -> list[Job]:
        """Enqueue one job per stage subscribed to this event."""
        return [queue.enqueue(name, payload) for name in self.stages_for(event_type)]
