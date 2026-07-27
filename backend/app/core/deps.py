from __future__ import annotations

from contextvars import ContextVar
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from supabase_auth.types import User

from app.core.api_key_rate_limit import ApiKeyRateLimiter
from app.core.config import settings
from app.core.database import get_session
from app.core.db_safe import SupabaseRequestError
from app.core.exceptions import (
    raise_auth_invalid_access_token,
    raise_auth_missing_bearer,
    raise_auth_user_not_returned,
)
from app.core.supabase_sdk import get_supabase_auth_client, get_supabase_sdk_client
from app.domain.mcp_api_keys import looks_like_mcp_api_key, mcp_scopes_allow
from app.repositories.account import get_auth_user
from app.repositories.mcp_api_keys import ResolvedMcpApiKey, resolve_mcp_api_key
from app.repositories.profiles import get_profile_row
from app.utils.exceptions import raise_forbidden, raise_service_unavailable, raise_too_many_requests
from supabase import AsyncClient, AuthApiError

DbSession = Annotated[AsyncSession, Depends(get_session)]

SupabaseSdkDep = Annotated[AsyncClient, Depends(get_supabase_sdk_client)]
SupabaseAuthDep = Annotated[AsyncClient, Depends(get_supabase_auth_client)]

_http_bearer = HTTPBearer(auto_error=False)

_api_key_ctx: ContextVar[ResolvedMcpApiKey | None] = ContextVar("mcp_api_key_ctx", default=None)
_api_key_limiter = ApiKeyRateLimiter(
    max_calls=settings.mcp_api_key_rate_limit_per_minute,
    window_seconds=60.0,
)


def get_request_mcp_api_key() -> ResolvedMcpApiKey | None:
    return _api_key_ctx.get()


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


def _enforce_request_scope(request: Request, scopes: list[str]) -> None:
    """Map HTTP method to mcp:read vs mcp:write (admin/* cover both)."""
    method = request.method.upper()
    if method in {"GET", "HEAD", "OPTIONS"}:
        if not mcp_scopes_allow(scopes, "mcp:read"):
            raise_forbidden("MCP API key lacks mcp:read scope.")
        return
    if not mcp_scopes_allow(scopes, "mcp:write"):
        raise_forbidden("MCP API key lacks mcp:write scope.")


async def _user_from_api_key(request: Request, client: AsyncClient, raw_key: str) -> User:
    try:
        resolved = await resolve_mcp_api_key(client, raw_key)
    except SupabaseRequestError as exc:
        raise_service_unavailable("API key service unavailable.", cause=exc)
    if resolved is None:
        raise_auth_invalid_access_token()
    if not _api_key_limiter.allow(resolved.key_id):
        raise_too_many_requests("MCP API key rate limit exceeded. Try again shortly.")
    _enforce_request_scope(request, resolved.scopes)
    _api_key_ctx.set(resolved)
    return await get_auth_user(client, str(resolved.user_id))


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
    client: Annotated[AsyncClient, Depends(get_supabase_sdk_client)],
) -> User:
    """Validate Bearer JWT **or** MCP API key (``rad_…`` / ``X-API-Key``)."""
    _api_key_ctx.set(None)
    token = _extract_credential(request, credentials)
    if not token:
        raise_auth_missing_bearer()

    if looks_like_mcp_api_key(token):
        return await _user_from_api_key(request, client, token)

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
    """Require admin profile; API keys also need ``mcp:admin`` or ``*`` scope."""
    api_key = get_request_mcp_api_key()
    if api_key is not None and not mcp_scopes_allow(api_key.scopes, "mcp:admin"):
        raise_forbidden("MCP API key lacks mcp:admin scope.")

    try:
        raw = await get_profile_row(client, UUID(user.id))
    except SupabaseRequestError as exc:
        raise_service_unavailable("Profile service unavailable.", cause=exc)
    if not raw or not raw.get("is_admin"):
        raise_forbidden("Admin access required.")
    return user


CurrentAdmin = Annotated[User, Depends(get_current_admin)]
