"""HTTP errors for LLM fit-explanation helpers."""

from __future__ import annotations

from typing import NoReturn

from app.utils.exceptions import raise_bad_gateway


def raise_fit_explanation_empty() -> NoReturn:
    raise_bad_gateway("Fit explanation was empty.")
