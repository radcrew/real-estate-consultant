"""Fold an existing Google-only user into the email/password user that just confirmed.

Runs after ``ConfirmSignUp`` succeeds, because the code proves the new user owns the
email; merging any earlier would let someone take over a Google account by signing up
with its address. The fold itself (data, delete, link) lives in ``google_identity``.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.google_identity import (
    GOOGLE_USERNAME_PREFIX,
    attributes,
    fold_google_user,
    google_user_id,
    users_with_email,
)


async def merge_google_user(session: AsyncSession, email: str) -> bool:
    """Merge the Google-only user with this email into the confirmed password user.

    Returns True when the Google user was folded in. Never raises: the sign-up is already
    confirmed, so a failure here is logged and the two users simply stay separate.
    """
    email = email.strip().lower()
    users = await users_with_email(email, event="google_merge")
    if users is None:
        return False

    same_email = [u for u in users if attributes(u).get("email", "").lower() == email]
    password_users = [u for u in same_email if u.get("UserStatus") == "CONFIRMED"]
    # Google must have verified the address too, or anyone could claim it there first and
    # be handed this account once its owner confirms.
    google_users = [
        u
        for u in same_email
        if u.get("UserStatus") == "EXTERNAL_PROVIDER"
        and u["Username"].startswith(GOOGLE_USERNAME_PREFIX)
        and attributes(u).get("email_verified") == "true"
    ]
    if len(password_users) != 1 or len(google_users) != 1:
        return False

    destination, google = password_users[0], google_users[0]
    new_sub = attributes(destination).get("sub")
    old_sub = attributes(google).get("sub")
    google_id = google_user_id(attributes(google).get("identities"), google["Username"])
    if not (new_sub and old_sub and google_id):
        return False

    return await fold_google_user(
        session,
        google_username=google["Username"],
        google_id=google_id,
        google_sub=old_sub,
        destination_username=destination["Username"],
        destination_sub=new_sub,
        event="google_merge",
    )
