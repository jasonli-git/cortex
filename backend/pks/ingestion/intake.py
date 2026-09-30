"""Resource intake: accept uploads and notes, store originals, start the pipeline.

Identical content (by SHA-256) maps to the existing resource instead of
creating a duplicate (spec: the system de-duplicates automatically). The
original file always remains available on disk, per the spec.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from pks.config import Settings
from pks.core.engine import KnowledgeEngine
from pks.core.errors import ValidationError
from pks.core.models import Resource, ResourceRelationship, ResourceType
from pks.events.bus import PipelineRegistry
from pks.events.queue import JobQueue

_EXTENSION_TYPES: dict[str, ResourceType] = {
    ".pdf": ResourceType.PDF,
    ".md": ResourceType.MARKDOWN,
    ".markdown": ResourceType.MARKDOWN,
    ".txt": ResourceType.TEXT,
}


def resource_type_for_filename(filename: str) -> ResourceType:
    ext = Path(filename).suffix.lower()
    if ext not in _EXTENSION_TYPES:
        supported = ", ".join(sorted(_EXTENSION_TYPES))
        raise ValidationError(f"unsupported file type {ext or filename!r} (supported: {supported})")
    return _EXTENSION_TYPES[ext]


def save_upload(
    engine: KnowledgeEngine,
    settings: Settings,
    registry: PipelineRegistry,
    queue: JobQueue,
    *,
    filename: str,
    content: bytes,
    relationship: ResourceRelationship | str = ResourceRelationship.REFERENCE,
) -> tuple[Resource, bool]:
    """Store an uploaded file and enqueue processing.

    Returns (resource, created). created=False means identical content was
    already ingested and the existing resource is returned untouched.
    """
    if not content:
        raise ValidationError("uploaded file is empty")
    resource_type = resource_type_for_filename(filename)
    ext = Path(filename).suffix.lower()
    title = Path(filename).stem.strip() or filename
    return _ingest(
        engine,
        settings,
        registry,
        queue,
        resource_type=resource_type,
        title=title,
        content=content,
        extension=ext,
        relationship=relationship,
    )


def create_note(
    engine: KnowledgeEngine,
    settings: Settings,
    registry: PipelineRegistry,
    queue: JobQueue,
    *,
    title: str,
    content: str,
    relationship: ResourceRelationship | str = ResourceRelationship.REFERENCE,
) -> tuple[Resource, bool]:
    """Store an in-app note (Markdown) and enqueue processing."""
    if not content.strip():
        raise ValidationError("note content is empty")
    return _ingest(
        engine,
        settings,
        registry,
        queue,
        resource_type=ResourceType.NOTE,
        title=title,
        content=content.encode("utf-8"),
        extension=".md",
        relationship=relationship,
    )


def _ingest(
    engine: KnowledgeEngine,
    settings: Settings,
    registry: PipelineRegistry,
    queue: JobQueue,
    *,
    resource_type: ResourceType,
    title: str,
    content: bytes,
    extension: str,
    relationship: ResourceRelationship | str,
) -> tuple[Resource, bool]:
    content_hash = hashlib.sha256(content).hexdigest()
    existing = engine.find_resource_by_hash(content_hash)
    if existing is not None:
        return existing, False

    resource = engine.register_resource(
        type=resource_type,
        title=title,
        content_hash=content_hash,
        relationship=relationship,
    )
    relative_path = f"{resource.id}/original{extension}"
    original = settings.resources_dir / relative_path
    original.parent.mkdir(parents=True, exist_ok=True)
    original.write_bytes(content)
    resource = engine.set_resource_path(resource.id, relative_path)

    registry.publish(queue, "resource.uploaded", {"resource_id": resource.id})
    return resource, True
