"""HTTP errors raised by admin endpoints."""

from __future__ import annotations

from typing import NoReturn

from app.utils.exceptions import raise_conflict, raise_not_found


def raise_job_already_queued(source: str, status: str) -> NoReturn:
    raise_conflict(f"Job for {source!r} is already {status!r} today.")


def raise_job_not_found() -> NoReturn:
    raise_not_found("Job not found.")
