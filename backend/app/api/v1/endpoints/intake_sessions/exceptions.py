"""HTTP errors for intake-session endpoints."""

from __future__ import annotations

from typing import NoReturn

from app.utils.exceptions import raise_bad_gateway


def raise_intake_endpoint_no_questions_configured() -> NoReturn:
    raise_bad_gateway("No questions configured for intake flow.")
