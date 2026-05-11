"""HTTP errors for intake-session answer endpoints."""

from __future__ import annotations

from typing import NoReturn

from app.utils.exceptions import raise_bad_request


def raise_intake_unknown_question_key() -> NoReturn:
    raise_bad_request("Unknown question key for this questionnaire.")
