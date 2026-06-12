from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AsyncClient, AuthApiError
from supabase_auth.types import User

from app.core.database import get_session
from app.core.exceptions import (
    raise_auth_invalid_access_token,
    raise_auth_missing_bearer,
    raise_auth_user_not_returned,
)
from app.core.supabase_sdk import get_supabase_sdk_client
from app.repositories.profiles import fetch_profile_row
from app.utils.exceptions import raise_forbidden

DbSession = Annotated[AsyncSession, Depends(get_session)]

# get_supabase_sdk_client is a plain sync function returning the singleton client —
# FastAPI handles both sync and async callables as dependencies.
SupabaseSdkDep = Annotated[AsyncClient, Depends(get_supabase_sdk_client)]

_http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
    client: Annotated[AsyncClient, Depends(get_supabase_sdk_client)],
) -> User:
    """Validate ``Authorization: Bearer <access_token>`` via Supabase Auth."""
    if credentials is None or not credentials.credentials.strip():
        raise_auth_missing_bearer()
    token = credentials.credentials.strip()
    try:
        response = await client.auth.get_user(token)
    except AuthApiError as exc:
        raise_auth_invalid_access_token(cause=exc)

    if response is None or response.user is None:
        raise_auth_user_not_returned()
    return response.user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_admin(
    user: CurrentUser,
    client: SupabaseSdkDep,
) -> User:
    """Require the authenticated user to have ``profiles.is_admin = true``."""
    raw = await fetch_profile_row(client, UUID(user.id))
    if not raw or not raw.get("is_admin"):
        raise_forbidden("Admin access required.")
    return user


CurrentAdmin = Annotated[User, Depends(get_current_admin)]
