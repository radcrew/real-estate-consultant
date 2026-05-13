"""HTTP errors for LLM outreach helpers."""

from __future__ import annotations

from typing import NoReturn

from app.utils.exceptions import raise_bad_gateway


def raise_outreach_email_empty() -> NoReturn:
    raise_bad_gateway("Outreach draft email was empty.")
