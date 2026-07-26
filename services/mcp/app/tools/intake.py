from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from app.client import BackendClient
from app.tools._common import error_text, run_backend


def register_intake_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def start_intake_session(mode: Literal["guided", "llm"] = "guided") -> dict:
        """Start a new intake session (WRITE — creates a session row).

        Requires MCP_USER_ACCESS_TOKEN.

        Args:
            mode: "guided" uses the questionnaire; "llm" returns an open chat prompt.
        """
        client = BackendClient()
        return await run_backend(
            "start_intake_session",
            lambda: client.start_intake_session(mode),
        )

    @mcp.tool()
    async def get_intake_session(session_id: str) -> dict:
        """Get intake session status, criteria, and next question (read-only).

        Requires MCP_USER_ACCESS_TOKEN.

        Args:
            session_id: Intake session UUID from start_intake_session.
        """
        client = BackendClient()
        return await run_backend(
            "get_intake_session",
            lambda: client.get_intake_session(session_id),
        )

    @mcp.tool()
    async def answer_intake(
        session_id: str,
        mode: Literal["guided", "llm"] = "guided",
        key: str | None = None,
        answers: Any | None = None,
        text: str | None = None,
    ) -> dict:
        """Submit an intake answer (WRITE — mutates session criteria).

        Requires MCP_USER_ACCESS_TOKEN.

        Guided mode: provide `key` (question key) and `answers` (string, list,
        range object, or location object — same shapes as the product UI).

        LLM mode: provide `text` (natural-language user message). Backend parses
        criteria and returns next_question / is_complete.

        Args:
            session_id: Intake session UUID.
            mode: "guided" or "llm".
            key: Guided question key (required when mode=guided).
            answers: Guided answer payload (required when mode=guided).
            text: Free-text input (required when mode=llm).
        """
        client = BackendClient()
        if mode == "guided":
            if not key or answers is None:
                return error_text(
                    "guided mode requires key and answers "
                    '(e.g. key="location", answers="Austin, TX").',
                )

            async def _guided() -> dict[str, Any]:
                return await client.answer_intake_guided(
                    session_id,
                    key=key,
                    answers=answers,
                )

            return await run_backend("answer_intake", _guided)

        if not text or not text.strip():
            return error_text("llm mode requires text (natural-language user message).")

        async def _llm() -> dict[str, Any]:
            return await client.answer_intake_llm(session_id, text=text.strip())

        return await run_backend("answer_intake", _llm)

    @mcp.tool()
    async def complete_intake(session_id: str) -> dict:
        """Complete intake and create/link a search profile (WRITE).

        Requires MCP_USER_ACCESS_TOKEN. Response includes `search_profile_id`
        for search_properties / explain_fit.

        Args:
            session_id: Intake session UUID.
        """
        client = BackendClient()
        return await run_backend(
            "complete_intake",
            lambda: client.complete_intake_session(session_id),
        )
