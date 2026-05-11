
from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.core.deps import CurrentUser, SupabaseSdkDep
from app.exceptions.account_routes import (
    raise_account_new_password_same_as_current,
    raise_account_no_email_for_password_change,
)
from app.repositories.account import (
    update_auth_user_password,
    verify_current_email_password,
)
from app.schemas.account import AccountPasswordChangeRequest

router = APIRouter(prefix="/account", tags=["account"])

@router.post("/password", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def change_account_password(
    body: AccountPasswordChangeRequest,
    current_user: CurrentUser,
    client: SupabaseSdkDep,
) -> Response:
    email = (current_user.email or "").strip()
    if not email:
        raise_account_no_email_for_password_change()

    await verify_current_email_password(client, email=email, password=body.current_password)

    if body.current_password == body.new_password:
        raise_account_new_password_same_as_current()

    await update_auth_user_password(client, current_user.id, new_password=body.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
