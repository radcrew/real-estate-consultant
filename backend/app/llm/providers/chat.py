"""Chat inference entry point: resolve OpenRouter vs Hugging Face by env keys."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Literal

from fastapi import HTTPException

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

# Box-is-down signals: bad gateway, service unavailable, gateway timeout. Everything
# else - auth, malformed request, a refusal - is a fault the fallback would repeat.
_FALLBACK_STATUS = frozenset({502, 503, 504})

logger = logging.getLogger(__name__)


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
    include_schema_instruction: bool = True,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> StructuredOutputT:
    """Structured chat completion via the provider routed for ``task``.

    Omitting ``task`` uses ``llm_route_default``, which itself defaults to the
    key-presence order — so an unannotated call site behaves as it always has.

    ``base_url`` pins the call to one OpenAI-compatible endpoint and overrides the route,
    going through the Hugging Face provider because that is the plain client; OpenRouter's
    path uses ``beta.chat.completions.parse``, which assumes that vendor's structured
    output support rather than a generic ``/v1/chat/completions``.

    An explicit pin beating the route is deliberate. The route says which provider a task
    prefers; a pin says which box this deployment is actually running, and the second is
    the more specific statement.
    """
    # Imported here, not at module scope: routing imports this module for its "auto"
    # fallback, so a top-level import would be circular.
    from app.llm.providers.routing import resolve_chat_provider_for_task

    pinned = bool((base_url or "").strip())
    provider: ChatProvider = (
        huggingface_provider if pinned
        else resolve_chat_provider_for_task(task=task, config=config)
    )
    try:
        return await provider.generate_structured_output(
            messages=messages,
            response_format=response_format,
            temperature=temperature,
            max_tokens=max_tokens,
            include_schema_instruction=include_schema_instruction,
            model=model,
            base_url=base_url,
            api_key=api_key,
        )
    except HTTPException as exc:
        # A pinned endpoint is a single box we operate; the routed provider is a managed
        # service on the same protocol. When the box is unreachable, degrade to it rather
        # than fail the turn. Only transport-level faults qualify: a 401 means the key is
        # wrong and a 4xx means the request is wrong, and both should stay loud instead of
        # being papered over by a silent, more expensive fallback.
        if not pinned or exc.status_code not in _FALLBACK_STATUS:
            raise
        logger.warning(
            "intake_endpoint_fallback",
            extra={"status_code": exc.status_code, "pinned_model": model},
        )

    fallback = resolve_chat_provider_for_task(task=task, config=config)
    return await fallback.generate_structured_output(
        messages=messages,
        response_format=response_format,
        temperature=temperature,
        max_tokens=max_tokens,
        include_schema_instruction=include_schema_instruction,
    )
