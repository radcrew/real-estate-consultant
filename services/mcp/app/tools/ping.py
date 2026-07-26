from __future__ import annotations

import logging

import httpx
from mcp.server.fastmcp import FastMCP

from app.client import BackendClient
from app.tools._common import error_text, ok_text

logger = logging.getLogger(__name__)


def register_ping_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def ping_backend() -> dict:
        """Health-check the radestate FastAPI backend (GET /api/v1/ping).

        Use this to verify BACKEND_API_URL is reachable before calling other tools.
        No authentication is required for ping.
        """
        client = BackendClient()
        try:
            data = await client.ping()
            return ok_text(data)
        except httpx.HTTPStatusError as exc:
            logger.warning("ping_backend HTTP %s", exc.response.status_code)
            return error_text(
                f"Backend returned HTTP {exc.response.status_code}: {exc.response.text[:300]}",
            )
        except httpx.RequestError as exc:
            logger.warning("ping_backend request failed: %s", exc)
            return error_text(f"Could not reach backend: {exc}")
        except Exception as exc:  # noqa: BLE001 — surface to host, never crash stdio
            logger.exception("ping_backend unexpected error")
            return error_text(f"Unexpected error: {exc}")
