"""OpenRouter provider wrapper built on the OpenAI Python SDK."""

from __future__ import annotations

import logging
import time
from typing import Any, TypeVar

import httpx
from openai import APITimeoutError, AsyncOpenAI, OpenAIError
from openai.types.completion_usage import CompletionUsage
from pydantic import BaseModel, ValidationError

from app.core.config import Settings, settings
from app.llm.providers.exceptions import (
    raise_openrouter_api_key_not_configured,
    raise_openrouter_completion_parse_failed,
    raise_openrouter_openai_error,
    raise_openrouter_request_timeout,
    raise_openrouter_structured_refusal,
    raise_openrouter_structured_reply_incomplete,
)

OR_CONNECT_TIMEOUT = 20.0
OR_READ_TIMEOUT = 75.0
OR_WRITE_TIMEOUT = 30.0
OR_POOL_TIMEOUT = 10.0
OR_TRANSIENT_RETRIES = 3

logger = logging.getLogger(__name__)

StructuredOutputT = TypeVar("StructuredOutputT", bound=BaseModel)


class OpenRouterProvider:
    """Provider client for OpenRouter OpenAI-compatible chat completions."""

    def __init__(
        self,
        *,
        settings: Settings,
        timeout: httpx.Timeout | None = None,
        transient_retries: int = OR_TRANSIENT_RETRIES,
        client: AsyncOpenAI | None = None,
    ) -> None:
        self.settings = settings
        self.timeout = timeout or httpx.Timeout(
            connect=OR_CONNECT_TIMEOUT,
            read=OR_READ_TIMEOUT,
            write=OR_WRITE_TIMEOUT,
            pool=OR_POOL_TIMEOUT,
        )
        self.transient_retries = transient_retries
        default_headers: dict[str, str] = {}
        if settings.openrouter_http_referer.strip():
            default_headers["HTTP-Referer"] = settings.openrouter_http_referer.strip()
        if settings.openrouter_app_title.strip():
            default_headers["X-Title"] = settings.openrouter_app_title.strip()
        self.client = client or AsyncOpenAI(
            api_key=settings.openrouter_api_key or "missing-openrouter-api-key",
            base_url=settings.openrouter_base_url,
            timeout=self.timeout,
            max_retries=transient_retries,
            default_headers=default_headers or None,
        )

    def _log_call(
        self,
        *,
        outcome: str,
        duration_ms: float,
        usage: CompletionUsage | None = None,
        model: str | None = None,
    ) -> None:
        cost_usd = None
        prompt_tokens = getattr(usage, "prompt_tokens", None) if usage is not None else None
        completion_tokens = getattr(usage, "completion_tokens", None) if usage is not None else None
        total_tokens = getattr(usage, "total_tokens", None) if usage is not None else None
        if usage is not None and prompt_tokens is not None:
            completion_for_cost = completion_tokens or 0
            cost_usd = round(
                (
                    prompt_tokens * self.settings.openrouter_input_cost_per_1m
                    + completion_for_cost * self.settings.openrouter_output_cost_per_1m
                )
                / 1_000_000,
                6,
            )
        logger.info(
            "llm_call",
            extra={
                "provider": "openrouter",
                "model": model or self.settings.openrouter_chat_model,
                "outcome": outcome,
                "duration_ms": round(duration_ms, 2),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": cost_usd,
            },
        )

    async def generate_structured_output(
        self,
        *,
        messages: list[dict[str, Any]],
        response_format: type[StructuredOutputT],
        temperature: float,
        max_tokens: int,
        include_schema_instruction: bool = True,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> StructuredOutputT:
        """Request a typed structured output from OpenRouter.

        ``include_schema_instruction`` is accepted for protocol parity and unused:
        ``beta.chat.completions.parse`` sends the schema natively, so this provider
        never prepends a copy to ``messages``.

        The endpoint overrides are likewise accepted for parity and unused. Intake's
        override is resolved in ``chat.py``, which routes a pinned task to the Hugging
        Face provider directly rather than through the configured default.
        """
        if not self.settings.openrouter_api_key.strip():
            raise_openrouter_api_key_not_configured()

        start = time.perf_counter()
        try:
            completion = await self.client.beta.chat.completions.parse(
                model=self.settings.openrouter_chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )
        except ValidationError as exc:
            self._log_call(outcome="parse_failed", duration_ms=(time.perf_counter() - start) * 1000)
            raise_openrouter_completion_parse_failed(cause=exc)
        except APITimeoutError as exc:
            self._log_call(outcome="timeout", duration_ms=(time.perf_counter() - start) * 1000)
            raise_openrouter_request_timeout(cause=exc)
        except OpenAIError as exc:
            self._log_call(outcome="error", duration_ms=(time.perf_counter() - start) * 1000)
            raise_openrouter_openai_error(cause=exc)

        duration_ms = (time.perf_counter() - start) * 1000
        message = completion.choices[0].message
        if message.parsed is not None:
            self._log_call(outcome="success", duration_ms=duration_ms, usage=completion.usage)
            return message.parsed
        if message.refusal:
            self._log_call(outcome="refusal", duration_ms=duration_ms, usage=completion.usage)
            raise_openrouter_structured_refusal(refusal=str(message.refusal))
        self._log_call(outcome="incomplete", duration_ms=duration_ms, usage=completion.usage)
        raise_openrouter_structured_reply_incomplete()

    async def embed(self, *, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text via OpenRouter."""
        if not texts:
            return []
        if not self.settings.openrouter_api_key.strip():
            raise_openrouter_api_key_not_configured()

        start = time.perf_counter()
        try:
            response = await self.client.embeddings.create(
                model=self.settings.openrouter_embedding_model,
                input=texts,
            )
        except APITimeoutError as exc:
            self._log_call(outcome="timeout", duration_ms=(time.perf_counter() - start) * 1000)
            raise_openrouter_request_timeout(cause=exc)
        except OpenAIError as exc:
            self._log_call(outcome="error", duration_ms=(time.perf_counter() - start) * 1000)
            raise_openrouter_openai_error(cause=exc)

        duration_ms = (time.perf_counter() - start) * 1000
        ordered = sorted(response.data, key=lambda item: item.index)
        self._log_call(
            outcome="success",
            duration_ms=duration_ms,
            usage=response.usage,
            model=self.settings.openrouter_embedding_model,
        )
        return [list(item.embedding) for item in ordered]


openrouter_provider = OpenRouterProvider(settings=settings)
