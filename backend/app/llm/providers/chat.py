"""Chat inference entry point: resolve OpenRouter vs Hugging Face by env keys."""

from __future__ import annotations

import logging
from typing import Any, Literal

from fastapi import HTTPException

from app.core.config import Settings
from app.core.config import settings as app_settings
from app.llm.providers.base import ChatProvider, StructuredOutputT
from app.llm.providers.exceptions import raise_ai_unavailable
from app.llm.providers.huggingface import huggingface_provider
from app.llm.providers.openrouter import openrouter_provider

ChatProviderName = Literal["openrouter", "huggingface"]

# Box-is-down signals: bad gateway, service unavailable, gateway timeout. Everything
# else - auth, malformed request, a refusal - is a fault the fallback would repeat.
_FALLBACK_STATUS = frozenset({502, 503, 504})

logger = logging.getLogger(__name__)


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
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> StructuredOutputT:
    """Structured chat completion via the configured provider (OpenRouter preferred).

    When ``base_url`` is supplied the call is pinned to that endpoint and routed through
    the Hugging Face provider, which is the plain OpenAI-compatible client. OpenRouter's
    path uses ``beta.chat.completions.parse``, which assumes that vendor's structured
    output support rather than a generic ``/v1/chat/completions``.
    """
    pinned = bool((base_url or "").strip())
    provider: ChatProvider = huggingface_provider if pinned else resolve_chat_provider(
        config=config
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
        # A pinned endpoint is a single box we operate; the router is a managed service on
        # the same protocol. When the box is unreachable, degrade to it rather than fail
        # the turn. Only transport-level faults qualify: a 401 means the key is wrong and
        # a 4xx means the request is wrong, and both should stay loud instead of being
        # papered over by a silent, more expensive fallback.
        if not pinned or exc.status_code not in _FALLBACK_STATUS:
            raise
        logger.warning(
            "intake_endpoint_fallback",
            extra={"status_code": exc.status_code, "pinned_model": model},
        )

    fallback = resolve_chat_provider(config=config)
    return await fallback.generate_structured_output(
        messages=messages,
        response_format=response_format,
        temperature=temperature,
        max_tokens=max_tokens,
        include_schema_instruction=include_schema_instruction,
    )
