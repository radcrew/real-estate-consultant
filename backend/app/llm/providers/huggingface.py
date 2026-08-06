"""Hugging Face provider wrapper built on the OpenAI Python SDK."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, TypeVar

import httpx
from openai import APITimeoutError, AsyncOpenAI, OpenAIError
from openai.types.completion_usage import CompletionUsage
from pydantic import BaseModel, ValidationError

from app.core.config import Settings, settings
from app.llm.providers.exceptions import (
    raise_hf_api_key_not_configured,
    raise_hf_completion_parse_failed,
    raise_hf_openai_error,
    raise_hf_request_timeout,
    raise_hf_structured_refusal,
    raise_hf_structured_reply_incomplete,
)
from app.utils.exceptions import raise_bad_gateway, raise_gateway_timeout

HF_CONNECT_TIMEOUT = 20.0
HF_READ_TIMEOUT = 75.0
HF_WRITE_TIMEOUT = 30.0
HF_POOL_TIMEOUT = 10.0
HF_TRANSIENT_RETRIES = 3

_JSON_FENCE_RE = re.compile(
    r"```(?:json)?\s*([\s\S]*?)\s*```",
    re.IGNORECASE,
)

logger = logging.getLogger(__name__)

StructuredOutputT = TypeVar("StructuredOutputT", bound=BaseModel)


def structured_output_messages(
    *,
    messages: list[dict[str, Any]],
    response_format: type[BaseModel],
) -> list[dict[str, Any]]:
    """Prepend the schema instruction the provider sends with every structured request.

    Module-level so ``ml/eval`` can reproduce the exact request without reaching into
    the provider or restating the instruction.
    """
    schema = response_format.model_json_schema()
    instruction = (
        "Respond with a single JSON object that validates against this JSON Schema. "
        "Do not wrap the JSON in markdown fences or add commentary.\n"
        f"{json.dumps(schema, ensure_ascii=True)}"
    )
    return [{"role": "system", "content": instruction}, *messages]


class HuggingFaceProvider:
    """Provider client for Hugging Face OpenAI-compatible chat completions."""

    def __init__(
        self,
        *,
        settings: Settings,
        timeout: httpx.Timeout | None = None,
        transient_retries: int = HF_TRANSIENT_RETRIES,
        client: AsyncOpenAI | None = None,
    ) -> None:
        self.settings = settings
        self.timeout = timeout or httpx.Timeout(
            connect=HF_CONNECT_TIMEOUT,
            read=HF_READ_TIMEOUT,
            write=HF_WRITE_TIMEOUT,
            pool=HF_POOL_TIMEOUT,
        )
        self.transient_retries = transient_retries
        self.client = client or AsyncOpenAI(
            api_key=settings.hf_token or "missing-huggingface-api-key",
            base_url=settings.hf_base_url,
            timeout=self.timeout,
            max_retries=transient_retries,
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
                    prompt_tokens * self.settings.hf_input_cost_per_1m
                    + completion_for_cost * self.settings.hf_output_cost_per_1m
                )
                / 1_000_000,
                6,
            )
        logger.info(
            "llm_call",
            extra={
                "provider": "huggingface",
                "model": model or self.settings.hf_model,
                "outcome": outcome,
                "duration_ms": round(duration_ms, 2),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": cost_usd,
            },
        )

    @staticmethod
    def _extract_json_object(text: str) -> str:
        """Pull a JSON object out of model text (raw or fenced)."""
        stripped = text.strip()
        if not stripped:
            return stripped
        fenced = _JSON_FENCE_RE.search(stripped)
        if fenced:
            return fenced.group(1).strip()
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            return stripped[start : end + 1]
        return stripped

    def _structured_messages(
        self,
        *,
        messages: list[dict[str, Any]],
        response_format: type[BaseModel],
    ) -> list[dict[str, Any]]:
        return structured_output_messages(
            messages=messages,
            response_format=response_format,
        )

    async def generate_structured_output(
        self,
        *,
        messages: list[dict[str, Any]],
        response_format: type[StructuredOutputT],
        temperature: float,
        max_tokens: int,
    ) -> StructuredOutputT:
        """Request typed JSON from Hugging Face and validate with Pydantic.

        Avoids ``beta.chat.completions.parse`` / grammar-constrained structured
        outputs: HF Inference Providers often return 422
        ``grammar is not valid: failed to compile grammar`` depending on which
        upstream provider the router selects for the same model id.
        """
        if not self.settings.hf_token.strip():
            raise_hf_api_key_not_configured()

        request_messages = self._structured_messages(
            messages=messages,
            response_format=response_format,
        )
        start = time.perf_counter()
        try:
            try:
                completion = await self.client.chat.completions.create(
                    model=self.settings.hf_model,
                    messages=request_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"},
                )
            except APITimeoutError:
                raise
            except OpenAIError as json_mode_exc:
                # Some router backends reject json_object; retry unconstrained.
                status = getattr(json_mode_exc, "status_code", None)
                if status not in {400, 404, 422}:
                    raise
                completion = await self.client.chat.completions.create(
                    model=self.settings.hf_model,
                    messages=request_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
        except APITimeoutError as exc:
            self._log_call(outcome="timeout", duration_ms=(time.perf_counter() - start) * 1000)
            raise_hf_request_timeout(cause=exc)
        except OpenAIError as exc:
            self._log_call(outcome="error", duration_ms=(time.perf_counter() - start) * 1000)
            raise_hf_openai_error(cause=exc)

        duration_ms = (time.perf_counter() - start) * 1000
        message = completion.choices[0].message
        if message.refusal:
            self._log_call(outcome="refusal", duration_ms=duration_ms, usage=completion.usage)
            raise_hf_structured_refusal(refusal=str(message.refusal))
        content = (message.content or "").strip()
        if not content:
            self._log_call(outcome="incomplete", duration_ms=duration_ms, usage=completion.usage)
            raise_hf_structured_reply_incomplete()

        try:
            parsed = response_format.model_validate_json(self._extract_json_object(content))
        except ValidationError as exc:
            self._log_call(outcome="parse_failed", duration_ms=duration_ms, usage=completion.usage)
            raise_hf_completion_parse_failed(cause=exc)
        except (json.JSONDecodeError, ValueError) as exc:
            self._log_call(outcome="parse_failed", duration_ms=duration_ms, usage=completion.usage)
            raise_bad_gateway(
                "We couldn't process the assistant's reply. Please try again in a moment.",
                cause=exc,
            )

        self._log_call(outcome="success", duration_ms=duration_ms, usage=completion.usage)
        return parsed

    def _feature_extraction_url(self) -> str:
        """HF OpenAI router (`…/v1`) is chat-only; embeddings use feature-extraction."""
        root = self.settings.hf_base_url.rstrip("/").removesuffix("/v1")
        model = self.settings.hf_embedding_model.strip().strip("/")
        return f"{root}/hf-inference/models/{model}/pipeline/feature-extraction"

    @staticmethod
    def _normalize_feature_extraction(
        payload: object,
        *,
        expected: int,
    ) -> list[list[float]]:
        """Normalize HF feature-extraction JSON into one float vector per input text."""
        if not isinstance(payload, list) or not payload:
            raise_bad_gateway("Hugging Face returned an empty embedding response.")

        first = payload[0]
        # Single sentence vector: [float, …]
        if isinstance(first, (int, float)):
            vectors = [[float(x) for x in payload]]
        # Batch of sentence vectors: [[float, …], …]
        elif isinstance(first, list) and first and isinstance(first[0], (int, float)):
            vectors = [[float(x) for x in row] for row in payload if isinstance(row, list)]
        # Token-level embeddings: [[[float, …], …], …] — mean-pool each sequence
        elif isinstance(first, list) and first and isinstance(first[0], list):
            vectors = []
            for sequence in payload:
                if not isinstance(sequence, list) or not sequence:
                    continue
                width = len(sequence[0]) if isinstance(sequence[0], list) else 0
                if width == 0:
                    continue
                sums = [0.0] * width
                count = 0
                for token in sequence:
                    if not isinstance(token, list) or len(token) != width:
                        continue
                    for i, value in enumerate(token):
                        sums[i] += float(value)
                    count += 1
                if count:
                    vectors.append([value / count for value in sums])
        else:
            raise_bad_gateway("Hugging Face returned an unexpected embedding shape.")

        if len(vectors) != expected:
            raise_bad_gateway(
                "Hugging Face embedding count did not match the number of input texts.",
            )
        return vectors

    async def embed(self, *, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text via HF feature-extraction.

        ``router.huggingface.co/v1`` is chat-completions only; sentence embeddings
        go through ``/hf-inference/models/.../pipeline/feature-extraction``.
        """
        if not texts:
            return []
        if not self.settings.hf_token.strip():
            raise_hf_api_key_not_configured()

        url = self._feature_extraction_url()
        headers = {
            "Authorization": f"Bearer {self.settings.hf_token.strip()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json={"inputs": texts})
                response.raise_for_status()
                payload = response.json()
        except httpx.TimeoutException as exc:
            self._log_call(
                outcome="timeout",
                duration_ms=(time.perf_counter() - start) * 1000,
                model=self.settings.hf_embedding_model,
            )
            raise_gateway_timeout("Timed out while calling Hugging Face API.", cause=exc)
        except httpx.HTTPError as exc:
            self._log_call(
                outcome="error",
                duration_ms=(time.perf_counter() - start) * 1000,
                model=self.settings.hf_embedding_model,
            )
            raise_bad_gateway(
                "The AI service is temporarily unavailable. Please try again later.",
                cause=exc,
            )

        vectors = self._normalize_feature_extraction(payload, expected=len(texts))
        duration_ms = (time.perf_counter() - start) * 1000
        self._log_call(
            outcome="success",
            duration_ms=duration_ms,
            model=self.settings.hf_embedding_model,
        )
        return vectors


huggingface_provider = HuggingFaceProvider(settings=settings)
