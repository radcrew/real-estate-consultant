from uuid import UUID

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
from app.utils.exceptions import raise_bad_request
from app.repositories.profiles import upsert_profile_patch
from app.schemas.account import AccountProfileUpdate
from app.schemas.auth import SignUpRequest, SignUpResponse

router = APIRouter()


@router.post("/sign-up", status_code=status.HTTP_201_CREATED)
async def sign_up(body: SignUpRequest, client: SupabaseSdkDep) -> SignUpResponse:
    first_name = body.first_name.strip()
    last_name = body.last_name.strip()
    if not first_name or not last_name:
        raise_bad_request("First name and last name are required.")

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
    user_id = UUID(user.id)
    await upsert_profile_patch(
        client,
        user_id,
        AccountProfileUpdate(
            email=str(body.email),
            first_name=first_name,
            last_name=last_name,
        ),
    )
    return SignUpResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
    )
