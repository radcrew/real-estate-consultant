"""HTTP errors for LLM intake helpers."""

from __future__ import annotations

from typing import NoReturn

from app.utils.exceptions import raise_bad_gateway


def raise_hf_opening_response_missing_text() -> NoReturn:
    raise_bad_gateway("Hugging Face response missing text field.")
