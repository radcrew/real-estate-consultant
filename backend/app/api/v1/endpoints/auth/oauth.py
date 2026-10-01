"""Google sign-in: trade the Hosted UI authorization code for a session.

The frontend owns the redirect to Cognito and the ``state`` check. It calls this endpoint
from its ``/auth/callback`` route handler, because only the backend holds the client secret.
"""

import asyncio
import logging
from typing import Any
from uuid import UUID

import httpx
import jwt
from fastapi import APIRouter

from app.api.v1.endpoints.auth.exceptions import (
    raise_oauth_code_rejected,
    raise_sign_in_transport_unavailable,
)
from app.api.v1.endpoints.auth.sign_in import session_response
from app.core.cognito import verify_id_token
from app.core.config import settings
from app.core.db_safe import SupabaseRequestError
from app.core.deps import SupabaseSdkDep
from app.repositories.profiles import get_profile_row, upsert_profile_patch
from app.schemas.account import AccountProfileUpdate
from app.schemas.auth import OAuthExchangeRequest, SignInResponse
from supabase import AsyncClient

router = APIRouter()
logger = logging.getLogger(__name__)

_TOKEN_TIMEOUT = httpx.Timeout(10.0)


async def _exchange_code(code: str, redirect_uri: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=_TOKEN_TIMEOUT) as http:
            r = await http.post(
                f"{settings.cognito_domain.rstrip('/')}/oauth2/token",
                auth=(settings.cognito_client_id, settings.cognito_client_secret),
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.cognito_client_id,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )
    except httpx.HTTPError as exc:
        raise_sign_in_transport_unavailable(cause=exc)
    if r.status_code >= 500:
        raise_sign_in_transport_unavailable(cause=RuntimeError(r.text))
    if r.status_code != 200:
        # invalid_grant: the code expired, was already used, or redirect_uri differs.
        raise_oauth_code_rejected(cause=RuntimeError(r.text))
    return r.json()


async def _sync_profile(client: AsyncClient, claims: dict[str, Any]) -> None:
    """Always take the email from Google; fill names only where the user has none.

    A failed write is logged, not raised: the profile is display data and must not
    block sign-in.
    """
    user_id = UUID(claims["sub"])
    try:
        existing = await get_profile_row(client, user_id) or {}
        await upsert_profile_patch(
            client,
            user_id,
            AccountProfileUpdate(
                email=claims.get("email"),
                first_name=existing.get("first_name") or claims.get("given_name"),
                last_name=existing.get("last_name") or claims.get("family_name"),
            ),
        )
    except SupabaseRequestError as exc:
        logger.error("Profile sync after Google sign-in failed for %s: %s", user_id, exc)


@router.post("/oauth/exchange")
async def oauth_exchange(body: OAuthExchangeRequest, client: SupabaseSdkDep) -> SignInResponse:
    tokens = await _exchange_code(body.code, body.redirect_uri)
    try:
        claims = await asyncio.to_thread(verify_id_token, tokens["id_token"])
    except jwt.PyJWTError as exc:
        raise_oauth_code_rejected(cause=exc)

    await _sync_profile(client, claims)
    auth = {
        "AccessToken": tokens["access_token"],
        "IdToken": tokens["id_token"],
        "RefreshToken": tokens["refresh_token"],
        "ExpiresIn": tokens["expires_in"],
        "TokenType": tokens["token_type"],
    }
    return await session_response(auth, email=claims.get("email"))
