"""Build account API payloads from Supabase Auth ``User`` + ``public.profiles`` row."""

from __future__ import annotations

from supabase_auth.types import User

from app.models.profile import Profile
from app.schemas.account import AccountProfileResponse


def account_profile_response(*, user: User, profile: Profile | None) -> AccountProfileResponse:
    if profile is None:
        return AccountProfileResponse(
            id=user.id,
            email=user.email,
            phone=user.phone,
        )

    return AccountProfileResponse(
        id=user.id,
        email=user.email,
        phone=user.phone,
        first_name=profile.first_name,
        last_name=profile.last_name,
        address=profile.address,
        city=profile.city,
        state=profile.state,
        zip_code=profile.zip_code,
        country=profile.country,
        avatar_url=profile.avatar_url,
    )
