import asyncio
from typing import Any

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
from app.schemas.auth import SignInRequest, SignInResponse, SignInUser

router = APIRouter()


async def session_response(
    auth: dict[str, Any],
    *,
    email: str | None,
    refresh_token: str | None = None,
) -> SignInResponse:
    """Build the client session from a Cognito ``AuthenticationResult``.

    ``username`` is Cognito's own user name (the ``sub`` for pools that sign in by email,
    ``google_…`` for Google users). Refreshing a token needs it for ``SECRET_HASH``.
    A refresh returns no new refresh token unless rotation is on, so the caller passes
    the one it used.
    """
    claims = await asyncio.to_thread(verify_access_token, auth["AccessToken"])
    return SignInResponse(
        access_token=auth["AccessToken"],
        id_token=auth["IdToken"],
        refresh_token=auth.get("RefreshToken") or refresh_token,
        expires_in=auth["ExpiresIn"],
        token_type=auth["TokenType"],
        user=SignInUser(id=claims["sub"], email=email, username=claims["username"]),
    )


@router.post("/sign-in")
async def sign_in(body: SignInRequest) -> SignInResponse:
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

    return await session_response(auth, email=email)
