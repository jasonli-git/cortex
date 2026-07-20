"""Prompts and schema for the chat service (fast tier)."""

CHAT_SYSTEM = (
    "You are the conversational interface of the user's personal knowledge "
    "system. Ground your answers in the user's stored knowledge (the numbered "
    "sources) whenever it is relevant; use your general knowledge to fill "
    "gaps, and always keep the two clearly separated. Never attribute to a "
    "source anything it does not actually support."
)

CHAT_SCHEMA = {
    "type": "object",
    "properties": {
        "segments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "source": {"type": "string", "enum": ["pks", "model"]},
                    "source_numbers": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["text", "source", "source_numbers"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["segments"],
    "additionalProperties": False,
}


def chat_prompt(sources_block: str, history_block: str, question: str) -> str:
    sources = sources_block or "(the knowledge base returned nothing relevant)"
    history = f"Conversation so far:\n\n{history_block}\n\n" if history_block else ""
    return f"""Answer the user's message, split into ordered segments that read as one
coherent reply when joined together.

Rules for each segment:
- source "pks": the statement is supported by the numbered sources below; \
list the supporting source numbers in source_numbers.
- source "model": the statement comes from your general knowledge; \
source_numbers stays empty.
- Prefer the user's stored knowledge where it answers the question. If the \
sources don't cover something, say it from general knowledge rather than \
forcing a citation.

Sources from the user's knowledge base:

{sources}

{history}User's message:

{question}"""
