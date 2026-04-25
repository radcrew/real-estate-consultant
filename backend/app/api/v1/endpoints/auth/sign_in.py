import httpx
from fastapi import APIRouter, HTTPException, status
from supabase import AuthApiError, AuthInvalidCredentialsError

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        ) from exc

    except AuthApiError as exc:
        if exc.code in ("invalid_credentials", "invalid_grant"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            ) from exc

        if exc.code in ("email_not_confirmed", "provider_email_needs_verification"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=exc.message,
            ) from exc

        raise HTTPException(
            status_code=exc.status if 400 <= exc.status < 600 else status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable. Please try again.",
        ) from exc

    session = result.session
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No session returned. Confirm your email if your project requires it.",
        )

    user = session.user
    return SignInResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        expires_in=session.expires_in,
        token_type=session.token_type,
        user=SignInUser(id=user.id, email=user.email),
    )
