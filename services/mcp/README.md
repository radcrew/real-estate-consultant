# MCP adapter for the radestate commercial real-estate platform.

Thin FastMCP process over the FastAPI backend (`/api/v1`). Domain logic stays in
`backend/`. Roadmap: repo root `MCP_SERVER_PLAN.md`.

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

Endpoint path defaults to `/mcp` on the configured host/port. Logging → **stderr**
(stdout is the JSON-RPC wire). Cursor’s MCP panel labels stderr as `[error]` even
for INFO lines; the server quiets MCP SDK protocol logs (Ping/ListTools/etc.) to
WARNING+ so those do not look like failures.

### Vercel (Streamable HTTP, no Docker)

Same pattern as the FastAPI backend: Python ASGI on Vercel Functions.

```text
services/mcp/api/index.py  →  app.asgi:app  (stateless + JSON MCP)
vercel.json                →  rewrite /* → /api/index, maxDuration 60
```

**One-time project setup**

```powershell
cd services/mcp
npx vercel link   # Root Directory = services/mcp (new Vercel project)
```

Set project env in the Vercel dashboard (or `npx vercel env add`):

| Variable | Value |
|----------|--------|
| `BACKEND_API_URL` | `https://real-estate-consultant-be.vercel.app` |
| `HTTP_TIMEOUT_SECONDS` | `55` |
| `LOG_LEVEL` | `INFO` |

Optional: `RATE_LIMIT_PER_MINUTE`. Enable **Fluid Compute** on the project for bursty MCP traffic.

Do **not** set a shared `MCP_API_KEY` on the deployment — clients send `Authorization: Bearer rad_…` or `X-API-Key` per request.

Health check: `GET https://<mcp-project>.vercel.app/health`

**Local Vercel runtime check** (after link):

```powershell
cd services/mcp
npx vercel dev
# then POST http://127.0.0.1:3000/mcp  (or the port vercel prints)
```

**Preview / prod**

```powershell
npx vercel deploy
npx vercel deploy --prod
```

Public path: `https://<mcp-project>.vercel.app/mcp`. Plan: repo root
[`MCP_VERCEL_DEPLOY_PLAN.md`](../../MCP_VERCEL_DEPLOY_PLAN.md).

Linked project (local `npx vercel link`): **`real-estate-consultant-mcp`**  
Project ID for GitHub secret `VERCEL_MCP_PROJECT_ID`: `prj_dZS9H4Ne4VpVIMHiz5XaDohRxRvs`  
**Production URL:** https://real-estate-consultant-mcp.vercel.app  
Health: https://real-estate-consultant-mcp.vercel.app/health  
MCP endpoint: https://real-estate-consultant-mcp.vercel.app/mcp  

Verified: `tools/list` + `ping_backend` against this URL with **`rad_…` API key**
(MCP → `https://real-estate-consultant-be-nu.vercel.app`).

### Production API keys (for remote MCP)

Create keys against the **production** backend (pepper must already be set on
that Vercel project as `MCP_API_KEY_PEPPER`):

```powershell
cd services/mcp
# Prefer a real user JWT from the signed-in app:
.\.venv\Scripts\python.exe scripts\create_mcp_api_key.py `
  --backend-url https://real-estate-consultant-be.vercel.app `
  --access-token "<user_jwt>" `
  --name cursor-prod `
  --print-only
```

Copy the printed `rad_…` into your host config headers only. Rotate by creating
a new key, updating the host, then `DELETE /api/v1/account/api-keys/{id}` with
JWT or a write-scoped key.

### Deployment Protection

If the MCP Vercel project has **Deployment Protection** (SSO / password), MCP
hosts and Inspector will get HTML challenges instead of JSON-RPC. For the
production MCP URL either:

- disable protection on that project, or
- use a [protection bypass](https://vercel.com/docs/security/deployment-protection/methods-to-bypass-deployment-protection)
  header/secret only for trusted automation (not a substitute for `rad_…`).

Standard Protection Bypass is optional; **API key auth remains required**.

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

## Cursor host config (remote / Vercel)

After the MCP project is deployed, use Streamable HTTP instead of stdio.
Example template (no secrets): [`.cursor/mcp.remote.example.json`](../../.cursor/mcp.remote.example.json).

```json
{
  "mcpServers": {
    "radestate-remote": {
      "url": "https://<mcp-project>.vercel.app/mcp",
      "headers": {
        "Authorization": "Bearer rad_…"
      }
    }
  }
}
```

Keep local stdio (`radestate`) for day-to-day repo work; use `radestate-remote`
when you want the deployed adapter. If your Cursor build ignores `headers`, use
MCP Inspector with the same URL + Bearer token to verify, then check Cursor docs
for the current remote-auth field names.

## Hardening

- Backend per-key rate limit (`MCP_API_KEY_RATE_LIMIT_PER_MINUTE`)
- MCP per-process rate limit (`RATE_LIMIT_PER_MINUTE`)
- Tool call timeout (`HTTP_TIMEOUT_SECONDS`, keep ≤ Vercel `maxDuration`)
- Output + log sanitization (JWT / `rad_…` / HF key redaction, injection filter, truncation)
- Admin tools (`enqueue_ingest`, `list_listing_submissions`) — backend enforces
  `mcp:admin` (API key) and `profiles.is_admin`

## Runbook (remote MCP)

| Symptom | Likely cause | What to do |
|---------|----------------|------------|
| First tool call slow / timeout | Vercel cold start (MCP and/or backend) | Retry once; raise `maxDuration` / Fluid Compute if persistent |
| `401` / invalid token | Missing/wrong `rad_…`, revoked key, or pepper mismatch on backend | Recreate key against **prod** backend; confirm `MCP_API_KEY_PEPPER` on BE |
| `403` Forbidden | User lacks access or API key lacks `mcp:admin` for admin tools | Use a key with the right scopes; confirm `profiles.is_admin` |
| `429` rate limited | Backend per-key limit or MCP process limiter | Back off; raise limits only if needed |
| `502` / `503` / unavailable | Backend cold start, RLS, or upstream error | Check BE `/health` and Vercel BE logs; retry |
| HTML instead of JSON from `/mcp` | Vercel Deployment Protection | Disable protection or use bypass secret for automation |
| `Task group is not initialized` | ASGI lifespan not running | Confirm Vercel Python ASGI lifespan; see deploy plan Phase 0 note |

Local stdio (`run-mcp.cmd` / `pnpm run dev:mcp`) remains the default for contributors.

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

CI: `.github/workflows/mcp.yml` (lint/test on every change; Vercel preview on PR; prod deploy on `main`).

Required GitHub secrets for deploy: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_MCP_PROJECT_ID`
(optional `VERCEL_AUTOMATION_BYPASS_SECRET`). Create the Vercel project first
(Root Directory = `services/mcp`) before expecting deploy jobs to succeed.
