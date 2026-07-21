"""Resource endpoints: upload, notes, listing, and pipeline status."""

from typing import Annotated

from fastapi import APIRouter, Form, UploadFile
from pydantic import BaseModel

from pks.api.deps import EngineDep, QueueDep, RegistryDep, SettingsDep
from pks.core.errors import ValidationError
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
    workspace_id: str | None = None  # reference the note from this workspace


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
    workspace_id: Annotated[str | None, Form()] = None,
) -> IngestResult:
    if workspace_id is not None:
        engine.get_workspace(workspace_id)
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
    if workspace_id is not None:
        engine.attach_to_workspace(workspace_id, "resource", resource.id)
    return IngestResult(resource=resource, created=created)


@router.post("/notes", response_model=IngestResult)
def create_note(
    note: NoteIn,
    engine: EngineDep,
    settings: SettingsDep,
    registry: RegistryDep,
    queue: QueueDep,
) -> IngestResult:
    if note.workspace_id is not None:
        engine.get_workspace(note.workspace_id)
    resource, created = intake.create_note(
        engine,
        settings,
        registry,
        queue,
        title=note.title,
        content=note.content,
        relationship=note.relationship,
    )
    if note.workspace_id is not None:
        engine.attach_to_workspace(note.workspace_id, "resource", resource.id)
    return IngestResult(resource=resource, created=created)


@router.post("/{resource_id}/reprocess", response_model=Resource)
def reprocess_resource(
    resource_id: str,
    engine: EngineDep,
    settings: SettingsDep,
    registry: RegistryDep,
    queue: QueueDep,
) -> Resource:
    """Re-run the full pipeline on a resource from its stored original.

    Chunks and indexes are rebuilt; knowledge objects are enriched in place
    (extraction and provenance are idempotent), so nothing accumulated is lost.
    """
    resource = engine.get_resource(resource_id)
    if resource.status in ("pending", "processing"):
        raise ValidationError("resource is already being processed")
    if not resource.path or not (settings.resources_dir / resource.path).exists():
        raise ValidationError("original file is missing; re-upload the resource instead")
    resource = engine.set_resource_status(resource_id, "pending")
    registry.publish(queue, "resource.uploaded", {"resource_id": resource_id})
    return resource


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
