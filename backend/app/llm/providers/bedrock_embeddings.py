"""AWS Bedrock embeddings provider built on ``bedrock-runtime`` ``InvokeModel``."""

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

from app.core.config import Settings, settings
from app.llm.providers.exceptions import (
    raise_bedrock_access_denied,
    raise_bedrock_api_error,
    raise_bedrock_not_configured,
    raise_bedrock_rate_limited,
    raise_bedrock_request_timeout,
)
from app.utils.exceptions import raise_bad_gateway

BR_CONNECT_TIMEOUT = 20.0
BR_READ_TIMEOUT = 75.0
BR_TRANSIENT_RETRIES = 3

# Botocore error codes that mean "retry later" rather than "this request was wrong".
THROTTLING_CODES = frozenset({"ThrottlingException", "TooManyRequestsException"})
ACCESS_DENIED_CODES = frozenset({"AccessDeniedException", "UnrecognizedClientException"})
TIMEOUT_CODES = frozenset({"ModelTimeoutException", "RequestTimeout", "RequestTimeoutException"})

logger = logging.getLogger(__name__)


def chunked(texts: list[str], size: int) -> list[list[str]]:
    """Split ``texts`` into ``size``-length chunks, preserving order."""
    step = max(1, size)
    return [texts[index : index + step] for index in range(0, len(texts), step)]


class BedrockEmbeddingsProvider:
    """Provider client for Cohere Embed v3 text embeddings on Amazon Bedrock.

    Only the Cohere request/response shape is supported. Titan embeds a single text per
    call, so it would need a fan-out request path rather than a different body.
    """

    def __init__(
        self,
        *,
        settings: Settings,
        client: Any | None = None,
    ) -> None:
        self.settings = settings
        self._client = client

    @property
    def client(self) -> Any:
        """Build the boto3 client on first use.

        boto3 raises when the region is blank, so an eagerly-built module-level client
        would fail at import time whenever ``AWS_REGION`` is unset. Callers reach this
        only after the region guard in ``embed``.
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

    def _log_call(self, *, outcome: str, duration_ms: float, texts: int | None = None) -> None:
        logger.info(
            "llm_call",
            extra={
                "provider": "bedrock",
                "model": self.settings.bedrock_embedding_model,
                "outcome": outcome,
                "duration_ms": round(duration_ms, 2),
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
                "estimated_cost_usd": None,
                "embedded_texts": texts,
            },
        )

    def _invoke(self, chunk: list[str]) -> list[list[float]]:
        """Blocking ``InvokeModel`` call — always run via ``anyio.to_thread``."""
        response = self.client.invoke_model(
            modelId=self.settings.bedrock_embedding_model,
            body=json.dumps({"texts": chunk, "input_type": "search_document"}),
            accept="application/json",
            contentType="application/json",
        )
        payload = json.loads(response["body"].read())
        return _parse_embeddings(payload, expected=len(chunk))

    async def embed(self, *, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text, in input order."""
        if not texts:
            return []
        if not self.settings.aws_region.strip():
            raise_bedrock_not_configured()

        vectors: list[list[float]] = []
        start = time.perf_counter()
        for chunk in chunked(texts, self.settings.bedrock_embedding_batch_size):
            try:
                # boto3 is synchronous; never block the event loop with it.
                vectors.extend(await anyio.to_thread.run_sync(partial(self._invoke, chunk)))
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
        if len(vectors) != len(texts):
            self._log_call(outcome="count_mismatch", duration_ms=duration_ms, texts=len(texts))
            raise_bad_gateway(
                "Bedrock embedding count did not match the number of input texts.",
            )
        self._log_call(outcome="success", duration_ms=duration_ms, texts=len(texts))
        return vectors

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


def _parse_embeddings(payload: object, *, expected: int) -> list[list[float]]:
    """Read Cohere Embed v3's ``{"embeddings": [[float, …], …]}`` response body."""
    if not isinstance(payload, dict):
        raise_bad_gateway("Bedrock returned an unexpected embedding response.")
    raw = payload.get("embeddings")
    # Cohere returns {"embeddings": {"float": [[...]]}} when embedding_types is set.
    if isinstance(raw, dict):
        raw = raw.get("float")
    if not isinstance(raw, list) or not raw:
        raise_bad_gateway("Bedrock returned an empty embedding response.")
    vectors = [[float(value) for value in row] for row in raw if isinstance(row, list)]
    if len(vectors) != expected:
        raise_bad_gateway(
            "Bedrock embedding count did not match the number of input texts.",
        )
    return vectors


bedrock_embeddings_provider = BedrockEmbeddingsProvider(settings=settings)
