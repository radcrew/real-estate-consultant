"""Fold an existing Google-only user into the email/password user that just confirmed.

Runs after ``ConfirmSignUp`` succeeds, because the code proves the new user owns the
email; merging any earlier would let someone take over a Google account by signing up
with its address. Steps, in an order where an early failure changes nothing:

1. Find the confirmed password user and the Google (``EXTERNAL_PROVIDER``) user that
   share the email.
2. Delete the Google user. ``AdminLinkProviderForUser`` refuses to link an identity that
   still exists as its own user.
3. Link the Google identity to the password user, so Google sign-in lands there.
4. Move the Google user's data from its old ``sub`` to the new user's ``sub``.

Needs IAM credentials (ListUsers, AdminDeleteUser, AdminLinkProviderForUser).
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

_GOOGLE_PREFIX = "google_"


def _attrs(user: dict[str, Any]) -> dict[str, str]:
    return {a["Name"]: a["Value"] for a in user.get("Attributes", [])}


def _google_user_id(user: dict[str, Any]) -> str | None:
    """Google's own id for a federated user: the ``identities`` attribute, else the name."""
    raw = _attrs(user).get("identities")
    try:
        identities = json.loads(raw) if raw else []
    except ValueError:
        identities = []
    for identity in identities:
        if isinstance(identity, dict) and identity.get("providerName") == "Google":
            if identity.get("userId"):
                return identity["userId"]
    username = user["Username"]
    return username[len(_GOOGLE_PREFIX):] if username.startswith(_GOOGLE_PREFIX) else None


async def merge_google_user(session: AsyncSession, email: str) -> bool:
    """Merge the Google-only user with this email into the confirmed password user.

    Returns True when a merge happened. Never raises: the sign-up is already confirmed,
    so a failure here is logged and the two users simply stay separate.
    """
    email = email.strip().lower()
    if '"' in email or "\\" in email:
        return False
    pool = settings.cognito_user_pool_id

    try:
        users = (
            await call_admin_idp(
                "list_users", UserPoolId=pool, Filter=f'email = "{email}"', Limit=10
            )
        ).get("Users", [])
    except (ClientError, BotoCoreError) as exc:
        logger.error("google_merge_lookup_failed", extra={"error": str(exc)})
        return False

    same_email = [u for u in users if _attrs(u).get("email", "").lower() == email]
    password_users = [u for u in same_email if u.get("UserStatus") == "CONFIRMED"]
    google_users = [
        u
        for u in same_email
        if u.get("UserStatus") == "EXTERNAL_PROVIDER" and u["Username"].startswith(_GOOGLE_PREFIX)
    ]
    if len(password_users) != 1 or len(google_users) != 1:
        return False

    new_sub = _attrs(password_users[0]).get("sub")
    google = google_users[0]
    old_sub = _attrs(google).get("sub")
    google_id = _google_user_id(google)
    if not (new_sub and old_sub and google_id):
        return False

    try:
        await call_admin_idp("admin_delete_user", UserPoolId=pool, Username=google["Username"])
    except (ClientError, BotoCoreError) as exc:
        logger.error("google_merge_delete_failed", extra={"error": str(exc)})
        return False

    try:
        await call_admin_idp(
            "admin_link_provider_for_user",
            UserPoolId=pool,
            DestinationUser={
                "ProviderName": "Cognito",
                "ProviderAttributeValue": password_users[0]["Username"],
            },
            SourceUser={
                "ProviderName": "Google",
                "ProviderAttributeName": "Cognito_Subject",
                "ProviderAttributeValue": google_id,
            },
        )
    except (ClientError, BotoCoreError) as exc:
        # Next Google sign-in recreates a Google user and the exchange links it then.
        logger.error("google_merge_link_failed", extra={"error": str(exc)})

    try:
        path = await reassign_user(session, old_sub, new_sub)
    except SQLAlchemyError as exc:
        # The Google user is gone; its data now needs a manual move. Log both ids.
        logger.error(
            "google_merge_data_move_failed",
            extra={"old_sub": old_sub, "new_sub": new_sub, "error": str(exc)},
        )
        return True

    logger.info("google_user_merged", extra={"data_path": path})
    return True
