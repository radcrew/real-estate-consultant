"""Persistence for ``public.mcp_api_keys`` (Supabase PostgREST)."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from app.core.config import settings
from app.core.db_safe import execute_db_safe
from app.domain.mcp_api_keys import (
    generate_mcp_api_key,
    hash_mcp_api_key,
    mcp_api_key_prefix,
    normalize_mcp_scopes,
    verify_mcp_api_key,
)
from app.utils.supabase.response import as_row_list, get_single_row
from supabase import AsyncClient

logger = logging.getLogger(__name__)

_SELECT_META = (
    "id, user_id, name, key_prefix, scopes, created_at, last_used_at, revoked_at, expires_at"
)
_SELECT_RESOLVE = f"{_SELECT_META}, key_hash"

# Sample last_used_at updates to avoid a write on every authenticated request.
_LAST_USED_SAMPLE_RATE = 0.1
_LAST_USED_MIN_INTERVAL = timedelta(minutes=5)


@dataclass(frozen=True, slots=True)
class ResolvedMcpApiKey:
    user_id: UUID
    key_id: UUID
    key_prefix: str
    scopes: list[str]


def _pepper() -> str:
    return settings.mcp_api_key_pepper or ""


def _is_expired(row: dict[str, Any], *, now: datetime | None = None) -> bool:
    expires_at = row.get("expires_at")
    if not expires_at:
        return False
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    ref = now or datetime.now(UTC)
    return expires_at <= ref


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return None


def _should_touch_last_used(row: dict[str, Any], *, now: datetime) -> bool:
    if random.random() > _LAST_USED_SAMPLE_RATE:
        return False
    last = _parse_dt(row.get("last_used_at"))
    if last is None:
        return True
    return (now - last) >= _LAST_USED_MIN_INTERVAL


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
        "scopes": normalize_mcp_scopes(scopes),
    }
    if expires_at is not None:
        payload["expires_at"] = expires_at.isoformat()

    result = await execute_db_safe(
        client.table("mcp_api_keys")
        .insert(payload)
        .execute(),
    )
    row = get_single_row(result, detail="Unexpected response creating MCP API key.")
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
    now = datetime.now(UTC).isoformat()
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


async def touch_mcp_api_key_last_used(client: AsyncClient, key_id: UUID) -> None:
    now = datetime.now(UTC).isoformat()
    await execute_db_safe(
        client.table("mcp_api_keys")
        .update({"last_used_at": now})
        .eq("id", str(key_id))
        .execute(),
    )


async def resolve_mcp_api_key(
    client: AsyncClient,
    raw_key: str,
) -> ResolvedMcpApiKey | None:
    """Verify raw key; optionally sample-update ``last_used_at``."""
    prefix = mcp_api_key_prefix(raw_key)
    result = await execute_db_safe(
        client.table("mcp_api_keys")
        .select(_SELECT_RESOLVE)
        .eq("key_prefix", prefix)
        .is_("revoked_at", "null")
        .execute(),
    )
    pepper = _pepper()
    now = datetime.now(UTC)
    for row in as_row_list(result.data):
        key_hash = row.get("key_hash")
        if not isinstance(key_hash, str):
            continue
        if not verify_mcp_api_key(raw_key, key_hash, pepper=pepper):
            continue
        if _is_expired(row, now=now):
            return None
        user_id = row.get("user_id")
        key_id = row.get("id")
        if not isinstance(user_id, str) or not isinstance(key_id, str):
            return None
        scopes = list(row.get("scopes") or ["*"])
        resolved = ResolvedMcpApiKey(
            user_id=UUID(user_id),
            key_id=UUID(key_id),
            key_prefix=str(row.get("key_prefix") or prefix),
            scopes=scopes,
        )
        if _should_touch_last_used(row, now=now):
            try:
                await touch_mcp_api_key_last_used(client, resolved.key_id)
            except Exception:  # noqa: BLE001 — never fail auth on telemetry write
                logger.debug("mcp_api_key last_used_at update failed", exc_info=True)
        logger.info(
            "mcp_api_key_auth",
            extra={
                "key_id": str(resolved.key_id),
                "key_prefix": resolved.key_prefix,
                "user_id": str(resolved.user_id),
                "scopes": resolved.scopes,
            },
        )
        return resolved
    return None


async def resolve_mcp_api_key_user_id(
    client: AsyncClient,
    raw_key: str,
) -> UUID | None:
    """Backward-compatible wrapper — prefer ``resolve_mcp_api_key``."""
    resolved = await resolve_mcp_api_key(client, raw_key)
    return resolved.user_id if resolved else None
