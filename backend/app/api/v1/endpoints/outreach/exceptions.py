"""HTTP errors for outreach draft routes."""

from __future__ import annotations

from typing import NoReturn

from app.utils.exceptions import raise_not_found


def raise_outreach_draft_not_found() -> NoReturn:
    raise_not_found("Outreach draft not found.")
