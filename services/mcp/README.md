# MCP adapter for the radestate commercial real-estate platform.

Thin FastMCP process over the FastAPI backend (`/api/v1`). Domain logic stays in
`backend/`. Roadmap: repo root `MCP_SERVER_PLAN.md`.

## Requirements

- Python 3.11+
- Backend at `BACKEND_API_URL` (default `http://127.0.0.1:8888`)
- Supabase **user** JWT in `MCP_USER_ACCESS_TOKEN` (never the service role key)

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
copy .env.example .env
```

## Run

**stdio** (Cursor / Claude Desktop):

```powershell
python -m app.main
# or: radestate-mcp
```

**Streamable HTTP** (remote / multi-client):

```powershell
$env:MCP_TRANSPORT="streamable-http"
$env:MCP_HTTP_HOST="127.0.0.1"
$env:MCP_HTTP_PORT="8900"
python -m app.main
```

Endpoint path defaults to `/mcp` on the configured host/port. Logging → **stderr**.

## Cursor host config (stdio)

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

## Hardening

- Per-process rate limit (`RATE_LIMIT_PER_MINUTE`)
- Tool call timeout (`HTTP_TIMEOUT_SECONDS`)
- Output sanitization (secret redaction, injection-phrase filter, truncation)
- Admin tools (`enqueue_ingest`, `list_listing_submissions`) — backend enforces `is_admin`

## Tools (summary)

| Area | Tools |
|------|-------|
| Health | `ping_backend` |
| Search | `search_properties`, `update_search_criteria`, `explain_fit` |
| Listings | `get_listing`, `get_featured_listings`, `get_agent`, `list_saved_listings` |
| Intake | `start_intake_session`, `answer_intake`, `complete_intake`, `get_intake_session` |
| Outreach | `generate_outreach_draft`, `get_outreach_draft`, `update_outreach_draft` (draft only) |
| Admin | `enqueue_ingest`, `list_listing_submissions` |

Resources: `listing://`, `search://`, `intake://`.  
Prompts: `cre_property_search`, `draft_broker_outreach`.

## Tests

```powershell
pytest
ruff check app tests
```

CI: `.github/workflows/mcp.yml`.
