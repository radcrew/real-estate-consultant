"""MCP resources — readable context backed by the FastAPI backend."""

from __future__ import annotations

import json
import logging

from mcp.server.fastmcp import FastMCP

from app.client import BackendClient
from app.client.errors import AuthRequiredError
from app.tools._common import compact_search_response

logger = logging.getLogger(__name__)


def register_resources(mcp: FastMCP) -> None:
    @mcp.resource("listing://{property_id}")
    async def listing_resource(property_id: str) -> str:
        """Normalized listing JSON for a property id."""
        client = BackendClient()
        try:
            data = await client.get_listing(property_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("listing_resource failed: %s", exc)
            return json.dumps({"error": str(exc)}, default=str)
        return json.dumps(data, indent=2, default=str)

    @mcp.resource("search://{session_profile_id}")
    async def search_resource(session_profile_id: str) -> str:
        """Current criteria + compact top matches for a search profile."""
        client = BackendClient()
        try:
            data = await client.search_properties(session_profile_id, limit=10, offset=0)
            payload = compact_search_response(data)
        except AuthRequiredError as exc:
            return json.dumps({"error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            logger.warning("search_resource failed: %s", exc)
            return json.dumps({"error": str(exc)}, default=str)
        return json.dumps(payload, indent=2, default=str)

    @mcp.resource("intake://{session_id}")
    async def intake_resource(session_id: str) -> str:
        """Intake session status, criteria, and next question."""
        client = BackendClient()
        try:
            data = await client.get_intake_session(session_id)
        except AuthRequiredError as exc:
            return json.dumps({"error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            logger.warning("intake_resource failed: %s", exc)
            return json.dumps({"error": str(exc)}, default=str)
        return json.dumps(data, indent=2, default=str)
