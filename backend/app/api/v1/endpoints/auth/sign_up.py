from fastapi import APIRouter, status
from supabase import AuthApiError, AuthWeakPasswordError

from app.api.v1.endpoints.auth.exceptions import (
    raise_sign_up_auth_api_error,
    raise_sign_up_email_already_exists,
    raise_sign_up_weak_password_api,
    raise_sign_up_weak_password_sdk,
)
from app.core.config import settings
from app.core.deps import SupabaseSdkDep
from app.schemas.auth import SignUpRequest, SignUpResponse

router = APIRouter()


@router.post("/sign-up", status_code=status.HTTP_201_CREATED)
async def sign_up(body: SignUpRequest, client: SupabaseSdkDep) -> SignUpResponse:
    try:
        result = await client.auth.admin.create_user(
            {
                "email": body.email,
                "password": body.password,
                "email_confirm": settings.signup_email_confirm,
            }
        )

    except AuthWeakPasswordError as exc:
        raise_sign_up_weak_password_sdk(exc=exc)

    except AuthApiError as exc:
        if exc.code in ("email_exists", "user_already_exists", "phone_exists"):
            raise_sign_up_email_already_exists(cause=exc)

        if exc.code == "weak_password":
            raise_sign_up_weak_password_api(exc=exc)

        raise_sign_up_auth_api_error(exc)

    user = result.user
    return SignUpResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
    )
