# MCP adapter for the radestate commercial real-estate platform.

Phase 1: stdio FastMCP adapter over the FastAPI backend. Domain logic stays in
`backend/`. See repo root `MCP_SERVER_PLAN.md` for the full roadmap.

## Requirements

- Python 3.11+
- Backend reachable at `BACKEND_API_URL` (default `http://127.0.0.1:8888`)
- For authenticated tools: a short-lived Supabase **user** access token in
  `MCP_USER_ACCESS_TOKEN` (never the service role key)

## Setup

From this directory (`services/mcp/`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
copy .env.example .env
```

On macOS/Linux: `source .venv/bin/activate`, then the same `python -m pip` lines.

## Run (stdio)

```powershell
python -m app.main
```

Or: `radestate-mcp`

Logging goes to **stderr** only (stdout is the MCP JSON-RPC wire).

## Smoke test with MCP Inspector

```powershell
mcp dev app/main.py
```

Try `ping_backend`, then with a real JWT + search session id: `search_properties`
→ `get_listing` → `explain_fit`.

## Cursor host config

```json
{
  "mcpServers": {
    "radestate": {
      "command": "D:/work/real-estate-consultant/services/mcp/.venv/Scripts/python.exe",
      "args": ["-m", "app.main"],
      "cwd": "D:/work/real-estate-consultant/services/mcp",
      "env": {
        "BACKEND_API_URL": "http://127.0.0.1:8888",
        "MCP_USER_ACCESS_TOKEN": "<supabase-access-token>"
      }
    }
  }
}
```

## Tools (Phase 1)

| Tool | Backend | Auth | Side effects |
|------|---------|------|--------------|
| `ping_backend` | `GET /api/v1/ping` | No | None |
| `search_properties` | `GET /api/v1/search/{id}` | Yes | None |
| `update_search_criteria` | `PUT /api/v1/search/{id}` | Yes | Replaces criteria |
| `get_listing` | `GET /api/v1/listings/{id}` | No | None |
| `get_featured_listings` | `GET /api/v1/listings/featured` | No | None |
| `explain_fit` | `POST /api/v1/search/{id}/fit/{property_id}` | Yes | LLM call (not persisted) |
| `list_saved_listings` | `GET /api/v1/account/saved` | Yes | None |
| `get_agent` | `GET /api/v1/agents/{broker}` | Yes | None |

## Tests

```powershell
pytest
```
