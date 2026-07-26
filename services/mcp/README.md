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

### One-shot local auth (recommended)

With the FastAPI backend running and `backend/.env` configured, mint a user JWT
into `services/mcp/.env` (gitignored):

```powershell
.\.venv\Scripts\python.exe scripts\setup_local_auth.py
.\.venv\Scripts\python.exe scripts\verify_local_setup.py
```

Then reload the `radestate` MCP server in Cursor. `run-mcp.cmd` loads `.env`
automatically (so you do not need to paste the token into `mcp.json`).

## Run

MCP is a **separate** process from the Next.js app and FastAPI backend. It only
calls `BACKEND_API_URL` over HTTP.

### From the monorepo root (concurrent)

```powershell
# App only (frontend + backend) — default
pnpm run dev

# App + MCP Streamable HTTP on :8900
pnpm run dev:all

# MCP HTTP alone (backend should already be up)
pnpm run dev:mcp
```

`dev:mcp` / `dev:all` start MCP in **streamable-http** mode
(`http://127.0.0.1:8900/mcp`). Cursor’s default config still uses **stdio** via
`run-mcp.cmd` (Cursor spawns that itself — do not also put stdio MCP in
`concurrently`).

### stdio (Cursor / Claude Desktop)

```powershell
python -m app.main
# or: radestate-mcp
# or: run-mcp.cmd
```

### Streamable HTTP (manual)

```powershell
$env:MCP_TRANSPORT="streamable-http"
$env:MCP_HTTP_HOST="127.0.0.1"
$env:MCP_HTTP_PORT="8900"
python -m app.main
```

Endpoint path defaults to `/mcp` on the configured host/port. Logging → **stderr**
(stdout is the JSON-RPC wire). Cursor’s MCP panel labels stderr as `[error]` even
for INFO lines; the server quiets MCP SDK protocol logs (Ping/ListTools/etc.) to
WARNING+ so those do not look like failures.

## Cursor host config (stdio)

On Windows, Cursor launches MCP servers through `cmd.exe`. Pointing `command`
straight at `.venv\\Scripts\\python.exe` often fails with *not recognized as an
internal or external command*. Use the repo launcher instead:

- Project config: [`.cursor/mcp.json`](../../.cursor/mcp.json) (uses
  `${workspaceFolder}`)
- Or user config (`%USERPROFILE%\\.cursor\\mcp.json`):

```json
{
  "mcpServers": {
    "radestate": {
      "command": "cmd.exe",
      "args": [
        "/c",
        "D:\\work\\real-estate-consultant\\services\\mcp\\run-mcp.cmd"
      ],
      "cwd": "D:\\work\\real-estate-consultant\\services\\mcp",
      "env": {
        "BACKEND_API_URL": "http://127.0.0.1:8888",
        "MCP_TRANSPORT": "stdio",
        "MCP_USER_ACCESS_TOKEN": "<supabase-access-token>"
      }
    }
  }
}
```

`run-mcp.cmd` runs `.venv\\Scripts\\python.exe -m app.main` with `PYTHONPATH`
set to `services/mcp` (avoids `ModuleNotFoundError: app` from a broken
`radestate-mcp.exe` editable install). Create the venv first:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
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
| Search | `quick_search` (location/budget/type one-shot), `search_properties`, `update_search_criteria`, `explain_fit` |
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
