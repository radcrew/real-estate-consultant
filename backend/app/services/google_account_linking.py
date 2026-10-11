"""Fold a Google sign-in into an existing email/password account.

By the time the backend sees a Google sign-in, Cognito has already created a standalone
``google_…`` user. It is folded into the password account (data, delete, link; see
``google_identity``). Anything the Google user already owned (it may have signed in
before, for example when the confirm-time merge could not run) moves with it. The tokens
in hand belong to the deleted user; the caller has the browser sign in again, and that
second pass lands on the existing account.

Linking by email hands that account to whoever controls the Google address, so it only
happens when both Google and the existing account have the email verified.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cognito import is_google_username
from app.services.google_identity import (
    attributes,
    fold_google_user,
    google_user_id,
    users_with_email,
)


def _is_true(value: Any) -> bool:
    return value is True or value == "true"


def _password_account(users: list[dict[str, Any]], email: str) -> tuple[str, str] | None:
    """Username and ``sub`` of the one enabled, verified email/password user with this email."""
    matches = []
    for user in users:
        attrs = attributes(user)
        if (
            user.get("UserStatus") != "EXTERNAL_PROVIDER"
            and user.get("Enabled", True)
            and attrs.get("email", "").lower() == email
            and _is_true(attrs.get("email_verified"))
        ):
            matches.append((user["Username"], attrs.get("sub")))
    # Two candidates would mean the pool is not keyed by email; do not guess.
    if len(matches) != 1 or not matches[0][1]:
        return None
    return matches[0]


async def link_to_existing_account(session: AsyncSession, claims: dict[str, Any]) -> bool:
    """Link a standalone Google user to a password account with the same email.

    Returns True when the Google user was deleted (and linked), meaning the caller's
    tokens are dead and the browser must sign in again. Returns False when there is
    nothing to link or linking was not attempted; sign-in then proceeds as is.
    """
    username = str(claims.get("cognito:username") or "")
    email = str(claims.get("email") or "").strip().lower()
    if not is_google_username(username) or not email:
        return False
    if not _is_true(claims.get("email_verified")):
        return False
    # Read from the claim only: the username fallback is for pool entries, not tokens.
    google_id = google_user_id(claims.get("identities"))
    old_sub = str(claims.get("sub") or "")
    if not google_id or not old_sub:
        return False

    users = await users_with_email(email, event="google_link")
    if users is None:
        return False
    destination = _password_account(users, email)
    if destination is None:
        return False
    destination_username, new_sub = destination

    return await fold_google_user(
        session,
        google_username=username,
        google_id=google_id,
        google_sub=old_sub,
        destination_username=destination_username,
        destination_sub=new_sub,
        event="google_link",
    )
