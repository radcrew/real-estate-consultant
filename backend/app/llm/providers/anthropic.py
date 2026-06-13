"""Anthropic Claude provider for structured intake outputs."""

from __future__ import annotations

import json
from typing import Any, TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

from app.core.config import Settings, settings
from app.utils.exceptions import (
    raise_bad_gateway,
    raise_gateway_timeout,
    raise_service_unavailable,
)

StructuredOutputT = TypeVar("StructuredOutputT", bound=BaseModel)

_TIMEOUT = 60.0


class AnthropicProvider:
    def __init__(
        self, *, settings: Settings, client: anthropic.AsyncAnthropic | None = None
    ) -> None:
        self.settings = settings
        self.client = client or anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key or "missing-anthropic-api-key",
            timeout=_TIMEOUT,
        )

    async def generate_structured_output(
        self,
        *,
        messages: list[dict[str, Any]],
        response_format: type[StructuredOutputT],
        temperature: float,
        max_tokens: int,
    ) -> StructuredOutputT:
        if not self.settings.anthropic_api_key.strip():
            raise_service_unavailable("Anthropic API key is not configured.")

        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        user_parts = [
            {"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"
        ]
        system_prompt = "\n\n".join(system_parts) if system_parts else None

        try:
            kwargs: dict[str, Any] = dict(
                model=self.settings.anthropic_model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=user_parts,
            )
            if system_prompt:
                kwargs["system"] = system_prompt

            response = await self.client.messages.create(**kwargs)
        except anthropic.APITimeoutError as exc:
            raise_gateway_timeout("Timed out while calling Claude API.", cause=exc)
        except anthropic.APIError as exc:
            raise_bad_gateway(
                "The AI service is temporarily unavailable. Please try again later.",
                cause=exc,
            )

        text = response.content[0].text if response.content else ""
        text = text.strip()

        # Extract the first JSON object or array, tolerating leading/trailing prose
        # and markdown fences that Claude sometimes adds.
        start = next((i for i, c in enumerate(text) if c in "{["), -1)
        end_brace = text.rfind("}")
        end_bracket = text.rfind("]")
        end = max(end_brace, end_bracket)
        if start != -1 and end != -1 and end >= start:
            text = text[start : end + 1]

        try:
            data = json.loads(text)
        except (json.JSONDecodeError, ValueError) as exc:
            raise_bad_gateway(
                "We couldn't process the assistant's reply. Please try again in a moment.",
                cause=exc,
            )

        try:
            return response_format.model_validate(data)
        except ValidationError as exc:
            raise_bad_gateway(
                "We couldn't process the assistant's reply. Please try again in a moment.",
                cause=exc,
            )


anthropic_provider = AnthropicProvider(settings=settings)
