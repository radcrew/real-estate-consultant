"""Client-side errors mapped to MCP `isError` payloads (never crash stdio)."""

from __future__ import annotations


class AuthRequiredError(Exception):
    """Raised when an authenticated backend call is attempted without a user JWT."""

    def __init__(
        self,
        message: str = (
            "MCP_USER_ACCESS_TOKEN is not set. Sign in via the app or Supabase, "
            "paste a short-lived user access token into services/mcp/.env "
            "(never the service role key), then retry."
        ),
    ) -> None:
        super().__init__(message)
