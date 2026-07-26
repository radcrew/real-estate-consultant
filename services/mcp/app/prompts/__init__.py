"""MCP prompts — reusable workflows for CRE search and outreach drafts."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    @mcp.prompt()
    def cre_property_search() -> str:
        """Guided workflow: intake → complete → search → explain top fits."""
        return (
            "You are helping a user find commercial real estate with radestate tools.\n"
            "1. Call start_intake_session(mode=\"llm\" or \"guided\").\n"
            "2. Use answer_intake until the session is ready "
            "(guided: key+answers; llm: text), then complete_intake.\n"
            "3. Take search_profile_id from complete_intake and call search_properties.\n"
            "4. For the top 2–3 matches, call get_listing and explain_fit.\n"
            "5. Summarize tradeoffs; do not invent listing facts.\n"
            "WRITE tools: start_intake_session, answer_intake, complete_intake, "
            "update_search_criteria. Prefer asking before writes when unsure."
        )

    @mcp.prompt()
    def draft_broker_outreach() -> str:
        """Draft-only broker email workflow for a chosen property."""
        return (
            "Help draft broker outreach for a property (draft only — never send).\n"
            "1. Call get_listing(property_id) to ground the email in facts.\n"
            "2. Call generate_outreach_draft(property_id) to create a saved draft.\n"
            "3. Optionally update_outreach_draft with edits the user requests.\n"
            "Never claim an email was sent. Outreach tools only create/edit drafts."
        )
