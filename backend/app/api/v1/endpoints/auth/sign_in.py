import asyncio
import logging
from typing import Any

import jwt
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter

from app.api.v1.endpoints.auth.exceptions import (
    cognito_error_code,
    raise_cognito_error,
    raise_sign_in_challenge_required,
    raise_sign_in_email_not_confirmed,
    raise_sign_in_invalid_credentials,
    raise_sign_in_transport_unavailable,
)
from app.core.cognito import call_idp, secret_hash, verify_access_token
from app.core.config import settings
from app.core.db_safe import SupabaseRequestError
from app.core.deps import SupabaseSdkDep, user_id_for_sub
from app.core.exceptions import raise_auth_provider_unavailable
from app.repositories.profiles import ensure_profile_row
from app.schemas.auth import SignInRequest, SignInResponse, SignInUser
from supabase import AsyncClient

router = APIRouter()
logger = logging.getLogger(__name__)


async def session_response(
    auth: dict[str, Any],
    client: AsyncClient,
    *,
    refresh_token: str | None = None,
) -> SignInResponse:
    """Build the client session from a Cognito ``AuthenticationResult``.

    ``username`` is Cognito's own user name (the ``sub`` for pools that sign in by email,
    ``google_…`` for Google users). Refreshing a token needs it for ``SECRET_HASH``.
    A refresh returns no new refresh token unless rotation is on, so the caller passes
    the one it used. ``user.id`` is the app user id (``sub`` mapped through
    ``cognito_identity_mapping``), the same id every protected request resolves to.

    A first sign-in also creates the user's ``public.profiles`` row from the ID token.
    """
    try:
        claims = await asyncio.to_thread(verify_access_token, auth["AccessToken"])
    except jwt.PyJWTError as exc:
        # Cognito issued this token moments ago, so a failure here is ours (JWKS fetch,
        # config), not the user's.
        logger.error("session_token_unverifiable", extra={"reason": f"{type(exc).__name__}: {exc}"})
        raise_auth_provider_unavailable(cause=exc)
    user_id = await user_id_for_sub(client, claims["sub"])
    # The ID token came straight from Cognito over TLS; it is only read for profile fields.
    id_claims = jwt.decode(auth["IdToken"], options={"verify_signature": False})
    email = id_claims.get("email")
    try:
        await ensure_profile_row(
            client,
            user_id,
            email=email,
            first_name=id_claims.get("given_name"),
            last_name=id_claims.get("family_name"),
        )
    except SupabaseRequestError as exc:
        # Sign-in must not fail over the profile; the next sign-in or refresh retries.
        logger.warning("profile_create_failed", extra={"error": str(exc)})
    return SignInResponse(
        access_token=auth["AccessToken"],
        id_token=auth["IdToken"],
        refresh_token=auth.get("RefreshToken") or refresh_token,
        expires_in=auth["ExpiresIn"],
        token_type=auth["TokenType"],
        user=SignInUser(
            id=user_id,
            email=email,
            username=claims["username"],
        ),
    )


@router.post("/sign-in")
async def sign_in(body: SignInRequest, client: SupabaseSdkDep) -> SignInResponse:
    email = str(body.email)
    try:
        result = await call_idp(
            "initiate_auth",
            ClientId=settings.cognito_client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": body.password,
                "SECRET_HASH": secret_hash(email),
            },
        )

    except ClientError as exc:
        code = cognito_error_code(exc)
        # UserNotFound is folded into bad credentials so sign-in does not reveal accounts.
        if code in ("NotAuthorizedException", "UserNotFoundException"):
            raise_sign_in_invalid_credentials(cause=exc)
        if code == "UserNotConfirmedException":
            raise_sign_in_email_not_confirmed(cause=exc)
        raise_cognito_error(exc)

    except BotoCoreError as exc:
        raise_sign_in_transport_unavailable(cause=exc)

    auth = result.get("AuthenticationResult")
    if not auth:
        raise_sign_in_challenge_required(result.get("ChallengeName"))

    return await session_response(auth, client)
