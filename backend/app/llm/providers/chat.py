"""Chat inference entry point: resolve OpenRouter vs Hugging Face by env keys."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from app.core.config import Settings
from app.core.config import settings as app_settings
from app.llm.providers.base import ChatProvider, StructuredOutputT
from app.llm.providers.bedrock_chat import bedrock_chat_provider
from app.llm.providers.exceptions import raise_ai_unavailable
from app.llm.providers.huggingface import huggingface_provider
from app.llm.providers.openrouter import openrouter_provider

if TYPE_CHECKING:
    from app.llm.providers.routing import LlmTask

ChatProviderName = Literal["openrouter", "huggingface", "bedrock"]


def resolve_chat_provider_name(*, config: Settings) -> ChatProviderName | None:
    """Return the configured chat provider name, or None when no LLM keys are set.

    Bedrock is checked last on purpose: it bills per token from the first request,
    so merely configuring a region must never silently displace a cheaper provider
    that is already working.
    """
    if config.openrouter_api_key.strip():
        return "openrouter"
    if config.hf_token.strip():
        return "huggingface"
    if config.aws_region.strip():
        return "bedrock"
    return None


def resolve_chat_provider(*, config: Settings | None = None) -> ChatProvider:
    """Return the active chat provider; raises 503 when no LLM keys are configured."""
    active_config = config or app_settings
    provider_name = resolve_chat_provider_name(config=active_config)
    if provider_name == "openrouter":
        return openrouter_provider
    if provider_name == "huggingface":
        return huggingface_provider
    if provider_name == "bedrock":
        return bedrock_chat_provider
    raise_ai_unavailable()


async def generate_structured_output(
    *,
    messages: list[dict[str, Any]],
    response_format: type[StructuredOutputT],
    temperature: float,
    max_tokens: int,
    config: Settings | None = None,
    task: LlmTask | None = None,
) -> StructuredOutputT:
    """Structured chat completion via the provider routed for ``task``.

    Omitting ``task`` uses ``llm_route_default``, which itself defaults to the
    key-presence order — so an unannotated call site behaves as it always has.
    """
    # Imported here, not at module scope: routing imports this module for its "auto"
    # fallback, so a top-level import would be circular.
    from app.llm.providers.routing import resolve_chat_provider_for_task

    provider = resolve_chat_provider_for_task(task=task, config=config)
    return await provider.generate_structured_output(
        messages=messages,
        response_format=response_format,
        temperature=temperature,
        max_tokens=max_tokens,
    )
