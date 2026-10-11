from typing import Annotated

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.v1.endpoints.auth.exceptions import (
    cognito_error_code,
    raise_cognito_error,
    raise_sign_in_transport_unavailable,
)
from app.core.cognito import call_idp
from app.core.exceptions import raise_auth_missing_bearer

router = APIRouter()

_http_bearer = HTTPBearer(auto_error=False)


@router.post("/sign-out", status_code=status.HTTP_204_NO_CONTENT)
async def sign_out(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
) -> Response:
    """Revoke the caller's refresh token and every access token issued from it.

    Google users' tokens carry this right only when ``aws.cognito.signin.user.admin``
    was requested at authorize time. The client clears its session whatever the outcome.
    """
    if credentials is None or not credentials.credentials.strip():
        raise_auth_missing_bearer()

    try:
        await call_idp("global_sign_out", AccessToken=credentials.credentials.strip())

    except ClientError as exc:
        # Already expired or revoked: the caller is signed out either way.
        if cognito_error_code(exc) != "NotAuthorizedException":
            raise_cognito_error(exc)

    except BotoCoreError as exc:
        raise_sign_in_transport_unavailable(cause=exc)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
