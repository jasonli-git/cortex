"""Pure extraction functions: provider + chunks in, validated results out.

No engine access here — applying results to the knowledge base happens in
stages.py. That split keeps these functions unit-testable with a fake
provider and keeps prompt/batching concerns out of the persistence code.
"""

from __future__ import annotations

from pks.core.models import ResourceChunk
from pks.extraction import prompts
from pks.extraction.models import ExtractionResult, SummaryResult
from pks.providers.base import CompletionProvider

# Roughly 8k tokens of source text per extraction call.
EXTRACTION_BATCH_CHARS = 32_000
# Above this, summarize in parts and combine (map-reduce).
SUMMARY_SINGLE_CALL_CHARS = 120_000


def batch_chunks(
    chunks: list[ResourceChunk], *, budget_chars: int = EXTRACTION_BATCH_CHARS
) -> list[list[ResourceChunk]]:
    batches: list[list[ResourceChunk]] = []
    current: list[ResourceChunk] = []
    current_len = 0
    for chunk in chunks:
        if current and current_len + len(chunk.text) > budget_chars:
            batches.append(current)
            current, current_len = [], 0
        current.append(chunk)
        current_len += len(chunk.text)
    if current:
        batches.append(current)
    return batches


def extract_batch(
    provider: CompletionProvider, title: str, chunks: list[ResourceChunk]
) -> ExtractionResult:
    prompt = prompts.extraction_prompt(
        title, [(c.ordinal, c.structure_path, c.text) for c in chunks]
    )
    raw = provider.extract_structured(
        prompt=prompt,
        schema=prompts.EXTRACTION_SCHEMA,
        system=prompts.EXTRACTION_SYSTEM,
        tier="heavy",
    )
    return ExtractionResult.model_validate(raw)


def summarize(
    provider: CompletionProvider, title: str, chunks: list[ResourceChunk]
) -> SummaryResult:
    full_text = "\n\n".join(chunk.text for chunk in chunks)
    if len(full_text) <= SUMMARY_SINGLE_CALL_CHARS:
        raw = provider.extract_structured(
            prompt=prompts.summary_prompt(title, full_text),
            schema=prompts.SUMMARY_SCHEMA,
            system=prompts.SUMMARY_SYSTEM,
            tier="heavy",
        )
        return SummaryResult.model_validate(raw)

    # Map-reduce for long documents: summarize parts, then combine.
    partials: list[str] = []
    for batch in batch_chunks(chunks, budget_chars=SUMMARY_SINGLE_CALL_CHARS):
        part_text = "\n\n".join(chunk.text for chunk in batch)
        raw = provider.extract_structured(
            prompt=prompts.summary_prompt(title, part_text),
            schema=prompts.SUMMARY_SCHEMA,
            system=prompts.SUMMARY_SYSTEM,
            tier="heavy",
        )
        partials.append(SummaryResult.model_validate(raw).summary)

    raw = provider.extract_structured(
        prompt=prompts.combine_summaries_prompt(title, partials),
        schema=prompts.SUMMARY_SCHEMA,
        system=prompts.SUMMARY_SYSTEM,
        tier="heavy",
    )
    return SummaryResult.model_validate(raw)
