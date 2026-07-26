import httpx
import pytest
import respx
from mcp.server.fastmcp import FastMCP

from app.tools.admin import register_admin_tools

BASE = "http://127.0.0.1:8888"
TOKEN = "test-admin-jwt"


def _tool(mcp: FastMCP, name: str):
    tool = mcp._tool_manager.get_tool(name)
    assert tool is not None
    return tool


@pytest.mark.asyncio
@respx.mock
async def test_enqueue_ingest_and_list_submissions() -> None:
    respx.post(f"{BASE}/api/v1/admin/ingest").mock(
        return_value=httpx.Response(
            200,
            json={
                "job_id": "j1",
                "source": "loopnet-seed",
                "status": "pending",
                "idempotency_key": "loopnet-seed:2026-07-26",
            },
        ),
    )
    respx.get(f"{BASE}/api/v1/listing-submissions").mock(
        return_value=httpx.Response(
            200,
            json=[{"id": "s1", "status": "pending", "title": "Warehouse"}],
        ),
    )
    from app import config

    mcp = FastMCP("test")
    register_admin_tools(mcp)
    original = config.settings.mcp_user_access_token
    config.settings.mcp_user_access_token = TOKEN
    try:
        enqueued = await _tool(mcp, "enqueue_ingest").fn(source="loopnet-seed")
        listed = await _tool(mcp, "list_listing_submissions").fn()
    finally:
        config.settings.mcp_user_access_token = original

    assert enqueued.get("isError") is not True
    assert "j1" in enqueued["content"][0]["text"]
    assert listed.get("isError") is not True
    assert "Warehouse" in listed["content"][0]["text"]


@pytest.mark.asyncio
@respx.mock
async def test_admin_forbidden() -> None:
    respx.post(f"{BASE}/api/v1/admin/ingest").mock(
        return_value=httpx.Response(403, json={"detail": "Admin required"}),
    )
    from app import config

    mcp = FastMCP("test")
    register_admin_tools(mcp)
    original = config.settings.mcp_user_access_token
    config.settings.mcp_user_access_token = TOKEN
    try:
        result = await _tool(mcp, "enqueue_ingest").fn()
    finally:
        config.settings.mcp_user_access_token = original
    assert result["isError"] is True
    assert "Forbidden" in result["content"][0]["text"]
