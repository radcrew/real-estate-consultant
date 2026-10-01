
from __future__ import annotations

from typing import Annotated

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.v1.endpoints.account.exceptions import (
    raise_account_new_password_same_as_current,
    raise_account_password_change_needs_session,
    raise_account_password_managed_by_google,
)
from app.api.v1.endpoints.auth.exceptions import (
    cognito_error_code,
    raise_cognito_error,
    raise_sign_in_transport_unavailable,
)
from app.core.cognito import call_idp
from app.core.deps import CurrentUser
from app.repositories.exceptions import raise_current_password_incorrect
from app.schemas.account import AccountPasswordChangeRequest

router = APIRouter(tags=["account"])

_http_bearer = HTTPBearer(auto_error=False)


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def change_account_password(
    body: AccountPasswordChangeRequest,
    current_user: CurrentUser,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
) -> Response:
    # Cognito's ChangePassword is authorised by the user's own access token, which an
    # MCP API key caller does not have.
    if current_user.username is None or credentials is None:
        raise_account_password_change_needs_session()
    # Federated users have no Cognito password; Google owns their credentials.
    if current_user.username.startswith("google_"):
        raise_account_password_managed_by_google()

    if body.current_password == body.new_password:
        raise_account_new_password_same_as_current()

    try:
        await call_idp(
            "change_password",
            PreviousPassword=body.current_password,
            ProposedPassword=body.new_password,
            AccessToken=credentials.credentials.strip(),
        )

    except ClientError as exc:
        # The token was verified moments ago, so NotAuthorized means the old password.
        if cognito_error_code(exc) == "NotAuthorizedException":
            raise_current_password_incorrect(cause=exc)
        raise_cognito_error(exc)

    except BotoCoreError as exc:
        raise_sign_in_transport_unavailable(cause=exc)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
