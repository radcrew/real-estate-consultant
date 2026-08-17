"""The fine-tuned Qwen2.5-0.5B criteria extractor, invoked as an AWS Lambda function.

Intake parse routes here and **only** here. A general model was never trained on the
extraction schema, so substituting one on failure would return a differently-shaped
answer that still validates — a silent wrong parse is worse than an honest error the
user can retry. Failure handling is therefore retry-then-degrade, never fall back.

The function is invoked over IAM (``lambda:Invoke``) rather than a Function URL, so
there is no public endpoint to secure.

Request payload::

    {"messages": [...], "schema_name": "LlmParseModelOutput",
     "max_tokens": 800, "temperature": 0.1}

Response payload::

    {"text": "<json matching schema_name>",
     "stop_reason": "stop" | "length",          # optional
     "usage": {"prompt_tokens": n, "completion_tokens": n}}   # optional

``messages`` keeps its ``system`` turn: the GGUF chat template renders roles itself, so
splitting the system prompt out would only force the handler to reassemble it.
"""

from __future__ import annotations

import json
import logging
import time
from functools import partial
from typing import Any

import anyio.to_thread
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.circuit_breaker import CircuitBreaker
from app.core.config import Settings, settings
from app.llm.providers.base import StructuredOutputT
from app.llm.providers.exceptions import (
    raise_qwen_access_denied,
    raise_qwen_circuit_open,
    raise_qwen_completion_parse_failed,
    raise_qwen_function_error,
    raise_qwen_invoke_failed,
    raise_qwen_not_configured,
    raise_qwen_rate_limited,
    raise_qwen_request_timeout,
    raise_qwen_structured_reply_incomplete,
)

QWEN_CONNECT_TIMEOUT = 10.0
# Must exceed the function's own timeout (~30s), or a read timeout fires while the model
# is still generating and the retry pays for a second inference of the same prompt.
QWEN_READ_TIMEOUT = 40.0
# One retry, no chaining (§3.3). Botocore's own retries are disabled below so this is the
# only one — layered retries turn a throttle into a thundering herd and hide the rate.
QWEN_RETRY_ATTEMPTS = 1

THROTTLING_CODES = frozenset({"TooManyRequestsException", "ThrottlingException"})
ACCESS_DENIED_CODES = frozenset({"AccessDeniedException", "UnrecognizedClientException"})
TIMEOUT_CODES = frozenset({"RequestTimeout", "RequestTimeoutException"})
NOT_FOUND_CODES = frozenset({"ResourceNotFoundException"})
# Lambda's own transient failures. Everything else — bad parameters, a conflicting
# update — is deterministic and must not be retried.
SERVICE_CODES = frozenset({"ServiceException", "EC2ThrottledException"})

RETRYABLE_CODES = THROTTLING_CODES | TIMEOUT_CODES | SERVICE_CODES

# Consecutive infrastructure failures before the breaker opens, and how long it then
# refuses calls. Long enough that a restarting environment is not hammered by traffic
# that would time out anyway; short enough that recovery is not user-visible for long.
QWEN_BREAKER_THRESHOLD = 5
QWEN_BREAKER_RESET_SECONDS = 30.0

logger = logging.getLogger(__name__)


def _error_code(exc: ClientError) -> str:
    return str(exc.response.get("Error", {}).get("Code", ""))


def is_transient(exc: ClientError | BotoCoreError) -> bool:
    """Whether one more attempt could plausibly succeed.

    Content failures are deliberately excluded: a schema violation retried is the same
    schema violation, bought twice.
    """
    if isinstance(exc, ClientError):
        return _error_code(exc) in RETRYABLE_CODES
    name = type(exc).__name__.lower()
    return "timeout" in name or "connection" in name


class QwenLambdaProvider:
    """Provider client for the fine-tuned Qwen2.5-0.5B function."""

    def __init__(
        self,
        *,
        settings: Settings,
        client: Any | None = None,
        breaker: CircuitBreaker | None = None,
    ) -> None:
        self.settings = settings
        self._client = client
        self._breaker = breaker or CircuitBreaker(
            failure_threshold=QWEN_BREAKER_THRESHOLD,
            reset_after_seconds=QWEN_BREAKER_RESET_SECONDS,
        )

    @property
    def client(self) -> Any:
        """Build the boto3 client on first use.

        boto3 raises when the region is blank, so an eagerly-built module-level client
        would fail at import time whenever ``AWS_REGION`` is unset. Callers reach this
        only after the configuration guard in ``generate_structured_output``.
        """
        if self._client is None:
            self._client = boto3.client(
                "lambda",
                region_name=self.settings.aws_region,
                config=Config(
                    connect_timeout=QWEN_CONNECT_TIMEOUT,
                    read_timeout=QWEN_READ_TIMEOUT,
                    # Retry policy lives in this module, where it can be logged.
                    retries={"max_attempts": 1, "mode": "standard"},
                ),
            )
        return self._client

    def _log_call(
        self,
        *,
        outcome: str,
        duration_ms: float,
        usage: dict[str, Any] | None = None,
        retry_used: bool = False,
    ) -> None:
        prompt_tokens = usage.get("prompt_tokens") if usage else None
        completion_tokens = usage.get("completion_tokens") if usage else None
        total_tokens = None
        if prompt_tokens is not None:
            total_tokens = prompt_tokens + (completion_tokens or 0)
        logger.info(
            "llm_call",
            extra={
                "provider": "qwen",
                "model": self.settings.qwen_inference_function_name,
                "model_version": self.settings.qwen_model_version,
                "outcome": outcome,
                "duration_ms": round(duration_ms, 2),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": None,
                "retry_used": retry_used,
            },
        )

    def _build_payload(
        self,
        *,
        messages: list[dict[str, Any]],
        response_format: type[StructuredOutputT],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Build the function's request payload.

        ``schema_name`` selects a GBNF grammar compiled into the image at build time, so
        the decoder cannot emit invalid JSON in the first place. ``temperature`` *is*
        forwarded — Qwen honours it, unlike the Anthropic path which must drop it.
        """
        return {
            "messages": messages,
            "schema_name": response_format.__name__,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

    def _invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Blocking ``lambda:Invoke`` — always run via ``anyio.to_thread``."""
        response = self.client.invoke(
            FunctionName=self.settings.qwen_inference_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload).encode(),
        )
        # A handler that raised still returns HTTP 200; only FunctionError distinguishes
        # it. Skip this check and a stack trace gets parsed as though it were a reply.
        if response.get("FunctionError"):
            raise_qwen_function_error()
        try:
            body = json.loads(response["Payload"].read())
        except (json.JSONDecodeError, KeyError, UnicodeDecodeError):
            raise_qwen_structured_reply_incomplete()
        return body if isinstance(body, dict) else {}

    async def _invoke_with_retry(
        self, payload: dict[str, Any], *, start: float
    ) -> tuple[dict[str, Any], bool]:
        """Invoke, retrying once on a transient failure (§3.3).

        Returns the decoded payload and whether the retry was used, so the caller can
        record it on the ``llm_call`` line — a retry rate that climbs unnoticed is how a
        broken function stays broken for a week.
        """
        retry_used = False
        for attempt in range(QWEN_RETRY_ATTEMPTS + 1):
            try:
                # boto3 is synchronous; never block the event loop with it.
                result = await anyio.to_thread.run_sync(partial(self._invoke, payload))
                return result, retry_used
            except (ClientError, BotoCoreError) as exc:
                if attempt < QWEN_RETRY_ATTEMPTS and is_transient(exc):
                    retry_used = True
                    logger.warning(
                        "qwen_invoke_retry",
                        extra={"reason": type(exc).__name__},
                    )
                    continue
                self._raise_for_error(exc, start=start, retry_used=retry_used)

    async def generate_structured_output(
        self,
        *,
        messages: list[dict[str, Any]],
        response_format: type[StructuredOutputT],
        temperature: float,
        max_tokens: int,
        # Accepted for the ``ChatProvider`` contract, not used here. ``base_url`` /
        # ``api_key`` / ``model`` pin one call to an OpenAI-compatible endpoint, which
        # this provider is not, and ``chat.py`` routes a pinned call to the Hugging Face
        # provider rather than here. Declared so every provider satisfies one signature
        # rather than the caller having to know which accepts what.
        include_schema_instruction: bool = True,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> StructuredOutputT:
        """Return a typed structured output from the Qwen function."""
        if not self.settings.aws_region.strip():
            raise_qwen_not_configured()
        if not self.settings.qwen_inference_function_name.strip():
            raise_qwen_not_configured()

        payload = self._build_payload(
            messages=messages,
            response_format=response_format,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if not self._breaker.allow():
            # Fail fast rather than queue an invocation that recent evidence says will
            # time out — the wait would be paid by the user and buy nothing.
            self._log_call(outcome="circuit_open", duration_ms=0.0)
            raise_qwen_circuit_open()

        start = time.perf_counter()
        try:
            raw, retry_used = await self._invoke_with_retry(payload, start=start)
        except HTTPException:
            self._breaker.record_failure()
            raise
        # Recorded before parsing: a reply that arrived and then failed validation proves
        # the function is healthy, so content errors must never trip the breaker.
        self._breaker.record_success()
        duration_ms = (time.perf_counter() - start) * 1000

        usage = raw.get("usage") if isinstance(raw.get("usage"), dict) else None
        text = raw.get("text")
        if not isinstance(text, str) or not text.strip() or raw.get("stop_reason") == "length":
            # Either nothing came back, or generation hit max_tokens mid-object. The
            # grammar guarantees shape, not that the model finished saying it.
            self._log_call(
                outcome="incomplete",
                duration_ms=duration_ms,
                usage=usage,
                retry_used=retry_used,
            )
            raise_qwen_structured_reply_incomplete()

        try:
            parsed = response_format.model_validate_json(text)
        except ValidationError as exc:
            # The grammar guarantees valid JSON of the right shape; it cannot guarantee
            # the values make sense, which is why this validation still runs.
            self._log_call(
                outcome="parse_failed",
                duration_ms=duration_ms,
                usage=usage,
                retry_used=retry_used,
            )
            raise_qwen_completion_parse_failed(cause=exc)

        self._log_call(
            outcome="success", duration_ms=duration_ms, usage=usage, retry_used=retry_used
        )
        return parsed

    def _raise_for_error(
        self,
        exc: ClientError | BotoCoreError,
        *,
        start: float,
        retry_used: bool,
    ) -> None:
        duration_ms = (time.perf_counter() - start) * 1000
        if isinstance(exc, ClientError):
            code = _error_code(exc)
            if code in THROTTLING_CODES:
                self._log_call(
                    outcome="rate_limited", duration_ms=duration_ms, retry_used=retry_used
                )
                raise_qwen_rate_limited(cause=exc)
            if code in ACCESS_DENIED_CODES:
                self._log_call(
                    outcome="access_denied", duration_ms=duration_ms, retry_used=retry_used
                )
                raise_qwen_access_denied(cause=exc)
            if code in NOT_FOUND_CODES:
                self._log_call(
                    outcome="not_configured", duration_ms=duration_ms, retry_used=retry_used
                )
                raise_qwen_not_configured()
            if code in TIMEOUT_CODES:
                self._log_call(outcome="timeout", duration_ms=duration_ms, retry_used=retry_used)
                raise_qwen_request_timeout(cause=exc)
            self._log_call(outcome="error", duration_ms=duration_ms, retry_used=retry_used)
            raise_qwen_invoke_failed(cause=exc)

        if "timeout" in type(exc).__name__.lower():
            self._log_call(outcome="timeout", duration_ms=duration_ms, retry_used=retry_used)
            raise_qwen_request_timeout(cause=exc)
        self._log_call(outcome="error", duration_ms=duration_ms, retry_used=retry_used)
        raise_qwen_invoke_failed(cause=exc)


qwen_lambda_provider = QwenLambdaProvider(settings=settings)
