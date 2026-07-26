"""Bootstrap a local MCP user JWT into services/mcp/.env.

Prefers backend auth API when it is up; otherwise uses Supabase Admin API via
backend/.env SERVICE_ROLE (local setup only — never commit that key).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import httpx

SVC_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SVC_ROOT.parents[1]
ENV_PATH = SVC_ROOT / ".env"
ENV_EXAMPLE = SVC_ROOT / ".env.example"
BACKEND_ENV = REPO_ROOT / "backend" / ".env"
BACKEND_HEALTH = "http://127.0.0.1:8888/health"
BASE = "http://127.0.0.1:8888/api/v1"

EMAIL = "mcp.local@radestate.dev"
PASSWORD = "McpLocalPass123!"


def load_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


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


def try_backend_auth(email: str, password: str) -> str | None:
    with httpx.Client(base_url=BASE, timeout=30.0, trust_env=False) as client:
        client.post(
            "/auth/sign-up",
            json={
                "email": email,
                "password": password,
                "first_name": "MCP",
                "last_name": "Local",
            },
        )
        si = client.post("/auth/sign-in", json={"email": email, "password": password})
        if si.status_code == 200:
            return si.json()["access_token"]
        print(f"backend sign-in failed status={si.status_code}")
        return None


def try_supabase_admin(email: str, password: str) -> str | None:
    be = load_dotenv(BACKEND_ENV)
    url = (be.get("SUPABASE_URL") or "").rstrip("/")
    service_key = be.get("SUPABASE_SERVICE_ROLE_KEY") or ""
    anon = be.get("SUPABASE_ANON_KEY") or ""
    if not url or not service_key:
        print("backend/.env missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return None

    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=60.0, trust_env=False) as client:
        create = client.post(
            f"{url}/auth/v1/admin/users",
            headers=headers,
            json={
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {"first_name": "MCP", "last_name": "Local"},
            },
        )
        if create.status_code in (200, 201):
            print("supabase: created local MCP user")
        elif create.status_code == 422 and "email_exists" in create.text:
            print("supabase: local MCP user already exists (ok)")
        else:
            print(f"supabase: create user status={create.status_code} body={create.text[:200]}")

        grant_key = anon or service_key
        grant = client.post(
            f"{url}/auth/v1/token?grant_type=password",
            headers={
                "apikey": grant_key,
                "Content-Type": "application/json",
            },
            json={"email": email, "password": password},
        )
        if grant.status_code != 200:
            print(f"supabase: password grant failed status={grant.status_code}")
            print(grant.text[:300])
            return None
        print("supabase: password grant ok")
        return grant.json()["access_token"]


def main() -> int:
    token: str | None = None

    if backend_reachable():
        print("backend is up — trying /api/v1/auth")
        token = try_backend_auth(EMAIL, PASSWORD)
    else:
        print("backend not reachable on :8888 — using Supabase Admin API fallback")

    if not token:
        token = try_supabase_admin(EMAIL, PASSWORD)

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
    print(f"user={EMAIL}")
    print(f"token_prefix={token[:20]}...")
    print("Reload the radestate MCP server in Cursor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
