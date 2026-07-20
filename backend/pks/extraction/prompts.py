"""Prompts and JSON schemas for the extraction stages.

Schemas follow the structured-outputs rules: every object closes with
additionalProperties=false and lists all properties as required. Soft
constraints (confidence range, quote length) are enforced in the result
models instead, since structured outputs don't support numeric bounds.
"""

EXTRACTION_SYSTEM = (
    "You are the knowledge-extraction stage of a personal knowledge system. "
    "You turn source text into structured, reusable knowledge objects that "
    "must remain meaningful years later, independent of the source document. "
    "Extract only what the text supports; never invent facts."
)

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["concept", "person", "organization", "place", "event"],
                    },
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "aliases": {"type": "array", "items": {"type": "string"}},
                    "quote": {"type": "string"},
                    "chunk_ordinal": {"type": "integer"},
                },
                "required": ["type", "name", "description", "aliases", "quote", "chunk_ordinal"],
                "additionalProperties": False,
            },
        },
        "relations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "from_name": {"type": "string"},
                    "to_name": {"type": "string"},
                    "type": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["from_name", "to_name", "type", "confidence"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["entities", "relations"],
    "additionalProperties": False,
}


def extraction_prompt(title: str, chunks: list[tuple[int, str | None, str]]) -> str:
    """chunks: (ordinal, structure_path, text)."""
    rendered = "\n\n".join(
        f"[chunk {ordinal}]" + (f" ({path})" if path else "") + f"\n{text}"
        for ordinal, path, text in chunks
    )
    return f"""Extract the knowledge worth keeping from this excerpt of "{title}".

Guidelines:
- Extract concepts, people, organizations, places, and events that are central \
enough to be worth remembering — not every passing mention.
- Use the canonical name; put other forms the text uses in aliases.
- description: 1-2 self-contained sentences based only on this text.
- quote: a short verbatim phrase (at most 25 words) from a chunk that evidences \
the entity, and chunk_ordinal: the [chunk N] number that phrase appears in.
- relations: meaningful relationships between the extracted entities. Use types \
like related_to, part_of, participated_in, located_in (or a more precise \
lowercase_snake_case type). confidence between 0 and 1.
- Only relate entities that appear in your entities list.

Excerpt:

{rendered}"""


SUMMARY_SYSTEM = (
    "You are the summarization stage of a personal knowledge system. "
    "Your summaries are stored as long-term knowledge, so they must stand on "
    "their own without the source at hand."
)

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "key_points"],
    "additionalProperties": False,
}


def summary_prompt(title: str, text: str) -> str:
    return f"""Summarize the following document, titled "{title}".

- summary: a faithful, self-contained summary of at most 300 words.
- key_points: the 3-8 most important takeaways, one sentence each.

Document:

{text}"""


def combine_summaries_prompt(title: str, partials: list[str]) -> str:
    rendered = "\n\n---\n\n".join(partials)
    return f"""These are partial summaries of consecutive parts of "{title}".
Merge them into one coherent whole.

- summary: a faithful, self-contained summary of at most 300 words.
- key_points: the 3-8 most important takeaways, one sentence each.

Partial summaries:

{rendered}"""
