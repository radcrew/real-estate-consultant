"""Hugging Face provider wrapper built on the OpenAI Python SDK."""

from __future__ import annotations

from typing import Any, TypeVar

import httpx
from openai import APITimeoutError, AsyncOpenAI, OpenAIError
from pydantic import BaseModel, ValidationError

from app.core.config import Settings, settings
from app.exceptions.llm import (
    raise_hf_api_key_not_configured,
    raise_hf_completion_parse_failed,
    raise_hf_openai_error,
    raise_hf_request_timeout,
    raise_hf_structured_refusal,
    raise_hf_structured_reply_incomplete,
)

HF_CONNECT_TIMEOUT = 20.0
HF_READ_TIMEOUT = 75.0
HF_WRITE_TIMEOUT = 30.0
HF_POOL_TIMEOUT = 10.0
HF_TRANSIENT_RETRIES = 3

StructuredOutputT = TypeVar("StructuredOutputT", bound=BaseModel)


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

    async def generate_structured_output(
        self,
        *,
        messages: list[dict[str, Any]],
        response_format: type[StructuredOutputT],
        temperature: float,
        max_tokens: int,
    ) -> StructuredOutputT:
        """Request a typed structured output from the Hugging Face router."""
        if not self.settings.hf_token.strip():
            raise_hf_api_key_not_configured()

        try:
            completion = await self.client.beta.chat.completions.parse(
                model=self.settings.hf_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )
        except ValidationError as exc:
            raise_hf_completion_parse_failed(cause=exc)
        except APITimeoutError as exc:
            raise_hf_request_timeout(cause=exc)
        except OpenAIError as exc:
            raise_hf_openai_error(cause=exc)

        message = completion.choices[0].message
        if message.parsed is not None:
            return message.parsed
        if message.refusal:
            raise_hf_structured_refusal(refusal=str(message.refusal))
        raise_hf_structured_reply_incomplete()


huggingface_provider = HuggingFaceProvider(settings=settings)
