from uuid import UUID

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, status

from app.api.v1.endpoints.auth.exceptions import (
    cognito_error_code,
    raise_cognito_error,
    raise_sign_in_transport_unavailable,
    raise_sign_up_email_already_exists,
)
from app.core.cognito import call_idp, secret_hash
from app.core.config import settings
from app.core.deps import SupabaseSdkDep
from app.repositories.profiles import upsert_profile_patch
from app.schemas.account import AccountProfileUpdate
from app.schemas.auth import SignUpRequest, SignUpResponse
from app.utils.exceptions import raise_bad_request

router = APIRouter()


@router.post("/sign-up", status_code=status.HTTP_201_CREATED)
async def sign_up(body: SignUpRequest, client: SupabaseSdkDep) -> SignUpResponse:
    first_name = body.first_name.strip()
    last_name = body.last_name.strip()
    if not first_name or not last_name:
        raise_bad_request("First name and last name are required.")

    email = str(body.email)
    try:
        result = await call_idp(
            "sign_up",
            ClientId=settings.cognito_client_id,
            SecretHash=secret_hash(email),
            Username=email,
            Password=body.password,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "given_name", "Value": first_name},
                {"Name": "family_name", "Value": last_name},
            ],
        )

    except ClientError as exc:
        if cognito_error_code(exc) == "UsernameExistsException":
            raise_sign_up_email_already_exists(cause=exc)
        raise_cognito_error(exc)

    except BotoCoreError as exc:
        raise_sign_in_transport_unavailable(cause=exc)

    user_id = result["UserSub"]
    await upsert_profile_patch(
        client,
        UUID(user_id),
        AccountProfileUpdate(email=email, first_name=first_name, last_name=last_name),
    )
    return SignUpResponse(
        id=user_id,
        email=email,
        confirmation_required=not result["UserConfirmed"],
    )
