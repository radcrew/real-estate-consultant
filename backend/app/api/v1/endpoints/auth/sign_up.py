from fastapi import APIRouter, HTTPException, status
from supabase import AuthApiError, AuthWeakPasswordError

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
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": exc.message,
                "reasons": exc.reasons,
            },
        ) from exc

    except AuthApiError as exc:
        if exc.code in ("email_exists", "user_already_exists", "phone_exists"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            ) from exc

        if exc.code == "weak_password":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.message,
            ) from exc

        raise HTTPException(
            status_code=exc.status if 400 <= exc.status < 600 else status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        ) from exc

    user = result.user
    return SignUpResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
    )
