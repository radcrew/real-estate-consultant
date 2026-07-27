from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AsyncClient, AuthApiError
from supabase_auth.types import User

from app.core.database import get_session
from app.core.db_safe import SupabaseRequestError
from app.core.exceptions import (
    raise_auth_invalid_access_token,
    raise_auth_missing_bearer,
    raise_auth_user_not_returned,
)
from app.core.supabase_sdk import get_supabase_auth_client, get_supabase_sdk_client
from app.domain.mcp_api_keys import looks_like_mcp_api_key
from app.repositories.account import get_auth_user
from app.repositories.mcp_api_keys import resolve_mcp_api_key_user_id
from app.repositories.profiles import get_profile_row
from app.utils.exceptions import raise_forbidden, raise_service_unavailable

DbSession = Annotated[AsyncSession, Depends(get_session)]

# get_supabase_sdk_client is a plain sync function returning the singleton client —
# FastAPI handles both sync and async callables as dependencies.
SupabaseSdkDep = Annotated[AsyncClient, Depends(get_supabase_sdk_client)]
# Password grants only — must not share the service-role data client (SIGNED_IN poisons it).
SupabaseAuthDep = Annotated[AsyncClient, Depends(get_supabase_auth_client)]

_http_bearer = HTTPBearer(auto_error=False)


def _extract_credential(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    if credentials is not None and credentials.credentials.strip():
        return credentials.credentials.strip()
    for header in ("X-API-Key", "x-api-key"):
        raw = request.headers.get(header)
        if raw and raw.strip():
            return raw.strip()
    return None


async def _user_from_api_key(client: AsyncClient, raw_key: str) -> User:
    try:
        user_id = await resolve_mcp_api_key_user_id(client, raw_key)
    except SupabaseRequestError as exc:
        raise_service_unavailable("API key service unavailable.", cause=exc)
    if user_id is None:
        raise_auth_invalid_access_token()
    return await get_auth_user(client, str(user_id))


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
    client: Annotated[AsyncClient, Depends(get_supabase_sdk_client)],
) -> User:
    """Validate Bearer JWT **or** MCP API key (``rad_…`` / ``X-API-Key``)."""
    token = _extract_credential(request, credentials)
    if not token:
        raise_auth_missing_bearer()

    if looks_like_mcp_api_key(token):
        return await _user_from_api_key(client, token)

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
    try:
        raw = await get_profile_row(client, UUID(user.id))
    except SupabaseRequestError as exc:
        raise_service_unavailable("Profile service unavailable.", cause=exc)
    if not raw or not raw.get("is_admin"):
        raise_forbidden("Admin access required.")
    return user


CurrentAdmin = Annotated[User, Depends(get_current_admin)]
