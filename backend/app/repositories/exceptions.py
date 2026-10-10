"""HTTP errors raised by repository helpers."""

from __future__ import annotations

from typing import NoReturn

from app.utils.exceptions import (
    raise_bad_gateway,
    raise_bad_request,
    raise_not_found,
)


def raise_current_password_incorrect(*, cause: BaseException | None = None) -> NoReturn:
    # 400, not 401: the browser treats a 401 as an expired session and signs the user out.
    raise_bad_request("Current password is incorrect.", cause=cause)


def raise_intake_session_not_found() -> NoReturn:
    raise_not_found("Intake session not found.")


def raise_intake_job_not_found() -> NoReturn:
    """Unknown job, or one belonging to another session.

    Both cases answer the same way on purpose: a job id is a bearer token, and telling a
    caller that an id exists but is not theirs is itself a disclosure.
    """
    raise_not_found("Intake job not found.")


def raise_intake_questions_load_empty() -> NoReturn:
    raise_bad_gateway("No question is configured for intake flow.")
