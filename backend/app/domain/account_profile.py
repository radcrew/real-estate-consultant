"""Build account API payloads from ``AuthUser`` + ``public.profiles`` row."""

from __future__ import annotations

from app.models.auth_user import AuthUser
from app.models.profile import Profile
from app.schemas.account import AccountProfileResponse


def account_profile_response(*, user: AuthUser, profile: Profile | None) -> AccountProfileResponse:
    if profile is None:
        return AccountProfileResponse(
            id=user.id,
            email=user.email,
            phone=user.phone,
        )

    return AccountProfileResponse(
        id=user.id,
        email=profile.email,
        phone=profile.phone,
        first_name=profile.first_name,
        last_name=profile.last_name,
        address=profile.address,
        city=profile.city,
        state=profile.state,
        zip_code=profile.zip_code,
        country=profile.country,
        avatar_url=profile.avatar_url,
    )
