"""Persistence for ``public.mcp_api_keys`` (Supabase PostgREST)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from supabase import AsyncClient

from app.core.config import settings
from app.core.db_safe import execute_db_safe
from app.domain.mcp_api_keys import (
    generate_mcp_api_key,
    hash_mcp_api_key,
    mcp_api_key_prefix,
    verify_mcp_api_key,
)
from app.utils.supabase.response import as_row_list, get_single_row

_SELECT_META = (
    "id, user_id, name, key_prefix, scopes, created_at, last_used_at, revoked_at, expires_at"
)
_SELECT_RESOLVE = f"{_SELECT_META}, key_hash"


def _pepper() -> str:
    return settings.mcp_api_key_pepper or ""


def _is_expired(row: dict[str, Any], *, now: datetime | None = None) -> bool:
    expires_at = row.get("expires_at")
    if not expires_at:
        return False
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    ref = now or datetime.now(timezone.utc)
    return expires_at <= ref


async def create_mcp_api_key(
    client: AsyncClient,
    *,
    user_id: UUID,
    name: str = "default",
    scopes: list[str] | None = None,
    expires_at: datetime | None = None,
) -> tuple[str, dict[str, Any]]:
    """Insert a new key. Returns ``(plaintext_once, metadata_row)``."""
    raw = generate_mcp_api_key()
    prefix = mcp_api_key_prefix(raw)
    key_hash = hash_mcp_api_key(raw, pepper=_pepper())
    payload: dict[str, Any] = {
        "user_id": str(user_id),
        "name": name.strip() or "default",
        "key_prefix": prefix,
        "key_hash": key_hash,
        "scopes": scopes or ["*"],
    }
    if expires_at is not None:
        payload["expires_at"] = expires_at.isoformat()

    result = await execute_db_safe(
        client.table("mcp_api_keys")
        .insert(payload)
        .execute(),
    )
    row = get_single_row(result, detail="Unexpected response creating MCP API key.")
    # Never return key_hash to callers.
    meta = {k: v for k, v in row.items() if k != "key_hash"}
    return raw, meta


async def list_mcp_api_keys(client: AsyncClient, user_id: UUID) -> list[dict[str, Any]]:
    result = await execute_db_safe(
        client.table("mcp_api_keys")
        .select(_SELECT_META)
        .eq("user_id", str(user_id))
        .order("created_at", desc=True)
        .execute(),
    )
    return as_row_list(result.data)


async def revoke_mcp_api_key(
    client: AsyncClient,
    *,
    user_id: UUID,
    key_id: UUID,
) -> dict[str, Any] | None:
    """Soft-revoke. Returns updated row or ``None`` if not found / not owned."""
    now = datetime.now(timezone.utc).isoformat()
    result = await execute_db_safe(
        client.table("mcp_api_keys")
        .update({"revoked_at": now})
        .eq("id", str(key_id))
        .eq("user_id", str(user_id))
        .is_("revoked_at", "null")
        .execute(),
    )
    rows = as_row_list(result.data)
    if not rows:
        return None
    return {k: v for k, v in rows[0].items() if k != "key_hash"}


async def resolve_mcp_api_key_user_id(
    client: AsyncClient,
    raw_key: str,
) -> UUID | None:
    """Verify raw key against active rows sharing its prefix. Returns user_id or None."""
    prefix = mcp_api_key_prefix(raw_key)
    result = await execute_db_safe(
        client.table("mcp_api_keys")
        .select(_SELECT_RESOLVE)
        .eq("key_prefix", prefix)
        .is_("revoked_at", "null")
        .execute(),
    )
    pepper = _pepper()
    for row in as_row_list(result.data):
        key_hash = row.get("key_hash")
        if not isinstance(key_hash, str):
            continue
        if not verify_mcp_api_key(raw_key, key_hash, pepper=pepper):
            continue
        if _is_expired(row):
            return None
        user_id = row.get("user_id")
        if not isinstance(user_id, str):
            return None
        return UUID(user_id)
    return None
