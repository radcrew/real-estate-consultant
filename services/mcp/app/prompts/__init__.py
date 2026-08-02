"""MCP prompts — reusable workflows for CRE search and outreach drafts."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    @mcp.prompt()
    def cre_property_search() -> str:
        """Guided workflow: quick_search → listing detail → optional similar."""
        return (
            "You are helping a user find commercial real estate with radestate tools.\n"
            "1. Prefer quick_search with location, optional property_types, "
            "and price_min/price_max.\n"
            "2. If a search_profile_id already exists, call search_properties "
            "to page through it instead of starting a new search.\n"
            "3. For the top 2–3 matches, call get_listing for full detail.\n"
            "4. Optionally call get_similar_listings on a favorite to explore neighbors.\n"
            "5. Summarize tradeoffs; do not invent listing facts.\n"
            "WRITE tools: quick_search. Prefer asking before writes when unsure."
        )

    @mcp.prompt()
    def draft_broker_outreach() -> str:
        """Draft-only broker email workflow for a chosen property."""
        return (
            "Help draft broker outreach for a property (draft only — never send).\n"
            "1. Call get_listing(property_id) to ground the email in facts.\n"
            "2. Call generate_outreach_draft(property_id) to create a saved draft.\n"
            "3. Call get_outreach_draft to read the saved draft back for review.\n"
            "Never claim an email was sent. Outreach tools only create drafts."
        )
