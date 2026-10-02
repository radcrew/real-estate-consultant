"""Shared by the local MCP scripts: get a user access token through the backend's auth API.

Users live in Cognito, and a new account must confirm its email before it can sign in,
so use an address you can read. Set MCP_LOCAL_EMAIL / MCP_LOCAL_PASSWORD (or pass
--email to create_mcp_api_key.py); the defaults only work on a pool that auto-confirms.
"""

from __future__ import annotations

import os

import httpx

DEFAULT_EMAIL = "mcp.local@radestate.dev"
DEFAULT_PASSWORD = "McpLocalPass123!"

# The backend's 403 detail for an account that has not confirmed its email yet.
_NOT_CONFIRMED = "Confirm your email address before signing in."


def local_credentials(email: str | None = None) -> tuple[str, str]:
    return (
        email or os.environ.get("MCP_LOCAL_EMAIL") or DEFAULT_EMAIL,
        os.environ.get("MCP_LOCAL_PASSWORD") or DEFAULT_PASSWORD,
    )


def obtain_access_token(api_base: str, email: str, password: str) -> str | None:
    """Sign up if needed, confirm the emailed code if asked, then sign in."""
    with httpx.Client(base_url=api_base, timeout=30.0, trust_env=False) as client:
        # 409 means the account already exists, which is fine.
        client.post(
            "/auth/sign-up",
            json={"email": email, "password": password, "first_name": "MCP", "last_name": "Local"},
        )

        credentials = {"email": email, "password": password}
        si = client.post("/auth/sign-in", json=credentials)
        if si.status_code == 403 and _NOT_CONFIRMED in si.text:
            code = input(f"Enter the verification code emailed to {email}: ").strip()
            confirm = client.post("/auth/confirm", json={"email": email, "code": code})
            if confirm.status_code != 204:
                print(f"confirm failed status={confirm.status_code} body={confirm.text[:300]}")
                return None
            si = client.post("/auth/sign-in", json=credentials)

        if si.status_code != 200:
            print(f"sign-in failed status={si.status_code} body={si.text[:300]}")
            return None
        return si.json()["access_token"]
