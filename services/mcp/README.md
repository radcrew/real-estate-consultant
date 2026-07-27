# MCP adapter for the radestate commercial real-estate platform.

Thin FastMCP process over the FastAPI backend (`/api/v1`). Domain logic stays in
`backend/`. Roadmap: repo root `MCP_SERVER_PLAN.md`. Deploy plan:
[`MCP_RENDER_DEPLOY_PLAN.md`](../../MCP_RENDER_DEPLOY_PLAN.md).

## Requirements

- Python 3.11+
- Backend at `BACKEND_API_URL` (default `http://127.0.0.1:8888`)
- **`MCP_API_KEY`** (`rad_…`) in `services/mcp/.env` for stdio — create via
  `POST /api/v1/account/api-keys` while signed in (JWT). Never the service role key.
- Legacy fallback: `MCP_USER_ACCESS_TOKEN` (short-lived Supabase user JWT)

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
copy .env.example .env
```

### Auth (API key)

**Recommended (one command):** with the backend running:

```powershell
.\.venv\Scripts\python.exe scripts\create_mcp_api_key.py
```

That signs in as the local MCP user, calls `POST /api/v1/account/api-keys`, and
writes `MCP_API_KEY` into gitignored `services/mcp/.env`. Then reload the
`radestate` MCP server in Cursor.

Manual alternative:

```powershell
# With a user JWT in $token
curl -X POST http://127.0.0.1:8888/api/v1/account/api-keys `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d "{\"name\":\"cursor\"}"
```

Put the returned `api_key` into `services/mcp/.env` as `MCP_API_KEY=rad_…`.
Never commit keys or paste them into `mcp.json`. Set `MCP_API_KEY_PEPPER` in
`backend/.env` (long random string) before creating production keys.

Optional create body fields: `scopes` (`*`, `mcp:read`, `mcp:write`, `mcp:admin`)
and `expires_in_days`. Default scope is `["*"]`. Backend maps GET→`mcp:read`,
mutating methods→`mcp:write`; admin routes also need `mcp:admin` plus
`profiles.is_admin`.

### Rotate a key

1. Create a new key (`create_mcp_api_key.py` or `POST /api/v1/account/api-keys`).
2. Update `MCP_API_KEY` in `services/mcp/.env` (stdio) or client headers (HTTP).
3. Reload the MCP server / host so it picks up the new value.
4. Revoke the old key: `DELETE /api/v1/account/api-keys/{id}` (JWT or a key with
   `mcp:write` / `*`).

Legacy JWT bootstrap (migration only): `scripts\setup_local_auth.py`.

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
(`http://127.0.0.1:8900/mcp`). HTTP tool calls require
`Authorization: Bearer rad_…` or `X-API-Key` **per request** (env credentials are
not used for HTTP). Cursor’s default config still uses **stdio** via
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

For a PaaS-like local check (public bind), use `MCP_HTTP_HOST=0.0.0.0`.
On Render, set `MCP_HTTP_HOST=0.0.0.0` and **omit** `MCP_HTTP_PORT` so the
platform `PORT` is used (see `app/config.py`).

Endpoint path defaults to `/mcp` on the configured host/port. Logging → **stderr**
(stdout is the JSON-RPC wire). Cursor’s MCP panel labels stderr as `[error]` even
for INFO lines; the server quiets MCP SDK protocol logs (Ping/ListTools/etc.) to
WARNING+ so those do not look like failures.

## Deploy (Render)

MCP on Render is a **separate Web Service** from the FastAPI backend. It only
calls `BACKEND_API_URL` over HTTPS. Full checklist:
[`MCP_RENDER_DEPLOY_PLAN.md`](../../MCP_RENDER_DEPLOY_PLAN.md).

**Blueprint:** repo-root [`render.yaml`](../../render.yaml) defines
`radestate-mcp`. Apply steps (push → New → Blueprint → set `BACKEND_API_URL` →
smoke `/healthz`): see
[`MCP_RENDER_DEPLOY_PLAN.md`](../../MCP_RENDER_DEPLOY_PLAN.md#apply-blueprint-preferred).
Or create a Web Service manually:

| Setting | Value |
|---------|--------|
| Root Directory | `services/mcp` |
| Build | `pip install -U pip && pip install .` |
| Start | `MCP_TRANSPORT=streamable-http python -m app.main` |

**Required env on Render**

| Key | Value |
|-----|--------|
| `BACKEND_API_URL` | Production backend URL (no trailing slash) |
| `MCP_TRANSPORT` | `streamable-http` |
| `MCP_HTTP_HOST` | `0.0.0.0` |

Omit `MCP_HTTP_PORT` — Render injects `PORT`. Do **not** set `MCP_API_KEY` on
the service (HTTP clients send `Authorization: Bearer rad_…` or `X-API-Key` per
request). Public URL shape: `https://<service>.onrender.com/mcp`.

Liveness for Render: `GET /healthz` (also `/health`) returns `{"status":"ok"}`
without an API key. Blueprint sets `healthCheckPath: /healthz`.

Local Cursor **stdio** (`run-mcp.cmd`) stays unchanged for day-to-day work.

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
        "MCP_TRANSPORT": "stdio"
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

- Backend per-key rate limit (`MCP_API_KEY_RATE_LIMIT_PER_MINUTE`)
- MCP per-process rate limit (`RATE_LIMIT_PER_MINUTE`)
- Tool call timeout (`HTTP_TIMEOUT_SECONDS`)
- Output sanitization (secret redaction, injection-phrase filter, truncation)
- Admin tools (`enqueue_ingest`, `list_listing_submissions`) — backend enforces
  `mcp:admin` (API key) and `profiles.is_admin`

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
