"""HTTP errors for authenticated account routes."""

from __future__ import annotations

from typing import NoReturn

from app.utils.exceptions import (
    raise_bad_request,
    raise_conflict,
    raise_not_found,
    raise_unprocessable_entity,
)


def raise_account_no_fields_to_update() -> NoReturn:
    raise_bad_request("No fields to update.")


def raise_account_password_managed_by_google() -> NoReturn:
    raise_bad_request("This account signs in with Google and has no password to change.")


def raise_account_email_managed_by_google() -> NoReturn:
    raise_bad_request("This account signs in with Google; its email comes from Google.")


def raise_account_email_change_needs_password_sign_in(*, cause: BaseException) -> NoReturn:
    raise_bad_request(
        "To change your email, sign in with your email and password, then try again.",
        cause=cause,
    )


def raise_account_email_in_use(*, cause: BaseException) -> NoReturn:
    raise_conflict("That email is already in use.", cause=cause)


def raise_account_new_password_same_as_current() -> NoReturn:
    raise_unprocessable_entity("New password must be different from your current password.")


def raise_mcp_api_key_not_found() -> NoReturn:
    raise_not_found("MCP API key not found.")
