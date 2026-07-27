"""Create an MCP API key and write MCP_API_KEY into services/mcp/.env.

Uses backend sign-in (same local user as setup_local_auth.py), then
POST /api/v1/account/api-keys. Requires backend on :8888 and mcp_api_keys table.

Never commits the key — services/mcp/.env is gitignored.
"""

from __future__ import annotations

import argparse
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


def upsert_env(path: Path, updates: dict[str, str], *, example: Path | None = None) -> None:
    if path.exists():
        text = path.read_text(encoding="utf-8")
    elif example and example.exists():
        text = example.read_text(encoding="utf-8")
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
    path.write_text(text, encoding="utf-8")


def backend_reachable() -> bool:
    try:
        response = httpx.get(BACKEND_HEALTH, timeout=3.0, trust_env=False)
    except httpx.HTTPError:
        return False
    return response.status_code == 200


def obtain_user_jwt() -> str | None:
    """Sign in (and sign up if needed) via backend auth."""
    with httpx.Client(base_url=BASE, timeout=30.0, trust_env=False) as client:
        client.post(
            "/auth/sign-up",
            json={
                "email": EMAIL,
                "password": PASSWORD,
                "first_name": "MCP",
                "last_name": "Local",
            },
        )
        si = client.post("/auth/sign-in", json={"email": EMAIL, "password": PASSWORD})
        if si.status_code != 200:
            print(f"sign-in failed status={si.status_code} body={si.text[:300]}")
            return None
        return si.json()["access_token"]


def create_api_key(jwt: str, *, name: str) -> dict:
    with httpx.Client(base_url=BASE, timeout=30.0, trust_env=False) as client:
        response = client.post(
            "/account/api-keys",
            headers={"Authorization": f"Bearer {jwt}"},
            json={"name": name},
        )
        if response.status_code != 201:
            print(f"create key failed status={response.status_code} body={response.text[:400]}")
            response.raise_for_status()
        return response.json()


def main() -> int:
    parser = argparse.ArgumentParser(description="Create MCP API key and update services/mcp/.env")
    parser.add_argument("--name", default="cursor-local", help="Key label stored in mcp_api_keys")
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print the key but do not write services/mcp/.env",
    )
    args = parser.parse_args()

    if not backend_reachable():
        print("Backend not reachable at http://127.0.0.1:8888 — start pnpm run dev:be (or dev:all)")
        return 1

    be = load_dotenv(BACKEND_ENV)
    if not (be.get("MCP_API_KEY_PEPPER") or "").strip():
        print(
            "WARNING: backend/.env has empty MCP_API_KEY_PEPPER. "
            "Keys will hash with an empty pepper — set a long random pepper before production.",
        )

    print(f"signing in as {EMAIL} …")
    jwt = obtain_user_jwt()
    if not jwt:
        return 1

    print(f"creating MCP API key name={args.name!r} …")
    try:
        created = create_api_key(jwt, name=args.name)
    except httpx.HTTPError:
        return 1

    api_key = created.get("api_key") or ""
    if not api_key.startswith("rad_"):
        print(f"unexpected create response: {created}")
        return 1

    print(f"OK id={created.get('id')} prefix={created.get('key_prefix')}")
    print(f"api_key={api_key[:12]}… (full value written to .env unless --print-only)")

    if args.print_only:
        print(api_key)
        return 0

    upsert_env(
        ENV_PATH,
        {
            "BACKEND_API_URL": "http://127.0.0.1:8888",
            "MCP_API_KEY": api_key,
            "MCP_TRANSPORT": "stdio",
        },
        example=ENV_EXAMPLE,
    )
    print(f"wrote MCP_API_KEY to {ENV_PATH}")
    print("Reload the radestate MCP server in Cursor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
