"""AI provider abstraction and implementations."""

from pks.config import Settings
from pks.providers.anthropic import AnthropicProvider
from pks.providers.base import CompletionProvider, ProviderError, Tier


def make_provider(settings: Settings) -> CompletionProvider | None:
    """Build the configured provider; None when no AI credentials are set."""
    if not settings.anthropic_api_key:
        return None
    return AnthropicProvider(
        api_key=settings.anthropic_api_key,
        heavy_model=settings.heavy_model,
        fast_model=settings.fast_model,
    )


__all__ = ["AnthropicProvider", "CompletionProvider", "ProviderError", "Tier", "make_provider"]
