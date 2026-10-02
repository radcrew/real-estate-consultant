from __future__ import annotations

from typing import Annotated
from uuid import UUID

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.v1.endpoints.account.exceptions import (
    raise_account_email_in_use,
    raise_account_email_managed_by_google,
    raise_account_no_fields_to_update,
)
from app.api.v1.endpoints.auth.exceptions import (
    cognito_error_code,
    raise_cognito_error,
    raise_invalid_verification_code,
    raise_sign_in_transport_unavailable,
    raise_verification_code_expired,
)
from app.core.cognito import call_idp
from app.core.deps import CurrentUser, SessionAccessToken, SupabaseSdkDep, session_access_token
from app.domain.account_profile import account_profile_response
from app.models.auth_user import AuthUser
from app.models.profile import profile_from_row
from app.repositories.profiles import (
    PROFILE_PATCH_DB_COLUMNS,
    get_profile_row,
    upsert_profile_patch,
)
from app.schemas.account import (
    AccountEmailVerifyRequest,
    AccountProfileResponse,
    AccountProfileUpdate,
)
from supabase import AsyncClient

router = APIRouter()

_http_bearer = HTTPBearer(auto_error=False)


async def _profile_response(
    client: AsyncClient,
    current_user: AuthUser,
    *,
    email_change_pending: bool = False,
) -> AccountProfileResponse:
    raw = await get_profile_row(client, UUID(current_user.id))
    response = account_profile_response(user=current_user, profile=profile_from_row(raw))
    response.email_change_pending = email_change_pending
    return response


async def _request_email_change(access_token: str, new_email: str) -> None:
    """Cognito emails a code to the new address; profiles.email changes on verification."""
    try:
        await call_idp(
            "update_user_attributes",
            AccessToken=access_token,
            UserAttributes=[{"Name": "email", "Value": new_email}],
        )
    except ClientError as exc:
        if cognito_error_code(exc) == "AliasExistsException":
            raise_account_email_in_use(cause=exc)
        raise_cognito_error(exc)
    except BotoCoreError as exc:
        raise_sign_in_transport_unavailable(cause=exc)


@router.get("/profile", response_model=AccountProfileResponse)
async def get_account_profile(
    current_user: CurrentUser,
    client: SupabaseSdkDep,
) -> AccountProfileResponse:
    return await _profile_response(client, current_user)


@router.patch("/profile", response_model=AccountProfileResponse)
async def update_account_profile(
    body: AccountProfileUpdate,
    current_user: CurrentUser,
    client: SupabaseSdkDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
) -> AccountProfileResponse:
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise_account_no_fields_to_update()

    new_email = updates.pop("email", None)
    email_change_pending = False
    stored = await get_profile_row(client, UUID(current_user.id)) if new_email else None
    if new_email is not None and str(new_email) != (stored or {}).get("email"):
        if (current_user.username or "").startswith("google_"):
            raise_account_email_managed_by_google()
        access_token = session_access_token(current_user, credentials)
        await _request_email_change(access_token, str(new_email))
        email_change_pending = True

    if set(updates) & PROFILE_PATCH_DB_COLUMNS:
        await upsert_profile_patch(client, UUID(current_user.id), AccountProfileUpdate(**updates))

    return await _profile_response(
        client, current_user, email_change_pending=email_change_pending
    )


@router.post("/email/verify", response_model=AccountProfileResponse)
async def verify_account_email(
    body: AccountEmailVerifyRequest,
    current_user: CurrentUser,
    access_token: SessionAccessToken,
    client: SupabaseSdkDep,
) -> AccountProfileResponse:
    try:
        await call_idp(
            "verify_user_attribute",
            AccessToken=access_token,
            AttributeName="email",
            Code=body.code.strip(),
        )
        cognito_user = await call_idp("get_user", AccessToken=access_token)
    except ClientError as exc:
        code = cognito_error_code(exc)
        if code == "CodeMismatchException":
            raise_invalid_verification_code(cause=exc)
        if code == "ExpiredCodeException":
            raise_verification_code_expired(cause=exc)
        raise_cognito_error(exc)
    except BotoCoreError as exc:
        raise_sign_in_transport_unavailable(cause=exc)

    attributes = {a["Name"]: a["Value"] for a in cognito_user.get("UserAttributes", [])}
    await upsert_profile_patch(
        client, UUID(current_user.id), AccountProfileUpdate(email=attributes["email"])
    )
    return await _profile_response(client, current_user)

