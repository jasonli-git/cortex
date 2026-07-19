"""FastAPI dependencies.

Each request gets its own store (SQLite connections must not cross threads;
opening one is cheap). Settings and the pipeline registry live on app.state,
set by the app factory.
"""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request

from pks.config import Settings
from pks.core.engine import KnowledgeEngine
from pks.core.store.sqlite import SqliteStore
from pks.events.bus import PipelineRegistry
from pks.events.queue import JobQueue


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_registry(request: Request) -> PipelineRegistry:
    return request.app.state.registry


def get_store(request: Request) -> Iterator[SqliteStore]:
    store = SqliteStore(request.app.state.settings.db_path)
    try:
        yield store
    finally:
        store.close()


def get_engine(store: Annotated[SqliteStore, Depends(get_store)]) -> KnowledgeEngine:
    return KnowledgeEngine(store)


def get_queue(store: Annotated[SqliteStore, Depends(get_store)]) -> JobQueue:
    return JobQueue(store)


SettingsDep = Annotated[Settings, Depends(get_settings)]
RegistryDep = Annotated[PipelineRegistry, Depends(get_registry)]
EngineDep = Annotated[KnowledgeEngine, Depends(get_engine)]
QueueDep = Annotated[JobQueue, Depends(get_queue)]
