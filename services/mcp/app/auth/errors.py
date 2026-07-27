"""Auth errors mapped to MCP ``isError`` payloads."""

from __future__ import annotations


class AuthRequiredError(Exception):
    """No API key / JWT available for an authenticated backend call."""

    def __init__(
        self,
        message: str = (
            "MCP credentials missing. Set MCP_API_KEY (rad_…) in services/mcp/.env "
            "for stdio, or send Authorization: Bearer / X-API-Key for HTTP. "
            "Create a key via POST /api/v1/account/api-keys (never use the service role key)."
        ),
    ) -> None:
        super().__init__(message)


class AuthInvalidError(Exception):
    """Backend rejected the credential (401)."""

    def __init__(
        self,
        message: str = (
            "Unauthorized — MCP_API_KEY is invalid or revoked "
            "(or legacy MCP_USER_ACCESS_TOKEN expired). "
            "Create/rotate a key via POST /api/v1/account/api-keys."
        ),
    ) -> None:
        super().__init__(message)
