"""Shared by the local MCP scripts: get a user access token through the backend's auth API.

The account comes from MCP_LOCAL_EMAIL / MCP_LOCAL_PASSWORD (see app/config.py), or pass
--email to create_mcp_api_key.py.
"""

from __future__ import annotations

import httpx

from app.config import settings

# The backend's 403 detail for an account that has not confirmed its email yet.
_NOT_CONFIRMED = "Confirm your email address before signing in."


def local_credentials(email: str | None = None) -> tuple[str, str]:
    return (email or settings.mcp_local_email, settings.mcp_local_password)


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
