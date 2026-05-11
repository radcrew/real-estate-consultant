"""HTTP errors for intake sessions and questionnaire data."""

from __future__ import annotations

from typing import NoReturn

from app.utils.exceptions import raise_bad_gateway, raise_bad_request, raise_not_found


def raise_intake_endpoint_no_questions_configured() -> NoReturn:
    raise_bad_gateway("No questions configured for intake flow.")


def raise_intake_unknown_question_key() -> NoReturn:
    raise_bad_request("Unknown question key for this questionnaire.")


def raise_intake_session_not_found() -> NoReturn:
    raise_not_found("Intake session not found.")


def raise_intake_questions_load_empty() -> NoReturn:
    raise_bad_gateway("No question is configured for intake flow.")
