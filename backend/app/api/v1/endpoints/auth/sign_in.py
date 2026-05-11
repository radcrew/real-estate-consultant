import httpx
from fastapi import APIRouter
from supabase import AuthApiError, AuthInvalidCredentialsError

from app.api.v1.endpoints.auth.exceptions import (
    raise_sign_in_auth_api_error,
    raise_sign_in_email_not_confirmed,
    raise_sign_in_invalid_credentials,
    raise_sign_in_no_session,
    raise_sign_in_transport_unavailable,
)
from app.core.deps import SupabaseSdkDep
from app.schemas.auth import SignInRequest, SignInResponse, SignInUser

router = APIRouter()


@router.post("/sign-in")
async def sign_in(body: SignInRequest, client: SupabaseSdkDep) -> SignInResponse:
    try:
        result = await client.auth.sign_in_with_password(
            {
                "email": body.email,
                "password": body.password,
            }
        )

    except AuthInvalidCredentialsError as exc:
        raise_sign_in_invalid_credentials(cause=exc)

    except AuthApiError as exc:
        if exc.code in ("invalid_credentials", "invalid_grant"):
            raise_sign_in_invalid_credentials(cause=exc)

        if exc.code in ("email_not_confirmed", "provider_email_needs_verification"):
            raise_sign_in_email_not_confirmed(message=str(exc.message), cause=exc)

        raise_sign_in_auth_api_error(exc)
    except httpx.HTTPError as exc:
        raise_sign_in_transport_unavailable(cause=exc)

    session = result.session
    if session is None:
        raise_sign_in_no_session()

    user = session.user
    return SignInResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        expires_in=session.expires_in,
        token_type=session.token_type,
        user=SignInUser(id=user.id, email=user.email),
    )
