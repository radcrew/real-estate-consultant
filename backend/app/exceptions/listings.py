"""HTTP errors for listing (property) routes."""

from __future__ import annotations

from typing import NoReturn

from app.exceptions.common import raise_not_found


def raise_listing_not_found() -> NoReturn:
    raise_not_found("Listing not found.")
