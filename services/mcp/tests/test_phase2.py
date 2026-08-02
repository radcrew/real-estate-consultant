import httpx
import pytest
import respx
from mcp.server.fastmcp import FastMCP

from app.server import create_server
from app.tools.outreach import register_outreach_tools

BASE = "http://127.0.0.1:8888"
TOKEN = "test-user-jwt"


def _tool(mcp: FastMCP, name: str):
    tool = mcp._tool_manager.get_tool(name)
    assert tool is not None
    return tool


def _with_token():
    from app import config

    original = config.settings.mcp_user_access_token
    config.settings.mcp_user_access_token = TOKEN
    return original


def _restore_token(original: str) -> None:
    from app import config

    config.settings.mcp_user_access_token = original


@pytest.mark.asyncio
@respx.mock
async def test_outreach_draft_tools() -> None:
    respx.post(f"{BASE}/api/v1/outreach/drafts").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "d1",
                "property_id": "p1",
                "draft_email": "Hello broker...",
            },
        ),
    )
    respx.get(f"{BASE}/api/v1/outreach/drafts/d1").mock(
        return_value=httpx.Response(
            200,
            json={"id": "d1", "property_id": "p1", "draft_email": "Hello broker..."},
        ),
    )
    respx.get(f"{BASE}/api/v1/outreach/drafts/latest", params={"property_id": "p1"}).mock(
        return_value=httpx.Response(
            200,
            json={"id": "d1", "property_id": "p1", "draft_email": "Hello broker..."},
        ),
    )
    respx.patch(f"{BASE}/api/v1/outreach/drafts/d1").mock(
        return_value=httpx.Response(
            200,
            json={"id": "d1", "property_id": "p1", "draft_email": "Edited draft"},
        ),
    )
    mcp = FastMCP("test")
    register_outreach_tools(mcp)
    original = _with_token()
    try:
        created = await _tool(mcp, "generate_outreach_draft").fn(property_id="p1")
        by_id = await _tool(mcp, "get_outreach_draft").fn(draft_id="d1")
        by_prop = await _tool(mcp, "get_outreach_draft").fn(property_id="p1")
        missing = await _tool(mcp, "get_outreach_draft").fn()
        updated = await _tool(mcp, "update_outreach_draft").fn(
            draft_id="d1",
            draft_email="Edited draft",
        )
    finally:
        _restore_token(original)

    assert created.get("isError") is not True
    assert "Hello broker" in created["content"][0]["text"]
    assert by_id.get("isError") is not True
    assert by_prop.get("isError") is not True
    assert missing["isError"] is True
    assert updated.get("isError") is not True
    assert "Edited draft" in updated["content"][0]["text"]


def test_create_server_registers_outreach_tools() -> None:
    mcp = create_server()
    for name in (
        "generate_outreach_draft",
        "get_outreach_draft",
        "update_outreach_draft",
    ):
        assert mcp._tool_manager.get_tool(name) is not None

    assert mcp._resource_manager is not None
    assert mcp._prompt_manager is not None
