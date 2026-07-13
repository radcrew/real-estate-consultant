"""Avatar upload for the authenticated account (Supabase Storage)."""

from __future__ import annotations

import logging
import secrets
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, UploadFile

from app.core.deps import CurrentUser, SupabaseSdkDep
from app.domain.account_profile import account_profile_response
from app.models.profile import profile_from_row
from app.repositories.account import get_auth_user
from app.repositories.profiles import get_profile_row, set_profile_avatar_url
from app.schemas.account import AccountProfileResponse
from app.utils.exceptions import raise_bad_gateway, raise_bad_request

logger = logging.getLogger(__name__)

router = APIRouter()

_AVATAR_BUCKET = "avatars"
_MAX_AVATAR_BYTES = 5 * 1024 * 1024  # 5 MB
_CONTENT_TYPE_EXT: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}


@router.post("/avatar", response_model=AccountProfileResponse)
async def upload_account_avatar(
    current_user: CurrentUser,
    client: SupabaseSdkDep,
    file: Annotated[UploadFile, File()],
) -> AccountProfileResponse:
    """Upload an avatar image to Supabase Storage and save its URL on the profile."""
    content_type = (file.content_type or "").lower()
    ext = _CONTENT_TYPE_EXT.get(content_type)
    if ext is None:
        raise_bad_request("Avatar must be a JPEG, PNG, WebP or GIF image.")

    data = await file.read()
    if not data:
        raise_bad_request("Uploaded file is empty.")
    if len(data) > _MAX_AVATAR_BYTES:
        raise_bad_request("Avatar must be 5 MB or smaller.")

    user_id = UUID(current_user.id)
    path = f"{user_id}/{secrets.token_hex(8)}.{ext}"

    storage = client.storage.from_(_AVATAR_BUCKET)
    try:
        await storage.upload(
            path,
            data,
            {"content-type": content_type, "upsert": "true"},
        )
    except Exception as exc:  # noqa: BLE001 - surface any storage failure as 502
        logger.error("Supabase Storage upload to bucket %r failed: %s", _AVATAR_BUCKET, exc)
        raise_bad_gateway("Failed to upload avatar.", cause=exc)

    public_url = await storage.get_public_url(path)
    if not isinstance(public_url, str) or not public_url:
        raise_bad_gateway("Failed to resolve avatar URL.")

    await set_profile_avatar_url(client, user_id, public_url)

    user = await get_auth_user(client, current_user.id)
    raw = await get_profile_row(client, user_id)
    return account_profile_response(user=user, profile=profile_from_row(raw))
