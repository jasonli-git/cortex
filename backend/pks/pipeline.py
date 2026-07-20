"""Pipeline composition: which stages run, in what chain.

With an AI provider configured:

    resource.uploaded → [parse] → [chunk] → [extract_knowledge] → [summarize]
                      → [index] → ready

Without one (no API key), extraction is skipped but everything else — parsing,
chunking, embedding, and search indexing — still runs:

    resource.uploaded → [parse] → [chunk] → [index] → ready

The index stage marks the resource ready in both configurations.
"""

from pks import extraction, ingestion, search
from pks.embeddings.base import EmbeddingProvider
from pks.events.bus import PipelineRegistry
from pks.providers.base import CompletionProvider


def build_pipeline(
    provider: CompletionProvider | None, embedder: EmbeddingProvider
) -> PipelineRegistry:
    registry = PipelineRegistry()
    ingestion.pipeline.register_stages(registry)
    if provider is not None:
        extraction.register_stages(registry, provider)
        search.register_stages(registry, embedder, on="resource.summarized")
    else:
        search.register_stages(registry, embedder, on="resource.chunked")
    return registry
