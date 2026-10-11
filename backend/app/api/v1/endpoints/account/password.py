
from __future__ import annotations

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Response, status

from app.api.v1.endpoints.account.exceptions import (
    raise_account_new_password_same_as_current,
    raise_account_password_change_needs_password_sign_in,
    raise_account_password_managed_by_google,
)
from app.api.v1.endpoints.auth.exceptions import (
    access_token_rejected,
    cognito_error_code,
    lacks_admin_scope,
    raise_cognito_error,
    raise_sign_in_transport_unavailable,
)
from app.core.cognito import call_idp, is_google_username
from app.core.deps import CurrentUser, SessionAccessToken
from app.repositories.exceptions import raise_current_password_incorrect
from app.schemas.account import AccountPasswordChangeRequest

router = APIRouter(tags=["account"])


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def change_account_password(
    body: AccountPasswordChangeRequest,
    current_user: CurrentUser,
    access_token: SessionAccessToken,
) -> Response:
    # Federated users have no Cognito password; Google owns their credentials.
    if is_google_username(current_user.username):
        raise_account_password_managed_by_google()

    if body.current_password == body.new_password:
        raise_account_new_password_same_as_current()

    try:
        await call_idp(
            "change_password",
            PreviousPassword=body.current_password,
            ProposedPassword=body.new_password,
            AccessToken=access_token,
        )

    except ClientError as exc:
        # A password user whose Google identity is linked can hold a Google-issued token,
        # which Cognito refuses for lacking the admin scope.
        if lacks_admin_scope(exc):
            raise_account_password_change_needs_password_sign_in(cause=exc)
        # A revoked or expired token (e.g. signed out in another tab) is a 401, not a
        # wrong password; raise_cognito_error maps it.
        if cognito_error_code(exc) == "NotAuthorizedException" and not access_token_rejected(exc):
            raise_current_password_incorrect(cause=exc)
        raise_cognito_error(exc)

    except BotoCoreError as exc:
        raise_sign_in_transport_unavailable(cause=exc)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
