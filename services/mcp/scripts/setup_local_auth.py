"""Bootstrap a local MCP user access token (Cognito) into services/mcp/.env.

Signs in through the local backend's auth API, which must be running. Legacy path:
prefer create_mcp_api_key.py, which stores a long-lived rad_ key instead.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import httpx
from backend_auth import local_credentials, obtain_access_token

SVC_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = SVC_ROOT / ".env"
ENV_EXAMPLE = SVC_ROOT / ".env.example"
BACKEND_HEALTH = "http://127.0.0.1:8888/health"
BASE = "http://127.0.0.1:8888/api/v1"


def upsert_env(updates: dict[str, str]) -> None:
    if ENV_PATH.exists():
        text = ENV_PATH.read_text(encoding="utf-8")
    elif ENV_EXAMPLE.exists():
        text = ENV_EXAMPLE.read_text(encoding="utf-8")
    else:
        text = ""

    for key, value in updates.items():
        pattern = re.compile(rf"^{re.escape(key)}=.*$", re.M)
        line = f"{key}={value}"
        if pattern.search(text):
            text = pattern.sub(line, text)
        else:
            if text and not text.endswith("\n"):
                text += "\n"
            text += line + "\n"
    ENV_PATH.write_text(text, encoding="utf-8")


def backend_reachable() -> bool:
    try:
        response = httpx.get(BACKEND_HEALTH, timeout=3.0, trust_env=False)
    except httpx.HTTPError:
        return False
    return response.status_code == 200


def main() -> int:
    if not backend_reachable():
        print("backend not reachable on :8888. Start pnpm run dev:be (or dev:all) first.")
        return 1

    email, password = local_credentials()
    token = obtain_access_token(BASE, email, password)
    if not token:
        print("FAILED: could not obtain access token")
        return 1

    upsert_env(
        {
            "BACKEND_API_URL": "http://127.0.0.1:8888",
            "MCP_TRANSPORT": "stdio",
            "MCP_USER_ACCESS_TOKEN": token,
            "LOG_LEVEL": "INFO",
        }
    )
    print(f"OK wrote JWT to {ENV_PATH}")
    print(f"user={email}")
    print(f"token_prefix={token[:20]}...")
    print("Reload the radestate MCP server in Cursor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
