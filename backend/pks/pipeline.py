"""Pipeline composition: which stages run, in what chain.

With an AI provider configured:

    resource.uploaded → [parse] → [chunk] → [extract_knowledge] → [summarize]
                      → [index] → ready → [dedupe]

(dedupe refines the graph after the resource is already usable — merges are
background quality work, per the spec's "relationships continuously improved".)

Without one (no API key), extraction is skipped but everything else — parsing,
chunking, embedding, and search indexing — still runs:

    resource.uploaded → [parse] → [chunk] → [index] → ready

The index stage marks the resource ready in both configurations.
"""

from pks import extraction, graph, ingestion, search
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
        graph.register_stages(registry, provider, embedder)
    else:
        search.register_stages(registry, embedder, on="resource.chunked")
    return registry
