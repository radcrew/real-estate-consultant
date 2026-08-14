"""Qwen chat on Amazon Bedrock, via the boto3 ``Converse`` API.

``BedrockChatProvider`` cannot serve these models: it is built on the Anthropic SDK,
which speaks only to Anthropic models. Converse is Bedrock's vendor-neutral chat API, so
it is what a Qwen route has to use — and it has no ``messages.parse`` equivalent, so
structured output arrives through a tool call the model is forced to make.
"""

from __future__ import annotations

import logging
import time
from functools import partial
from typing import Any

import anyio.to_thread
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.llm.providers.base import StructuredOutputT
from app.llm.providers.bedrock_chat import split_system_prompt
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
BR_TRANSIENT_RETRIES = 3

# Botocore error codes that mean "retry later" rather than "this request was wrong".
THROTTLING_CODES = frozenset(
    {"ThrottlingException", "TooManyRequestsException", "ServiceQuotaExceededException"}
)
ACCESS_DENIED_CODES = frozenset({"AccessDeniedException", "UnrecognizedClientException"})
TIMEOUT_CODES = frozenset({"ModelTimeoutException", "RequestTimeout", "RequestTimeoutException"})

# Bedrock stops with these when a policy blocked the reply rather than the model finishing.
REFUSAL_STOP_REASONS = frozenset({"content_filtered", "guardrail_intervened"})

# The single tool the model is forced to call. Its input schema is the caller's Pydantic
# model, which is how a text-completion API is made to return a validated object.
STRUCTURED_OUTPUT_TOOL = "emit_structured_output"

logger = logging.getLogger(__name__)


def to_converse_messages(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert OpenAI-style ``{"role", "content"}`` turns to Converse content blocks."""
    converted: list[dict[str, Any]] = []
    for turn in turns:
        content = turn.get("content")
        if isinstance(content, list):
            blocks = content
        else:
            blocks = [{"text": str(content)}]
        converted.append({"role": turn.get("role", "user"), "content": blocks})
    return converted


class BedrockQwenChatProvider:
    """Provider client for Qwen chat completions on Amazon Bedrock (Converse API)."""

    def __init__(self, *, settings: Settings, client: Any | None = None) -> None:
        self.settings = settings
        self._client = client

    @property
    def client(self) -> Any:
        """Build the boto3 client on first use.

        boto3 raises when the region is blank, so an eagerly-built module-level client
        would fail at import time whenever ``AWS_REGION`` is unset. Callers reach this
        only after the region guard in ``generate_structured_output``.
        """
        if self._client is None:
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=self.settings.aws_region,
                config=Config(
                    connect_timeout=BR_CONNECT_TIMEOUT,
                    read_timeout=BR_READ_TIMEOUT,
                    retries={"max_attempts": BR_TRANSIENT_RETRIES, "mode": "standard"},
                ),
            )
        return self._client

    def _log_call(
        self,
        *,
        outcome: str,
        duration_ms: float,
        usage: dict[str, Any] | None = None,
    ) -> None:
        prompt_tokens = usage.get("inputTokens") if usage else None
        completion_tokens = usage.get("outputTokens") if usage else None
        total_tokens = usage.get("totalTokens") if usage else None
        cost_usd = None
        if prompt_tokens is not None:
            cost_usd = round(
                (
                    prompt_tokens * self.settings.bedrock_qwen_input_cost_per_1m
                    + (completion_tokens or 0) * self.settings.bedrock_qwen_output_cost_per_1m
                )
                / 1_000_000,
                6,
            )
        logger.info(
            "llm_call",
            extra={
                "provider": "bedrock_qwen",
                "model": self.settings.bedrock_qwen_chat_model,
                "outcome": outcome,
                "duration_ms": round(duration_ms, 2),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": cost_usd,
            },
        )

    def _build_request(
        self,
        *,
        messages: list[dict[str, Any]],
        response_format: type[StructuredOutputT],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Build ``converse`` kwargs.

        ``temperature`` *is* forwarded here, unlike the Anthropic provider which must drop
        it. That asymmetry is why routing is per call site rather than per process.
        """
        system_prompt, turns = split_system_prompt(messages)
        request: dict[str, Any] = {
            "modelId": self.settings.bedrock_qwen_chat_model,
            "messages": to_converse_messages(turns),
            "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature},
            "toolConfig": {
                "tools": [
                    {
                        "toolSpec": {
                            "name": STRUCTURED_OUTPUT_TOOL,
                            "description": (
                                response_format.__doc__ or "Return the structured response."
                            ).strip(),
                            "inputSchema": {"json": response_format.model_json_schema()},
                        }
                    }
                ],
                # Forcing the tool is what makes the reply parseable: left to its own
                # choice the model may answer in prose, which no schema can rescue.
                "toolChoice": {"tool": {"name": STRUCTURED_OUTPUT_TOOL}},
            },
        }
        if system_prompt:
            request["system"] = [{"text": system_prompt}]
        if self.settings.bedrock_qwen_disable_thinking:
            # Qwen3 is a hybrid-thinking family and thinking is billed against maxTokens
            # for no benefit on a structured draft. The switch is model-revision specific,
            # so BEDROCK_QWEN_DISABLE_THINKING=false omits the field entirely if a
            # revision rejects it.
            request["additionalModelRequestFields"] = {"enable_thinking": False}
        return request

    async def generate_structured_output(
        self,
        *,
        messages: list[dict[str, Any]],
        response_format: type[StructuredOutputT],
        temperature: float,
        max_tokens: int,
    ) -> StructuredOutputT:
        """Request a typed structured output from a Qwen model on Bedrock."""
        if not self.settings.aws_region.strip():
            raise_bedrock_not_configured()

        request = self._build_request(
            messages=messages,
            response_format=response_format,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        start = time.perf_counter()
        try:
            # boto3 is synchronous; never block the event loop with it.
            response = await anyio.to_thread.run_sync(partial(self._converse, request))
        except ClientError as exc:
            self._raise_for_client_error(exc, start=start)
        except BotoCoreError as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            if "timeout" in type(exc).__name__.lower():
                self._log_call(outcome="timeout", duration_ms=duration_ms)
                raise_bedrock_request_timeout(cause=exc)
            self._log_call(outcome="error", duration_ms=duration_ms)
            raise_bedrock_api_error(cause=exc)

        duration_ms = (time.perf_counter() - start) * 1000
        usage = response.get("usage") if isinstance(response, dict) else None
        stop_reason = str(response.get("stopReason", "")) if isinstance(response, dict) else ""

        if stop_reason in REFUSAL_STOP_REASONS:
            self._log_call(outcome="refusal", duration_ms=duration_ms, usage=usage)
            raise_bedrock_structured_refusal(refusal=stop_reason)

        tool_input = _extract_tool_input(response)
        if stop_reason == "max_tokens" or tool_input is None:
            # A truncated reply loses the tool block, and a model that answered in prose
            # never produced one: both mean there is no structured output to return.
            self._log_call(outcome="incomplete", duration_ms=duration_ms, usage=usage)
            raise_bedrock_structured_reply_incomplete()

        try:
            parsed = response_format.model_validate(tool_input)
        except ValidationError as exc:
            self._log_call(outcome="parse_failed", duration_ms=duration_ms, usage=usage)
            raise_bedrock_completion_parse_failed(cause=exc)

        self._log_call(outcome="success", duration_ms=duration_ms, usage=usage)
        return parsed

    def _converse(self, request: dict[str, Any]) -> dict[str, Any]:
        """Blocking ``Converse`` call — always run via ``anyio.to_thread``."""
        return self.client.converse(**request)

    def _raise_for_client_error(self, exc: ClientError, *, start: float) -> None:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        duration_ms = (time.perf_counter() - start) * 1000
        if code in THROTTLING_CODES:
            self._log_call(outcome="rate_limited", duration_ms=duration_ms)
            raise_bedrock_rate_limited(cause=exc)
        if code in ACCESS_DENIED_CODES:
            self._log_call(outcome="access_denied", duration_ms=duration_ms)
            raise_bedrock_access_denied(cause=exc)
        if code in TIMEOUT_CODES:
            self._log_call(outcome="timeout", duration_ms=duration_ms)
            raise_bedrock_request_timeout(cause=exc)
        self._log_call(outcome="error", duration_ms=duration_ms)
        raise_bedrock_api_error(cause=exc)


def _extract_tool_input(response: object) -> dict[str, Any] | None:
    """Return the forced tool call's input, or ``None`` when the model made none."""
    if not isinstance(response, dict):
        return None
    content = response.get("output", {}).get("message", {}).get("content")
    if not isinstance(content, list):
        return None
    for block in content:
        if not isinstance(block, dict):
            continue
        tool_use = block.get("toolUse")
        if isinstance(tool_use, dict) and tool_use.get("name") == STRUCTURED_OUTPUT_TOOL:
            tool_input = tool_use.get("input")
            return tool_input if isinstance(tool_input, dict) else None
    return None


bedrock_qwen_chat_provider = BedrockQwenChatProvider(settings=settings)
