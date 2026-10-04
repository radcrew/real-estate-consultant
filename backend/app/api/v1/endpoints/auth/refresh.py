import jwt
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter

from app.api.v1.endpoints.auth.exceptions import (
    cognito_error_code,
    raise_cognito_error,
    raise_refresh_token_rejected,
    raise_sign_in_transport_unavailable,
)
from app.api.v1.endpoints.auth.sign_in import session_response
from app.core.cognito import call_idp, secret_hash
from app.core.config import settings
from app.core.deps import SupabaseSdkDep
from app.schemas.auth import RefreshRequest, SignInResponse

router = APIRouter()


@router.post("/refresh")
async def refresh(body: RefreshRequest, client: SupabaseSdkDep) -> SignInResponse:
    try:
        result = await call_idp(
            "initiate_auth",
            ClientId=settings.cognito_client_id,
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={
                "REFRESH_TOKEN": body.refresh_token,
                "SECRET_HASH": secret_hash(body.username),
            },
        )

    except ClientError as exc:
        # Expired, revoked, or signed for a different username.
        if cognito_error_code(exc) == "NotAuthorizedException":
            raise_refresh_token_rejected(cause=exc)
        raise_cognito_error(exc)

    except BotoCoreError as exc:
        raise_sign_in_transport_unavailable(cause=exc)

    auth = result["AuthenticationResult"]
    # The ID token came straight from Cognito over TLS; it is only read for display email.
    id_claims = jwt.decode(auth["IdToken"], options={"verify_signature": False})
    return await session_response(
        auth, client, email=id_claims.get("email"), refresh_token=body.refresh_token
    )
