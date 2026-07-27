import httpx
import pytest
import respx
from mcp.server.fastmcp import FastMCP

from app.client.backend import BackendClient
from app.client.errors import AuthRequiredError
from app.server import create_server
from app.tools.account import register_account_tools
from app.tools.agents import register_agents_tools
from app.tools.fit import register_fit_tools
from app.tools.listings import register_listings_tools
from app.tools.search import register_search_tools

BASE = "http://127.0.0.1:8888"
TOKEN = "test-user-jwt"


def _tool(mcp: FastMCP, name: str):
    tool = mcp._tool_manager.get_tool(name)
    assert tool is not None
    return tool


@pytest.mark.asyncio
@respx.mock
async def test_quick_search_creates_session_and_returns_matches() -> None:
    quick = respx.post(f"{BASE}/api/v1/search/quick").mock(
        return_value=httpx.Response(200, json={"search_profile_id": "sess-q"}),
    )
    search = respx.get(f"{BASE}/api/v1/search/sess-q").mock(
        return_value=httpx.Response(
            200,
            json={
                "criteria": {},
                "total": 1,
                "limit": 10,
                "offset": 0,
                "results": [
                    {
                        "property": {
                            "id": "prop-la",
                            "city": "Santa Fe Springs",
                            "state": "CA",
                            "property_type": "Industrial",
                            "price": 2476000,
                        },
                        "match_score": 88.0,
                    },
                ],
            },
        ),
    )
    mcp = FastMCP("test")
    register_search_tools(mcp)
    from app import config

    original = config.settings.mcp_user_access_token
    config.settings.mcp_user_access_token = TOKEN
    try:
        result = await _tool(mcp, "quick_search").fn(
            location="Los Angeles, CA",
            property_types=["Industrial"],
            price_max=4_000_000,
            limit=10,
        )
    finally:
        config.settings.mcp_user_access_token = original

    assert result.get("isError") is not True
    assert quick.called
    assert search.called
    body = quick.calls.last.request.content
    assert b"Los Angeles" in body
    assert b"Industrial" in body
    text = result["content"][0]["text"]
    assert "prop-la" in text
    assert "sess-q" in text
    assert "search_profile_id" in text


@pytest.mark.asyncio
@respx.mock
async def test_search_properties_compacts_and_auths() -> None:
    route = respx.get(f"{BASE}/api/v1/search/sess-1").mock(
        return_value=httpx.Response(
            200,
            json={
                "criteria": {},
                "total": 1,
                "limit": 10,
                "offset": 0,
                "results": [
                    {
                        "property": {
                            "id": "prop-1",
                            "city": "Austin",
                            "description": "long text should not appear in compact",
                        },
                        "match_score": 91.0,
                    },
                ],
            },
        ),
    )
    mcp = FastMCP("test")
    register_search_tools(mcp)
    # Patch settings via client ctor by monkeypatching tool's BackendClient — call client directly
    # and also exercise tool with a client that has token through env/settings.
    client = BackendClient(base_url=BASE, access_token=TOKEN)
    data = await client.search_properties("sess-1", limit=10)
    assert data["results"][0]["property"]["id"] == "prop-1"
    assert route.called
    assert route.calls.last.request.headers["Authorization"] == f"Bearer {TOKEN}"

    # Tool uses settings token; inject via BackendClient default — call tool.fn with patched client
    # by setting env is heavy; instead invoke transform path via tool after respx + settings token.
    from app import config

    original = config.settings.mcp_user_access_token
    config.settings.mcp_user_access_token = TOKEN
    try:
        result = await _tool(mcp, "search_properties").fn(session_profile_id="sess-1")
    finally:
        config.settings.mcp_user_access_token = original

    assert result.get("isError") is not True
    text = result["content"][0]["text"]
    assert "prop-1" in text
    assert "long text should not appear" not in text


@pytest.mark.asyncio
@respx.mock
async def test_search_requires_auth() -> None:
    mcp = FastMCP("test")
    register_search_tools(mcp)
    from app import config

    original_jwt = config.settings.mcp_user_access_token
    original_key = config.settings.mcp_api_key
    original_transport = config.settings.mcp_transport
    config.settings.mcp_user_access_token = ""
    config.settings.mcp_api_key = ""
    config.settings.mcp_transport = "stdio"
    try:
        result = await _tool(mcp, "search_properties").fn(session_profile_id="sess-1")
    finally:
        config.settings.mcp_user_access_token = original_jwt
        config.settings.mcp_api_key = original_key
        config.settings.mcp_transport = original_transport
    assert result["isError"] is True
    assert "MCP_API_KEY" in result["content"][0]["text"]


@pytest.mark.asyncio
@respx.mock
async def test_update_search_criteria() -> None:
    route = respx.put(f"{BASE}/api/v1/search/sess-1").mock(
        return_value=httpx.Response(200, json={"status": "in_progress", "criteria": {}}),
    )
    client = BackendClient(base_url=BASE, access_token=TOKEN)
    data = await client.update_search_criteria("sess-1", {"location": "Austin, TX"})
    assert data["status"] == "in_progress"
    assert route.called
    assert route.calls.last.request.content  # body present


@pytest.mark.asyncio
@respx.mock
async def test_get_listing_and_featured() -> None:
    respx.get(f"{BASE}/api/v1/listings/prop-1").mock(
        return_value=httpx.Response(
            200,
            json={"property": {"id": "prop-1", "city": "Austin"}, "images": ["https://x"]},
        ),
    )
    respx.get(f"{BASE}/api/v1/listings/featured").mock(
        return_value=httpx.Response(
            200,
            json={"listings": [{"property": {"id": "f1", "city": "Dallas"}, "images": []}]},
        ),
    )
    mcp = FastMCP("test")
    register_listings_tools(mcp)

    listing = await _tool(mcp, "get_listing").fn(property_id="prop-1")
    assert listing.get("isError") is not True
    assert "prop-1" in listing["content"][0]["text"]

    featured = await _tool(mcp, "get_featured_listings").fn()
    assert featured.get("isError") is not True
    assert "Dallas" in featured["content"][0]["text"]


@pytest.mark.asyncio
@respx.mock
async def test_explain_fit() -> None:
    respx.post(f"{BASE}/api/v1/search/sess-1/fit/prop-1").mock(
        return_value=httpx.Response(
            200,
            json={
                "property_id": "prop-1",
                "score": {"location": 0.9, "price": 0.8, "size": 0.7, "total": 85.0},
                "summary": "Strong location fit.",
                "strengths": ["Near target market"],
                "considerations": ["Slightly over budget"],
            },
        ),
    )
    from app import config

    mcp = FastMCP("test")
    register_fit_tools(mcp)
    original = config.settings.mcp_user_access_token
    config.settings.mcp_user_access_token = TOKEN
    try:
        result = await _tool(mcp, "explain_fit").fn(
            session_profile_id="sess-1",
            property_id="prop-1",
        )
    finally:
        config.settings.mcp_user_access_token = original
    assert result.get("isError") is not True
    assert "Strong location fit" in result["content"][0]["text"]


@pytest.mark.asyncio
@respx.mock
async def test_list_saved_and_get_agent() -> None:
    respx.get(f"{BASE}/api/v1/account/saved").mock(
        return_value=httpx.Response(200, json={"property_ids": ["a", "b"]}),
    )
    respx.get(f"{BASE}/api/v1/agents/Ada%20Broker").mock(
        return_value=httpx.Response(
            200,
            json={
                "name": "Ada Broker",
                "email": "ada@example.com",
                "phone": None,
                "properties": [{"id": "p1", "city": "Austin"}],
            },
        ),
    )
    from app import config

    mcp = FastMCP("test")
    register_account_tools(mcp)
    register_agents_tools(mcp)
    original = config.settings.mcp_user_access_token
    config.settings.mcp_user_access_token = TOKEN
    try:
        saved = await _tool(mcp, "list_saved_listings").fn()
        agent = await _tool(mcp, "get_agent").fn(broker="Ada Broker")
    finally:
        config.settings.mcp_user_access_token = original

    assert saved.get("isError") is not True
    assert "property_ids" in saved["content"][0]["text"]
    assert agent.get("isError") is not True
    assert "Ada Broker" in agent["content"][0]["text"]


def test_backend_client_require_auth() -> None:
    client = BackendClient(base_url=BASE, access_token="")
    with pytest.raises(AuthRequiredError):
        client.require_auth()


def test_create_server_registers_phase1_tools() -> None:
    mcp = create_server()
    for name in (
        "ping_backend",
        "quick_search",
        "search_properties",
        "update_search_criteria",
        "get_listing",
        "get_featured_listings",
        "explain_fit",
        "list_saved_listings",
        "get_agent",
    ):
        assert mcp._tool_manager.get_tool(name) is not None
