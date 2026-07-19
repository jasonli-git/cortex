"""Structure-aware chunking of parsed documents.

Chunks never cross section boundaries, so every chunk carries the structure
path of the section it came from (used for provenance and citations).
Paragraphs are packed greedily up to a target size; oversized paragraphs are
hard-split at whitespace.

Token counts are a chars/4 estimate — good enough for packing; exact counts
are not load-bearing anywhere.
"""

from __future__ import annotations

import re

from pks.ingestion.parsers import ParsedDocument

# ~1000 tokens per chunk at the 4-chars/token estimate.
DEFAULT_TARGET_CHARS = 4000

ChunkTuple = tuple[int, str, str | None, int]  # (ordinal, text, structure_path, token_count)

_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def chunk_document(
    doc: ParsedDocument, *, target_chars: int = DEFAULT_TARGET_CHARS
) -> list[ChunkTuple]:
    chunks: list[ChunkTuple] = []
    ordinal = 0
    for section in doc.sections:
        for text in _chunk_text(section.text, target_chars):
            chunks.append((ordinal, text, section.path, estimate_tokens(text)))
            ordinal += 1
    return chunks


def _chunk_text(text: str, target_chars: int) -> list[str]:
    pieces: list[str] = []
    for paragraph in _PARAGRAPH_SPLIT.split(text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if len(paragraph) <= target_chars:
            pieces.append(paragraph)
        else:
            pieces.extend(_hard_split(paragraph, target_chars))

    # Greedily pack consecutive pieces up to the target size.
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for piece in pieces:
        added = len(piece) + (2 if current else 0)
        if current and current_len + added > target_chars:
            chunks.append("\n\n".join(current))
            current, current_len = [], 0
        current.append(piece)
        current_len += added
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def _hard_split(paragraph: str, target_chars: int) -> list[str]:
    """Split an oversized paragraph at whitespace near the target size."""
    parts: list[str] = []
    remaining = paragraph
    while len(remaining) > target_chars:
        split_at = remaining.rfind(" ", target_chars // 2, target_chars)
        if split_at == -1:
            split_at = target_chars
        parts.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        parts.append(remaining)
    return parts
