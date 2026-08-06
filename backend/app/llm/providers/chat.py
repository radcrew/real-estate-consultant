"""Chat inference entry point: resolve OpenRouter vs Hugging Face by env keys."""

from __future__ import annotations

from typing import Any, Literal

from app.core.config import Settings
from app.core.config import settings as app_settings
from app.llm.providers.base import ChatProvider, StructuredOutputT
from app.llm.providers.exceptions import raise_ai_unavailable
from app.llm.providers.huggingface import huggingface_provider
from app.llm.providers.openrouter import openrouter_provider

ChatProviderName = Literal["openrouter", "huggingface"]


def resolve_chat_provider_name(*, config: Settings) -> ChatProviderName | None:
    """Return the configured chat provider name, or None when no LLM keys are set."""
    if config.openrouter_api_key.strip():
        return "openrouter"
    if config.hf_token.strip():
        return "huggingface"
    return None


def resolve_chat_provider(*, config: Settings | None = None) -> ChatProvider:
    """Return the active chat provider; raises 503 when no LLM keys are configured."""
    active_config = config or app_settings
    provider_name = resolve_chat_provider_name(config=active_config)
    if provider_name == "openrouter":
        return openrouter_provider
    if provider_name == "huggingface":
        return huggingface_provider
    raise_ai_unavailable()


async def generate_structured_output(
    *,
    messages: list[dict[str, Any]],
    response_format: type[StructuredOutputT],
    temperature: float,
    max_tokens: int,
    config: Settings | None = None,
    include_schema_instruction: bool = True,
) -> StructuredOutputT:
    """Structured chat completion via the configured provider (OpenRouter preferred)."""
    provider = resolve_chat_provider(config=config)
    return await provider.generate_structured_output(
        messages=messages,
        response_format=response_format,
        temperature=temperature,
        max_tokens=max_tokens,
        include_schema_instruction=include_schema_instruction,
    )
