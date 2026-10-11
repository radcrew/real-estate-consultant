"""Google sign-in: trade the Hosted UI authorization code for a session.

The frontend owns the redirect to Cognito and the ``state`` check. It calls this endpoint
from its ``/auth/callback`` route handler, because only the backend holds the client secret.
"""

import asyncio
import logging
from typing import Any

import httpx
import jwt
from fastapi import APIRouter

from app.api.v1.endpoints.auth.exceptions import (
    raise_oauth_account_linked,
    raise_oauth_code_rejected,
    raise_sign_in_transport_unavailable,
)
from app.api.v1.endpoints.auth.sign_in import session_response
from app.core.cognito import verify_id_token
from app.core.config import settings
from app.core.deps import DbSession, SupabaseSdkDep
from app.core.exceptions import raise_auth_provider_unavailable
from app.schemas.auth import OAuthExchangeRequest, SignInResponse
from app.services.google_account_linking import link_to_existing_account

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
        logger.warning(
            "google_code_rejected",
            extra={"step": "token_endpoint", "status": r.status_code, "reason": r.text[:300]},
        )
        raise_oauth_code_rejected(cause=RuntimeError(r.text))
    return r.json()


@router.post("/oauth/exchange")
async def oauth_exchange(
    body: OAuthExchangeRequest, client: SupabaseSdkDep, session: DbSession
) -> SignInResponse:
    tokens = await _exchange_code(body.code, body.redirect_uri)
    try:
        claims = await asyncio.to_thread(verify_id_token, tokens["id_token"])
    except jwt.PyJWKClientConnectionError as exc:
        # Cognito's signing keys could not be fetched: an outage, not a bad code.
        raise_auth_provider_unavailable(cause=exc)
    except jwt.PyJWTError as exc:
        logger.warning(
            "google_code_rejected",
            extra={"step": "id_token", "reason": f"{type(exc).__name__}: {exc}"},
        )
        raise_oauth_code_rejected(cause=exc)

    # These tokens belong to a new standalone Google user. If the email already has a
    # password account, the Google user is folded into it and must sign in once more.
    if body.link_accounts and await link_to_existing_account(session, claims):
        raise_oauth_account_linked()

    auth = {
        "AccessToken": tokens["access_token"],
        "IdToken": tokens["id_token"],
        "RefreshToken": tokens["refresh_token"],
        "ExpiresIn": tokens["expires_in"],
        "TokenType": tokens["token_type"],
    }
    return await session_response(auth, client, create_profile=True)
