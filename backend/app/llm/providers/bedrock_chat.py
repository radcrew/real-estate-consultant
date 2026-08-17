"""AWS Bedrock chat provider built on the Anthropic SDK's Messages API client."""

from __future__ import annotations

import logging
import time
from typing import Any, TypeVar

import httpx
from anthropic import (
    AnthropicError,
    APITimeoutError,
    AsyncAnthropicBedrockMantle,
    PermissionDeniedError,
    RateLimitError,
)
from anthropic.types import Usage
from pydantic import BaseModel, ValidationError

from app.core.config import Settings, settings
from app.llm.providers.exceptions import (
    raise_bedrock_access_denied,
    raise_bedrock_api_error,
    raise_bedrock_completion_parse_failed,
    raise_bedrock_not_configured,
    raise_bedrock_rate_limited,
    raise_bedrock_request_timeout,
    raise_bedrock_structured_refusal,
    raise_bedrock_structured_reply_incomplete,
)

BR_CONNECT_TIMEOUT = 20.0
BR_READ_TIMEOUT = 75.0
BR_WRITE_TIMEOUT = 30.0
BR_POOL_TIMEOUT = 10.0
BR_TRANSIENT_RETRIES = 3

logger = logging.getLogger(__name__)

StructuredOutputT = TypeVar("StructuredOutputT", bound=BaseModel)


def split_system_prompt(messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    """Split ``system`` turns out of ``messages``.

    Callers build OpenAI-style message lists that lead with a ``system`` role, but the
    Messages API takes the system prompt as a top-level parameter instead.
    """
    system_parts = [
        str(message["content"])
        for message in messages
        if message.get("role") == "system" and message.get("content")
    ]
    turns = [message for message in messages if message.get("role") != "system"]
    return "\n\n".join(system_parts), turns


class BedrockChatProvider:
    """Provider client for Claude chat completions on Amazon Bedrock."""

    def __init__(
        self,
        *,
        settings: Settings,
        timeout: httpx.Timeout | None = None,
        transient_retries: int = BR_TRANSIENT_RETRIES,
        client: AsyncAnthropicBedrockMantle | None = None,
    ) -> None:
        self.settings = settings
        self.timeout = timeout or httpx.Timeout(
            connect=BR_CONNECT_TIMEOUT,
            read=BR_READ_TIMEOUT,
            write=BR_WRITE_TIMEOUT,
            pool=BR_POOL_TIMEOUT,
        )
        self.transient_retries = transient_retries
        # An unset region builds an unusable base URL rather than raising, so the real
        # guard is the aws_region check in generate_structured_output.
        self.client = client or AsyncAnthropicBedrockMantle(
            aws_region=settings.aws_region,
            timeout=self.timeout,
            max_retries=transient_retries,
        )

    def _log_call(
        self,
        *,
        outcome: str,
        duration_ms: float,
        usage: Usage | None = None,
        model: str | None = None,
    ) -> None:
        cost_usd = None
        prompt_tokens = getattr(usage, "input_tokens", None) if usage is not None else None
        completion_tokens = getattr(usage, "output_tokens", None) if usage is not None else None
        cache_read_tokens = (
            getattr(usage, "cache_read_input_tokens", None) if usage is not None else None
        )
        total_tokens = None
        if prompt_tokens is not None:
            completion_for_cost = completion_tokens or 0
            total_tokens = prompt_tokens + completion_for_cost
            cost_usd = round(
                (
                    prompt_tokens * self.settings.bedrock_input_cost_per_1m
                    + completion_for_cost * self.settings.bedrock_output_cost_per_1m
                )
                / 1_000_000,
                6,
            )
        logger.info(
            "llm_call",
            extra={
                "provider": "bedrock",
                "model": model or self.settings.bedrock_chat_model,
                "outcome": outcome,
                "duration_ms": round(duration_ms, 2),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cache_read_input_tokens": cache_read_tokens,
                "estimated_cost_usd": cost_usd,
            },
        )

    def _build_request(
        self,
        *,
        messages: list[dict[str, Any]],
        response_format: type[StructuredOutputT],
        max_tokens: int,
    ) -> dict[str, Any]:
        """Build ``messages.parse`` kwargs.

        ``temperature`` is deliberately dropped: Claude 4.7+ rejects it outright and
        Sonnet 5 rejects non-default values, so forwarding the caller's value would turn
        every request into a 400. Determinism is steered by the prompt and by effort.
        """
        system_prompt, turns = split_system_prompt(messages)
        request: dict[str, Any] = {
            "model": self.settings.bedrock_chat_model,
            "max_tokens": max_tokens,
            "messages": turns,
            "output_format": response_format,
            "output_config": {"effort": self.settings.bedrock_effort},
        }
        if system_prompt:
            request["system"] = system_prompt
        if self.settings.bedrock_disable_thinking:
            # Rejected above effort "high" on Opus 5; the configured default is "low".
            request["thinking"] = {"type": "disabled"}
        else:
            request["thinking"] = {"type": "adaptive"}
        return request

    async def generate_structured_output(
        self,
        *,
        messages: list[dict[str, Any]],
        response_format: type[StructuredOutputT],
        temperature: float,
        max_tokens: int,
    ) -> StructuredOutputT:
        """Request a typed structured output from Bedrock. ``temperature`` is ignored."""
        if not self.settings.aws_region.strip():
            raise_bedrock_not_configured()

        request = self._build_request(
            messages=messages,
            response_format=response_format,
            max_tokens=max_tokens,
        )

        start = time.perf_counter()
        try:
            completion = await self.client.messages.parse(**request)
        except ValidationError as exc:
            self._log_call(outcome="parse_failed", duration_ms=(time.perf_counter() - start) * 1000)
            raise_bedrock_completion_parse_failed(cause=exc)
        except APITimeoutError as exc:
            self._log_call(outcome="timeout", duration_ms=(time.perf_counter() - start) * 1000)
            raise_bedrock_request_timeout(cause=exc)
        except RateLimitError as exc:
            self._log_call(outcome="rate_limited", duration_ms=(time.perf_counter() - start) * 1000)
            raise_bedrock_rate_limited(cause=exc)
        except PermissionDeniedError as exc:
            self._log_call(
                outcome="access_denied", duration_ms=(time.perf_counter() - start) * 1000
            )
            raise_bedrock_access_denied(cause=exc)
        except AnthropicError as exc:
            self._log_call(outcome="error", duration_ms=(time.perf_counter() - start) * 1000)
            raise_bedrock_api_error(cause=exc)

        duration_ms = (time.perf_counter() - start) * 1000
        usage = getattr(completion, "usage", None)
        if completion.stop_reason == "refusal":
            self._log_call(outcome="refusal", duration_ms=duration_ms, usage=usage)
            raise_bedrock_structured_refusal(refusal=_refusal_reason(completion))
        parsed = completion.parsed_output
        if completion.stop_reason == "max_tokens" or parsed is None:
            self._log_call(outcome="incomplete", duration_ms=duration_ms, usage=usage)
            raise_bedrock_structured_reply_incomplete()
        self._log_call(outcome="success", duration_ms=duration_ms, usage=usage)
        return parsed


def _refusal_reason(completion: Any) -> str:
    """``stop_details`` is only populated on refusals, and may still be ``None``."""
    details = getattr(completion, "stop_details", None)
    return str(getattr(details, "explanation", None) or "refused")


bedrock_chat_provider = BedrockChatProvider(settings=settings)
