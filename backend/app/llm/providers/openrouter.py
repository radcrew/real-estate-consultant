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
    ) -> None:
        cost_usd = None
        if usage is not None:
            cost_usd = round(
                (
                    usage.prompt_tokens * self.settings.openrouter_input_cost_per_1m
                    + usage.completion_tokens * self.settings.openrouter_output_cost_per_1m
                )
                / 1_000_000,
                6,
            )
        logger.info(
            "llm_call",
            extra={
                "provider": "openrouter",
                "model": self.settings.openrouter_chat_model,
                "outcome": outcome,
                "duration_ms": round(duration_ms, 2),
                "prompt_tokens": usage.prompt_tokens if usage else None,
                "completion_tokens": usage.completion_tokens if usage else None,
                "total_tokens": usage.total_tokens if usage else None,
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
    ) -> StructuredOutputT:
        """Request a typed structured output from OpenRouter."""
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


openrouter_provider = OpenRouterProvider(settings=settings)
