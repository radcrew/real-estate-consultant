"""Shared steps for folding a standalone Google user into an email/password user.

Two paths do this: ``google_user_merge`` when a password sign-up is confirmed, and
``google_account_linking`` on a Google sign-in. Each picks the two users its own way; this
module owns the lookup and the fold itself, so the sequence cannot drift between them.

The fold runs so that a failure part way loses nothing:

1. In one database transaction, move the Google user's data to the password user, then
   delete the Google user in Cognito (``AdminLinkProviderForUser`` refuses to link an
   identity that still exists as its own user). The transaction commits only once the
   delete has succeeded; if either step fails, it rolls back and both users stay as
   they were.
2. Link the Google identity to the password user, so Google sign-in lands there.

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

GOOGLE_USERNAME_PREFIX = "google_"


def attributes(user: dict[str, Any]) -> dict[str, str]:
    """A ListUsers entry's attributes as a dict."""
    return {a["Name"]: a["Value"] for a in user.get("Attributes", [])}


def google_user_id(identities: Any, username: str = "") -> str | None:
    """Google's own id for a federated user.

    Read from the ``identities`` attribute or claim (a JSON string or a list), else from a
    ``google_<id>`` username.
    """
    if isinstance(identities, str):
        try:
            identities = json.loads(identities)
        except ValueError:
            identities = []
    for identity in identities or []:
        if isinstance(identity, dict) and identity.get("providerName") == "Google":
            if identity.get("userId"):
                return identity["userId"]
    if username.startswith(GOOGLE_USERNAME_PREFIX):
        return username[len(GOOGLE_USERNAME_PREFIX):] or None
    return None


async def users_with_email(email: str, *, event: str) -> list[dict[str, Any]] | None:
    """Every pool user with this (lowercased) email, or None if the lookup cannot run."""
    # The email goes into a ListUsers filter string; refuse anything that could break it.
    if not email or '"' in email or "\\" in email:
        return None
    try:
        listed = await call_admin_idp(
            "list_users",
            UserPoolId=settings.cognito_user_pool_id,
            Filter=f'email = "{email}"',
            Limit=10,
        )
    except (ClientError, BotoCoreError) as exc:
        logger.error(f"{event}_lookup_failed", extra={"error": str(exc)})
        return None
    return listed.get("Users", [])


async def fold_google_user(
    session: AsyncSession,
    *,
    google_username: str,
    google_id: str,
    google_sub: str,
    destination_username: str,
    destination_sub: str,
    event: str,
) -> bool:
    """Move the Google user's data, delete it, and link its identity to the destination.

    Returns True once the Google user is deleted, even if the link then fails: the next
    Google sign-in recreates a standalone user and linking runs again. Returns False when
    nothing was deleted. Never raises.
    """
    pool = settings.cognito_user_pool_id
    subs = {"old_sub": google_sub, "new_sub": destination_sub}
    deleted = False
    try:
        async with session.begin():
            await reassign_user(session, google_sub, destination_sub)
            await call_admin_idp("admin_delete_user", UserPoolId=pool, Username=google_username)
            deleted = True
    except (ClientError, BotoCoreError) as exc:
        # The move rolled back with the failed delete: the Google user keeps its data.
        logger.error(f"{event}_delete_failed", extra={"error": str(exc)})
        return False
    except SQLAlchemyError as exc:
        if not deleted:
            logger.error(f"{event}_data_move_failed", extra={**subs, "error": str(exc)})
            return False
        # The Google user is gone but its data did not move; it needs a manual move.
        logger.error(f"{event}_commit_failed", extra={**subs, "error": str(exc)})

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
    except (ClientError, BotoCoreError) as exc:
        logger.error(f"{event}_link_failed", extra={"error": str(exc)})
        return True

    logger.info(f"{event}_done")
    return True
