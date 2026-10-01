"""HTTP errors for authenticated account routes."""

from __future__ import annotations

from typing import NoReturn

from app.utils.exceptions import (
    raise_bad_request,
    raise_forbidden,
    raise_not_found,
    raise_unprocessable_entity,
)


def raise_account_no_fields_to_update() -> NoReturn:
    raise_bad_request("No fields to update.")


def raise_account_password_change_needs_session() -> NoReturn:
    raise_forbidden("Changing the password requires a signed-in session, not an API key.")


def raise_account_password_managed_by_google() -> NoReturn:
    raise_bad_request("This account signs in with Google and has no password to change.")


def raise_account_new_password_same_as_current() -> NoReturn:
    raise_unprocessable_entity("New password must be different from your current password.")


def raise_mcp_api_key_not_found() -> NoReturn:
    raise_not_found("MCP API key not found.")
