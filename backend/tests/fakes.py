"""Deterministic fakes for AI providers — no network, no model downloads."""

import re
import zlib

from pks.extraction import prompts

ROME_MD = b"""# Rome

## Founding

Rome was founded in 753 BC, according to legend, by Romulus.

## Republic

The Roman Republic began in 509 BC after the last king was overthrown.
"""

EXTRACTION_RESPONSE = {
    "entities": [
        {
            "type": "place",
            "name": "Rome",
            "description": "An ancient city, founded in 753 BC.",
            "aliases": [],
            "quote": "Rome was founded in 753 BC",
            "chunk_ordinal": 0,
        },
        {
            "type": "concept",
            "name": "Roman Republic",
            "description": "The Roman state after the monarchy, from 509 BC.",
            "aliases": ["the Republic"],
            "quote": "The Roman Republic began in 509 BC",
            "chunk_ordinal": 1,
        },
    ],
    "relations": [
        {"from_name": "Roman Republic", "to_name": "Rome", "type": "located_in", "confidence": 0.9},
        # References an entity that was never extracted; must be skipped.
        {"from_name": "Rome", "to_name": "Carthage", "type": "related_to", "confidence": 0.5},
    ],
}

SUMMARY_RESPONSE = {
    "summary": "Rome was founded in 753 BC and became a republic in 509 BC.",
    "key_points": ["Founded 753 BC", "Republic from 509 BC"],
}


class FakeProvider:
    """Returns canned responses; records prompts for inspection."""

    def __init__(self, extraction: dict = EXTRACTION_RESPONSE, summary: dict = SUMMARY_RESPONSE):
        self._extraction = extraction
        self._summary = summary
        self.extraction_prompts: list[str] = []
        self.summary_prompts: list[str] = []

    def extract_structured(self, *, prompt, schema, system=None, tier="heavy", max_tokens=8192):
        if schema is prompts.EXTRACTION_SCHEMA:
            self.extraction_prompts.append(prompt)
            return self._extraction
        self.summary_prompts.append(prompt)
        return self._summary

    def complete(self, *, prompt, system=None, tier="fast", max_tokens=2048):
        return "ok"


class FakeEmbedder:
    """Stable bag-of-words hash embeddings: shared words → higher similarity."""

    model_name = "fake-embedder"
    dim = 64

    def __init__(self):
        self.embedded_texts: list[str] = []

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        for word in re.findall(r"\w+", text.lower()):
            vector[zlib.crc32(word.encode()) % self.dim] += 1.0
        norm = sum(value * value for value in vector) ** 0.5 or 1.0
        return [value / norm for value in vector]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.embedded_texts.extend(texts)
        return [self._vector(text) for text in texts]

    def embed_query(self, query: str) -> list[float]:
        return self._vector(query)
