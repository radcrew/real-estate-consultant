"""Fold a first-time Google sign-in into an existing email/password account.

By the time the backend sees a Google sign-in, Cognito has already created a standalone
``google_…`` user. ``AdminLinkProviderForUser`` refuses to link an identity that exists as
its own user, so the Google user is deleted first and then linked to the password account.
Anything the Google user already owned (it may have signed in before, for example when the
confirm-time merge could not run) moves to the password account. The tokens in hand belong
to the deleted user; the caller has the browser sign in again, and that second pass lands
on the existing account.

Linking by email hands that account to whoever controls the Google address, so it only
happens when both Google and the existing account have the email verified.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cognito import call_admin_idp
from app.core.config import settings
from app.repositories.user_reassignment import reassign_user

logger = logging.getLogger(__name__)

_GOOGLE_USERNAME_PREFIX = "google_"


def _is_true(value: Any) -> bool:
    return value is True or value == "true"


def _google_user_id(claims: dict[str, Any]) -> str | None:
    """Google's own id for the user, from the ID token's ``identities`` claim."""
    identities = claims.get("identities")
    if isinstance(identities, str):
        try:
            identities = json.loads(identities)
        except ValueError:
            return None
    for identity in identities or []:
        if isinstance(identity, dict) and identity.get("providerName") == "Google":
            return identity.get("userId") or None
    return None


def _password_account(users: list[dict[str, Any]], email: str) -> tuple[str, str] | None:
    """Username and ``sub`` of the one enabled, verified email/password user with this email."""
    matches = []
    for user in users:
        attrs = {a["Name"]: a["Value"] for a in user.get("Attributes", [])}
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
    """Link a new standalone Google user to a password account with the same email.

    Returns True when the Google user was deleted (and linked), meaning the caller's
    tokens are dead and the browser must sign in again. Returns False when there is
    nothing to link or linking was not attempted; sign-in then proceeds as is.
    """
    username = str(claims.get("cognito:username") or "")
    email = str(claims.get("email") or "").strip().lower()
    if not username.startswith(_GOOGLE_USERNAME_PREFIX) or not email:
        return False
    if not _is_true(claims.get("email_verified")):
        return False
    # The email goes into a ListUsers filter string; refuse anything that could break it.
    if '"' in email or "\\" in email:
        return False
    google_id = _google_user_id(claims)
    old_sub = str(claims.get("sub") or "")
    if not google_id or not old_sub:
        return False

    pool = settings.cognito_user_pool_id
    try:
        listed = await call_admin_idp(
            "list_users", UserPoolId=pool, Filter=f'email = "{email}"', Limit=10
        )
    except (ClientError, BotoCoreError) as exc:
        logger.error("google_link_lookup_failed", extra={"error": str(exc)})
        return False

    destination = _password_account(listed.get("Users", []), email)
    if destination is None:
        return False
    destination_username, new_sub = destination

    try:
        await call_admin_idp("admin_delete_user", UserPoolId=pool, Username=username)
    except (ClientError, BotoCoreError) as exc:
        logger.error("google_link_delete_failed", extra={"error": str(exc)})
        return False

    # From here the standalone Google user is gone, so report True even if linking
    # fails: the retry pass (link_accounts=False) recreates it as a plain Google user.
    try:
        await call_admin_idp(
            "admin_link_provider_for_user",
            UserPoolId=pool,
            DestinationUser={
                "ProviderName": "Cognito",
                "ProviderAttributeValue": destination_username,
            },
            SourceUser={
                "ProviderName": "Google",
                "ProviderAttributeName": "Cognito_Subject",
                "ProviderAttributeValue": google_id,
            },
        )
        logger.info("google_account_linked")
    except (ClientError, BotoCoreError) as exc:
        logger.error("google_link_failed", extra={"error": str(exc)})

    try:
        path = await reassign_user(session, old_sub, new_sub)
    except SQLAlchemyError as exc:
        # The Google user is gone; its data now needs a manual move. Log both ids.
        logger.error(
            "google_link_data_move_failed",
            extra={"old_sub": old_sub, "new_sub": new_sub, "error": str(exc)},
        )
        return True
    logger.info("google_link_data_moved", extra={"data_path": path})
    return True
