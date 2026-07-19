"""Resource endpoints: upload, notes, listing, and pipeline status."""

from typing import Annotated

from fastapi import APIRouter, Form, UploadFile
from pydantic import BaseModel

from pks.api.deps import EngineDep, QueueDep, RegistryDep, SettingsDep
from pks.core.models import Resource, ResourceChunk, ResourceRelationship
from pks.events.models import Job
from pks.ingestion import intake

router = APIRouter(prefix="/api/resources", tags=["resources"])


class IngestResult(BaseModel):
    resource: Resource
    created: bool  # False: identical content already ingested


class NoteIn(BaseModel):
    title: str
    content: str
    relationship: ResourceRelationship = ResourceRelationship.REFERENCE


class ResourceStatusOut(BaseModel):
    resource: Resource
    jobs: list[Job]


@router.post("/upload", response_model=IngestResult)
async def upload_resource(
    file: UploadFile,
    engine: EngineDep,
    settings: SettingsDep,
    registry: RegistryDep,
    queue: QueueDep,
    relationship: Annotated[ResourceRelationship, Form()] = ResourceRelationship.REFERENCE,
) -> IngestResult:
    content = await file.read()
    resource, created = intake.save_upload(
        engine,
        settings,
        registry,
        queue,
        filename=file.filename or "upload",
        content=content,
        relationship=relationship,
    )
    return IngestResult(resource=resource, created=created)


@router.post("/notes", response_model=IngestResult)
def create_note(
    note: NoteIn,
    engine: EngineDep,
    settings: SettingsDep,
    registry: RegistryDep,
    queue: QueueDep,
) -> IngestResult:
    resource, created = intake.create_note(
        engine,
        settings,
        registry,
        queue,
        title=note.title,
        content=note.content,
        relationship=note.relationship,
    )
    return IngestResult(resource=resource, created=created)


@router.get("", response_model=list[Resource])
def list_resources(engine: EngineDep) -> list[Resource]:
    return engine.list_resources()


@router.get("/{resource_id}", response_model=Resource)
def get_resource(resource_id: str, engine: EngineDep) -> Resource:
    return engine.get_resource(resource_id)


@router.get("/{resource_id}/status", response_model=ResourceStatusOut)
def get_resource_status(resource_id: str, engine: EngineDep, queue: QueueDep) -> ResourceStatusOut:
    """The resource plus every pipeline job that has touched it."""
    resource = engine.get_resource(resource_id)
    return ResourceStatusOut(resource=resource, jobs=queue.list_for_resource(resource_id))


@router.get("/{resource_id}/chunks", response_model=list[ResourceChunk])
def get_resource_chunks(resource_id: str, engine: EngineDep) -> list[ResourceChunk]:
    return engine.get_chunks(resource_id)
