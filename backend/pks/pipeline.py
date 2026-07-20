"""Pipeline composition: which stages run, in what chain.

With a provider configured:

    resource.uploaded → [parse] → [chunk] → [extract_knowledge] → [summarize] → ready

Without one (no API key), the pipeline ends at chunking and the resource is
still fully usable as parsed, chunked evidence.
"""

from pks import extraction, ingestion
from pks.events.bus import PipelineRegistry
from pks.providers.base import CompletionProvider


def build_pipeline(provider: CompletionProvider | None) -> PipelineRegistry:
    registry = PipelineRegistry()
    ingestion.pipeline.register_stages(registry, mark_ready_after_chunk=provider is None)
    if provider is not None:
        extraction.register_stages(registry, provider)
    return registry
