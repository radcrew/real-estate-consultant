"""Post-deploy smoke checks for MCP on Render (or any Streamable HTTP host).

Usage:
  python scripts/smoke_render.py --base-url https://radestate-mcp.onrender.com
  python scripts/smoke_render.py --base-url https://… --api-key rad_… --backend-url https://…onrender.com

Does not print full API keys. Exit 0 on success.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import httpx

SVC_ROOT = Path(__file__).resolve().parents[1]


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        required=True,
        help="MCP service origin, e.g. https://radestate-mcp.onrender.com",
    )
    parser.add_argument(
        "--api-key",
        default="",
        help="Optional rad_… key (or set MCP_API_KEY). Used with --backend-url.",
    )
    parser.add_argument(
        "--backend-url",
        default="",
        help="Optional FastAPI origin to verify the key against /api/v1/ping.",
    )
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    env = load_dotenv(SVC_ROOT / ".env")
    api_key = (args.api_key or os.environ.get("MCP_API_KEY") or env.get("MCP_API_KEY") or "").strip()
    backend = (args.backend_url or os.environ.get("BACKEND_API_URL") or env.get("BACKEND_API_URL") or "").rstrip(
        "/",
    )

    failures: list[str] = []

    with httpx.Client(timeout=args.timeout, follow_redirects=True) as client:
        print(f"GET {base}/healthz …")
        try:
            hz = client.get(f"{base}/healthz")
        except httpx.HTTPError as exc:
            print(f"FAIL healthz: {exc}")
            return 1
        if hz.status_code != 200:
            failures.append(f"healthz status {hz.status_code}")
            print(f"FAIL healthz: HTTP {hz.status_code} body={hz.text[:200]!r}")
        else:
            try:
                payload = hz.json()
            except ValueError:
                payload = None
            if not isinstance(payload, dict) or payload.get("status") != "ok":
                failures.append(f"healthz body {hz.text[:200]!r}")
                print(f"FAIL healthz body: {hz.text[:200]!r}")
            else:
                print("OK healthz")

        print(f"GET {base}/mcp (expect protocol response, not connection error) …")
        try:
            mcp = client.get(
                f"{base}/mcp",
                headers={"Accept": "application/json, text/event-stream"},
            )
            print(f"OK /mcp reachable (HTTP {mcp.status_code})")
        except httpx.HTTPError as exc:
            failures.append(f"/mcp unreachable: {exc}")
            print(f"FAIL /mcp: {exc}")

        if api_key and backend:
            print(f"GET {backend}/api/v1/ping with API key …")
            try:
                ping = client.get(
                    f"{backend}/api/v1/ping",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
            except httpx.HTTPError as exc:
                failures.append(f"backend ping: {exc}")
                print(f"FAIL backend ping: {exc}")
            else:
                if ping.status_code != 200:
                    failures.append(f"backend ping HTTP {ping.status_code}")
                    print(f"FAIL backend ping: HTTP {ping.status_code} {ping.text[:200]!r}")
                else:
                    print("OK backend ping (key accepted)")
        elif api_key and not backend:
            print("skip backend ping (pass --backend-url to verify API key)")
        elif backend and not api_key:
            print("skip backend ping (pass --api-key or set MCP_API_KEY)")

    if failures:
        print("SMOKE FAILED:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("SMOKE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
