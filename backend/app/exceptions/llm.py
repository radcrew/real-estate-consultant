"""HTTP errors for LLM / Hugging Face providers and intake LLM helpers."""

from __future__ import annotations

from typing import NoReturn

from openai import APITimeoutError, OpenAIError
from pydantic import ValidationError

from app.exceptions.common import (
    raise_bad_gateway,
    raise_gateway_timeout,
    raise_service_unavailable,
)


def raise_hf_api_key_not_configured() -> NoReturn:
    raise_service_unavailable("Hugging Face API key is not configured.")


def raise_hf_completion_parse_failed(*, cause: ValidationError) -> NoReturn:
    raise_bad_gateway(
        "We couldn't process the assistant's reply. Please try again in a moment.",
        cause=cause,
    )


def raise_hf_request_timeout(*, cause: APITimeoutError) -> NoReturn:
    raise_gateway_timeout("Timed out while calling Hugging Face API.", cause=cause)


def raise_hf_openai_error(*, cause: OpenAIError) -> NoReturn:
    raise_bad_gateway(f"Hugging Face request failed: {cause}", cause=cause)


def raise_hf_structured_refusal(*, refusal: str) -> NoReturn:
    raise_bad_gateway(f"Hugging Face refused the structured request: {refusal}")


def raise_hf_structured_reply_incomplete() -> NoReturn:
    raise_bad_gateway(
        "The assistant's reply didn't come through completely. "
        "Please try again in a moment.",
    )


def raise_hf_opening_response_missing_text() -> NoReturn:
    raise_bad_gateway("Hugging Face response missing text field.")
