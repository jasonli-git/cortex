"""Anthropic implementation of CompletionProvider (the V1 default)."""

from __future__ import annotations

import json

import anthropic

from pks.providers.base import ProviderError, Tier


class AnthropicProvider:
    def __init__(self, *, api_key: str, heavy_model: str, fast_model: str):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._models: dict[str, str] = {"heavy": heavy_model, "fast": fast_model}

    def _create(self, *, prompt: str, system: str | None, tier: Tier, max_tokens: int, **kwargs):
        request: dict = {
            "model": self._models[tier],
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs,
        }
        if system is not None:
            request["system"] = system
        try:
            response = self._client.messages.create(**request)
        except anthropic.APIError as exc:
            raise ProviderError(f"anthropic request failed: {exc}") from exc

        if response.stop_reason == "refusal":
            raise ProviderError("model declined the request (stop_reason=refusal)")
        if response.stop_reason == "max_tokens":
            raise ProviderError(f"response truncated at max_tokens={max_tokens}")
        return response

    def extract_structured(
        self,
        *,
        prompt: str,
        schema: dict,
        system: str | None = None,
        tier: Tier = "heavy",
        max_tokens: int = 8192,
    ) -> dict:
        response = self._create(
            prompt=prompt,
            system=system,
            tier=tier,
            max_tokens=max_tokens,
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        text = next((block.text for block in response.content if block.type == "text"), None)
        if text is None:
            raise ProviderError("structured response contained no text block")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProviderError(f"structured response was not valid JSON: {exc}") from exc

    def complete(
        self,
        *,
        prompt: str,
        system: str | None = None,
        tier: Tier = "fast",
        max_tokens: int = 2048,
    ) -> str:
        response = self._create(prompt=prompt, system=system, tier=tier, max_tokens=max_tokens)
        return "".join(block.text for block in response.content if block.type == "text")
