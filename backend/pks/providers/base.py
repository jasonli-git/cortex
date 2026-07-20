"""Provider abstraction (spec principle 6: AI providers are infrastructure).

Every module that needs a language model depends on CompletionProvider, never
on a vendor SDK. Callers pick a tier, not a model: `heavy` for ingestion-time
extraction, `fast` for conversation and navigation (spec: expensive reasoning
happens once).
"""

from typing import Literal, Protocol

Tier = Literal["heavy", "fast"]


class ProviderError(Exception):
    """The provider could not produce a usable response."""


class CompletionProvider(Protocol):
    def extract_structured(
        self,
        *,
        prompt: str,
        schema: dict,
        system: str | None = None,
        tier: Tier = "heavy",
        max_tokens: int = 8192,
    ) -> dict:
        """Run a completion constrained to the given JSON schema; returns the parsed object."""
        ...

    def complete(
        self,
        *,
        prompt: str,
        system: str | None = None,
        tier: Tier = "fast",
        max_tokens: int = 2048,
    ) -> str:
        """Plain text completion."""
        ...
