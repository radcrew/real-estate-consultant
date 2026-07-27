import httpx
import pytest
import respx
from mcp.server.fastmcp import FastMCP

from app.server import create_server
from app.tools.intake import register_intake_tools
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
async def test_start_and_get_intake() -> None:
    respx.post(f"{BASE}/api/v1/intake-sessions/").mock(
        return_value=httpx.Response(
            201,
            json={
                "mode": "guided",
                "session_id": "sess-1",
                "status": "in_progress",
                "current_index": 0,
                "total_questions": 5,
                "first_question": {"key": "location", "text": "Where?", "type": "text"},
            },
        ),
    )
    respx.get(f"{BASE}/api/v1/intake-sessions/sess-1").mock(
        return_value=httpx.Response(
            200,
            json={"id": "sess-1", "status": "in_progress", "criteria": {}},
        ),
    )
    mcp = FastMCP("test")
    register_intake_tools(mcp)
    original = _with_token()
    try:
        started = await _tool(mcp, "start_intake_session").fn(mode="guided")
        got = await _tool(mcp, "get_intake_session").fn(session_id="sess-1")
    finally:
        _restore_token(original)

    assert started.get("isError") is not True
    assert "sess-1" in started["content"][0]["text"]
    assert got.get("isError") is not True


@pytest.mark.asyncio
@respx.mock
async def test_answer_intake_guided_and_llm() -> None:
    respx.patch(f"{BASE}/api/v1/intake-sessions/sess-1/answers/guided").mock(
        return_value=httpx.Response(
            200,
            json={"session": {"id": "sess-1"}, "next_question": {"key": "size_sqft"}},
        ),
    )
    respx.post(f"{BASE}/api/v1/intake-sessions/sess-1/answers/llm").mock(
        return_value=httpx.Response(
            200,
            json={"mode": "llm", "is_complete": False, "missing_fields": ["size_sqft"]},
        ),
    )
    mcp = FastMCP("test")
    register_intake_tools(mcp)
    original = _with_token()
    try:
        missing = await _tool(mcp, "answer_intake").fn(
            session_id="sess-1",
            mode="guided",
        )
        guided = await _tool(mcp, "answer_intake").fn(
            session_id="sess-1",
            mode="guided",
            key="location",
            answers="Austin, TX",
        )
        llm = await _tool(mcp, "answer_intake").fn(
            session_id="sess-1",
            mode="llm",
            text="Looking for warehouse near Austin",
        )
    finally:
        _restore_token(original)

    assert missing["isError"] is True
    assert guided.get("isError") is not True
    assert "size_sqft" in guided["content"][0]["text"]
    assert llm.get("isError") is not True


@pytest.mark.asyncio
@respx.mock
async def test_complete_intake() -> None:
    respx.post(f"{BASE}/api/v1/intake-sessions/sess-1/complete").mock(
        return_value=httpx.Response(
            200,
            json={"id": "sess-1", "status": "completed", "search_profile_id": "sp-1"},
        ),
    )
    mcp = FastMCP("test")
    register_intake_tools(mcp)
    original = _with_token()
    try:
        result = await _tool(mcp, "complete_intake").fn(session_id="sess-1")
    finally:
        _restore_token(original)
    assert result.get("isError") is not True
    assert "sp-1" in result["content"][0]["text"]


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


def test_create_server_registers_phase2() -> None:
    mcp = create_server()
    for name in (
        "start_intake_session",
        "get_intake_session",
        "answer_intake",
        "complete_intake",
        "generate_outreach_draft",
        "get_outreach_draft",
        "update_outreach_draft",
    ):
        assert mcp._tool_manager.get_tool(name) is not None

    # Resources + prompts registered
    assert mcp._resource_manager is not None
    assert mcp._prompt_manager is not None
