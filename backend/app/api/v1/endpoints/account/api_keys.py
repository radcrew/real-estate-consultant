"""CRUD for MCP API keys under ``/api/v1/account/api-keys``."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.v1.endpoints.account.exceptions import raise_mcp_api_key_not_found
from app.core.deps import CurrentUser, SupabaseSdkDep
from app.core.db_safe import SupabaseRequestError
from app.repositories.mcp_api_keys import (
    create_mcp_api_key,
    list_mcp_api_keys,
    revoke_mcp_api_key,
)
from app.schemas.account import (
    McpApiKeyCreatedResponse,
    McpApiKeyCreateRequest,
    McpApiKeyListResponse,
    McpApiKeyResponse,
)
from app.utils.exceptions import raise_service_unavailable

router = APIRouter(prefix="/api-keys", tags=["account"])


def _meta_response(row: dict) -> McpApiKeyResponse:
    return McpApiKeyResponse(
        id=UUID(str(row["id"])),
        name=str(row.get("name") or "default"),
        key_prefix=str(row.get("key_prefix") or ""),
        scopes=list(row.get("scopes") or ["*"]),
        created_at=str(row["created_at"]) if row.get("created_at") is not None else None,
        last_used_at=str(row["last_used_at"]) if row.get("last_used_at") is not None else None,
        revoked_at=str(row["revoked_at"]) if row.get("revoked_at") is not None else None,
        expires_at=str(row["expires_at"]) if row.get("expires_at") is not None else None,
    )


@router.post("", response_model=McpApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_account_mcp_api_key(
    body: McpApiKeyCreateRequest,
    current_user: CurrentUser,
    client: SupabaseSdkDep,
) -> McpApiKeyCreatedResponse:
    try:
        raw, row = await create_mcp_api_key(
            client,
            user_id=UUID(current_user.id),
            name=body.name,
        )
    except SupabaseRequestError as exc:
        raise_service_unavailable("Could not create MCP API key.", cause=exc)

    meta = _meta_response(row)
    return McpApiKeyCreatedResponse(
        id=meta.id,
        name=meta.name,
        key_prefix=meta.key_prefix,
        api_key=raw,
        scopes=meta.scopes,
        created_at=meta.created_at,
        expires_at=meta.expires_at,
    )


@router.get("", response_model=McpApiKeyListResponse)
async def list_account_mcp_api_keys(
    current_user: CurrentUser,
    client: SupabaseSdkDep,
) -> McpApiKeyListResponse:
    try:
        rows = await list_mcp_api_keys(client, UUID(current_user.id))
    except SupabaseRequestError as exc:
        raise_service_unavailable("Could not list MCP API keys.", cause=exc)
    return McpApiKeyListResponse(keys=[_meta_response(r) for r in rows])


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def revoke_account_mcp_api_key(
    key_id: UUID,
    current_user: CurrentUser,
    client: SupabaseSdkDep,
) -> Response:
    try:
        updated = await revoke_mcp_api_key(
            client,
            user_id=UUID(current_user.id),
            key_id=key_id,
        )
    except SupabaseRequestError as exc:
        raise_service_unavailable("Could not revoke MCP API key.", cause=exc)
    if updated is None:
        raise_mcp_api_key_not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
