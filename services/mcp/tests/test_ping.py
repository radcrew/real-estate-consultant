import httpx
import pytest
import respx

from app.client.backend import BackendClient
from app.server import create_server
from app.tools.ping import register_ping_tools


@pytest.mark.asyncio
@respx.mock
async def test_backend_client_ping() -> None:
    route = respx.get("http://127.0.0.1:8888/api/v1/ping").mock(
        return_value=httpx.Response(200, json={"message": "pong"}),
    )
    client = BackendClient(base_url="http://127.0.0.1:8888", access_token="")
    data = await client.ping()
    assert data == {"message": "pong"}
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_ping_backend_tool_success() -> None:
    respx.get("http://127.0.0.1:8888/api/v1/ping").mock(
        return_value=httpx.Response(200, json={"message": "pong"}),
    )
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("test")
    register_ping_tools(mcp)
    tool = mcp._tool_manager.get_tool("ping_backend")
    assert tool is not None
    result = await tool.fn()
    assert result.get("isError") is not True
    assert "pong" in result["content"][0]["text"]


@pytest.mark.asyncio
@respx.mock
async def test_ping_backend_tool_unreachable() -> None:
    respx.get("http://127.0.0.1:8888/api/v1/ping").mock(
        side_effect=httpx.ConnectError("connection refused"),
    )
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("test")
    register_ping_tools(mcp)
    tool = mcp._tool_manager.get_tool("ping_backend")
    result = await tool.fn()
    assert result["isError"] is True
    assert "Could not reach backend" in result["content"][0]["text"]


def test_create_server_registers_ping() -> None:
    mcp = create_server()
    tool = mcp._tool_manager.get_tool("ping_backend")
    assert tool is not None
