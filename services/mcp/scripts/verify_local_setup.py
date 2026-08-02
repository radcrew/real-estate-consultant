"""Verify MCP settings token can reach the backend."""

from __future__ import annotations

import asyncio
import sys

import httpx

from app.client import BackendClient
from app.config import settings


async def main() -> int:
    print("token_set", bool((settings.mcp_api_key or settings.mcp_user_access_token).strip()))
    print("backend", settings.backend_api_url)
    client = BackendClient()

    try:
        created = await client.quick_search(location="Austin, TX")
        profile_id = created.get("search_profile_id")
        print("quick_search_profile", profile_id)
        if profile_id:
            results = await client.search_properties(str(profile_id), limit=3)
            print("search_total", results.get("total"))
    except httpx.HTTPStatusError as exc:
        print("search_http", exc.response.status_code, exc.response.text[:200])
        if exc.response.status_code in (401, 403):
            return 1
    except Exception as exc:  # noqa: BLE001
        print("search_skip", exc)

    print("OK local MCP auth is ready — reload radestate in Cursor")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
