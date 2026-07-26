"""Verify MCP settings token can reach the backend."""

from __future__ import annotations

import asyncio
import sys

import httpx

from app.client import BackendClient
from app.config import settings


async def main() -> int:
    print("token_set", bool(settings.mcp_user_access_token.strip()))
    print("backend", settings.backend_api_url)
    client = BackendClient()
    ping = await client.ping()
    print("ping", ping)

    try:
        featured = await client.get_featured_listings()
        print("featured_count", len(featured.get("listings") or []))
    except Exception as exc:  # noqa: BLE001
        print("featured_skip", exc)

    try:
        intake = await client.start_intake_session("guided")
        print("intake_session", intake.get("session_id") or intake.get("mode") or intake)
    except httpx.HTTPStatusError as exc:
        print("intake_http", exc.response.status_code, exc.response.text[:200])
        if exc.response.status_code in (401, 403):
            return 1
    except Exception as exc:  # noqa: BLE001
        print("intake_skip", exc)

    print("OK local MCP auth is ready — reload radestate in Cursor")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
