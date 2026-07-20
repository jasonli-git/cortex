"""The parse/chunk pipeline stages, wired into the event registry.

    resource.uploaded → [parse] → resource.parsed → [chunk] → resource.chunked

The parse stage persists its output (parsed.json alongside the original) so
each stage is independently retryable. Downstream stages (extraction, index)
subscribe to `resource.chunked` — see pks.pipeline for the full chain.
"""

from __future__ import annotations

import json
from pathlib import Path

from pks.core.models import Resource
from pks.events.bus import PipelineRegistry, StageContext
from pks.ingestion.chunking import chunk_document
from pks.ingestion.parsers import ParsedDocument, parse_resource_file

PARSED_FILENAME = "parsed.json"


def resource_dir(settings, resource: Resource) -> Path:
    return settings.resources_dir / resource.id


def register_stages(registry: PipelineRegistry) -> None:
    @registry.stage("parse", on="resource.uploaded")
    def parse(ctx: StageContext, payload: dict) -> None:
        resource = ctx.engine.get_resource(payload["resource_id"])
        ctx.engine.set_resource_status(resource.id, "processing")

        original = ctx.settings.resources_dir / resource.path
        doc = parse_resource_file(original, resource.type)

        out_path = resource_dir(ctx.settings, resource) / PARSED_FILENAME
        out_path.write_text(json.dumps(doc.to_dict()), encoding="utf-8")

        ctx.emit("resource.parsed", {"resource_id": resource.id})

    @registry.stage("chunk", on="resource.parsed")
    def chunk(ctx: StageContext, payload: dict) -> None:
        resource = ctx.engine.get_resource(payload["resource_id"])

        parsed_path = resource_dir(ctx.settings, resource) / PARSED_FILENAME
        doc = ParsedDocument.from_dict(json.loads(parsed_path.read_text(encoding="utf-8")))

        ctx.engine.set_chunks(resource.id, chunk_document(doc))
        ctx.emit("resource.chunked", {"resource_id": resource.id})
