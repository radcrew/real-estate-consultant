"""HTTP errors for authenticated account routes."""

from __future__ import annotations

from typing import NoReturn

from app.utils.exceptions import raise_bad_request, raise_unprocessable_entity


def raise_account_no_fields_to_update() -> NoReturn:
    raise_bad_request("No fields to update.")


def raise_account_no_email_for_password_change() -> NoReturn:
    raise_bad_request(
        "This account has no email; password change is not supported here.",
    )


def raise_account_new_password_same_as_current() -> NoReturn:
    raise_unprocessable_entity("New password must be different from your current password.")
