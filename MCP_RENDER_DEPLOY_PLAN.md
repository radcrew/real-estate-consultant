# MCP Deploy Plan — Render.com

Plan to host the radestate MCP adapter (`services/mcp/`) on **Render**, alongside
the existing production surfaces:

| Surface | Host today | Role |
|---------|------------|------|
| Frontend | Vercel | Browser app |
| Backend (FastAPI) | Render | Domain API / auth SoT |
| Database | Supabase | Postgres + Auth |
| MCP (local) | Developer machine | Cursor stdio / local HTTP `:8900` |
| **MCP (target)** | **Render** | Remote Streamable HTTP for hosts / agents |

Complements [`MCP_SERVER_PLAN.md`](MCP_SERVER_PLAN.md) and
[`MCP_AUTH_PLAN.md`](MCP_AUTH_PLAN.md). **Does not** change Vercel frontend or
Supabase schema unless noted.

---

## Goal

Ship a production MCP URL such as:

```text
https://<mcp-service>.onrender.com/mcp
```

Clients (Cursor remote MCP, Claude, Inspector, internal agents) connect over
**Streamable HTTP**, send a **user-bound API key** (`rad_…`) per request, and
MCP proxies tool calls to the **already-deployed Render backend**.

MCP never talks to Supabase directly. Backend remains the authorization source
of truth.

---

## Target architecture

```text
┌────────────────────┐     HTTPS      ┌─────────────────────┐
│ Cursor / Claude /  │ ──────────────►│ MCP on Render       │
│ other MCP hosts    │  Bearer rad_…  │ Streamable HTTP /mcp│
└────────────────────┘                └──────────┬──────────┘
                                                 │ HTTPS + same API key
                                                 ▼
                                      ┌─────────────────────┐
                                      │ Backend on Render   │
                                      │ FastAPI /api/v1     │
                                      └──────────┬──────────┘
                                                 │ service role / SDK
                                                 ▼
                                      ┌─────────────────────┐
                                      │ Supabase            │
                                      │ DB + Auth           │
                                      └─────────────────────┘

Browser ──HTTPS──► Frontend (Vercel) ──HTTPS──► Backend (Render) ──► Supabase
```

**Keep local stdio** for day-to-day Cursor against a local or prod backend.
Remote Render MCP is an *additional* surface, not a replacement for
`run-mcp.cmd`.

---

## Decisions (freeze before implement)

| Topic | Decision |
|-------|----------|
| Transport | **Streamable HTTP only** on Render (`MCP_TRANSPORT=streamable-http`) |
| Bind address | `0.0.0.0` (Render health checks require public bind) |
| Port | Honor Render’s **`PORT`** env (map to `MCP_HTTP_PORT`) |
| Path | Default FastMCP path `/mcp` (confirm in service logs / docs) |
| Auth | **Per-request** `Authorization: Bearer rad_…` or `X-API-Key` (existing HTTP path) |
| Process env key | **Do not** set `MCP_API_KEY` on the Render MCP service (avoids a shared god-key) |
| Backend URL | Production Render backend URL as `BACKEND_API_URL` |
| DB / Supabase | **No** MCP env for Supabase keys |
| Instance type | Start with Render **Web Service** (not cron / static) |
| Region | Same region as backend when possible (latency) |
| Autosleep | Prefer a paid instance that does not sleep if agents need low latency; free tier cold starts are OK for a pilot |

---

## Code / config changes required before deploy

Small adaptations so Render’s conventions work:

1. **Honor `PORT`**
   - Today: `MCP_HTTP_PORT` defaults to `8900`.
   - Render injects `PORT` (often `10000`).
   - Change: in `app/config.py` (or start command), prefer `PORT` when set:
     `MCP_HTTP_PORT` ← `PORT` ← `8900`.

2. **Bind host `0.0.0.0`**
   - Today: default `MCP_HTTP_HOST=127.0.0.1` (local-only).
   - Production: set `MCP_HTTP_HOST=0.0.0.0` on Render.

3. **Start command**
   - From `services/mcp`:
     ```bash
     MCP_TRANSPORT=streamable-http python -m app.main
     ```
   - Or `pip install -e .` then `radestate-mcp` with the same env.

4. **Optional health endpoint**
   - Render health check: HTTP GET `/healthz` (also `/health`) → `{"status":"ok"}`.
   - Wired in `HealthzMiddleware` + `render.yaml` `healthCheckPath: /healthz`.

5. **Docs**
   - Update `services/mcp/README.md` with production URL + client samples.
   - Keep local `dev:mcp` / `dev:all` unchanged.

No Dockerfile is required for v1 (native Python Web Service). Add one later if
build reproducibility becomes an issue.

---

## Render service blueprint

Repo file: [`render.yaml`](render.yaml) (`radestate-mcp`).

### Apply Blueprint (preferred)

Prereqs: MCP deploy commits are on the branch Render will build (usually `main`),
and you can open [dashboard.render.com](https://dashboard.render.com) in a
workspace you **own or belong to** (avoid old `srv-…` links from other accounts).

1. Push the MCP Render commits to GitHub (`radcrew/real-estate-consultant`).
2. Dashboard → **New → Blueprint**.
3. Connect the GitHub repo; Blueprint path = `render.yaml` (repo root).
4. When prompted for `BACKEND_API_URL`, paste your **production FastAPI** URL
   with **no trailing slash** (e.g. `https://<backend>.onrender.com`).
5. Apply / create. Wait for the first deploy (Events tab).
6. Open the `radestate-mcp` service → copy the `*.onrender.com` URL.
7. Smoke:
   ```bash
   curl -sS "https://<mcp>.onrender.com/healthz"
   # expect: {"status":"ok"}

   # or from services/mcp (optional key + backend check):
   python scripts/smoke_render.py --base-url https://<mcp>.onrender.com \
     --backend-url https://<backend>.onrender.com --api-key rad_…
   ```
8. Logs should show
   `transport=streamable-http host=0.0.0.0 port=<PORT>`.
9. Authenticated MCP smoke (Inspector or host) against
   `https://<mcp>.onrender.com/mcp` with `Authorization: Bearer rad_…`
   (key created against the **same** production backend).

If Blueprint apply is blocked (workspace permissions), create the Web Service
manually instead (below).

### Create service (manual)

1. Render Dashboard → **New → Web Service**.
2. Connect the GitHub repo `real-estate-consultant`.
3. Settings:

| Setting | Value |
|---------|--------|
| Name | `radestate-mcp` (or similar) |
| Root Directory | `services/mcp` |
| Runtime | Python 3 |
| Build Command | `pip install -U pip && pip install .` |
| Start Command | `MCP_TRANSPORT=streamable-http python -m app.main` |
| Health check path | `/healthz` |
| Instance | Starter (or Free for pilot) |
| Auto-Deploy | `main` (or a `deploy/mcp` branch for safer rollouts) |

### Environment variables (Render dashboard)

| Key | Value | Notes |
|-----|--------|------|
| `BACKEND_API_URL` | `https://<your-backend>.onrender.com` | No trailing slash |
| `MCP_TRANSPORT` | `streamable-http` | Required |
| `MCP_HTTP_HOST` | `0.0.0.0` | Required on Render |
| `MCP_HTTP_PORT` | *(omit — use Render `PORT`)* | Honored via `AliasChoices` in `app/config.py` |
| `HTTP_TIMEOUT_SECONDS` | `60` | Raise if backend cold-starts |
| `RATE_LIMIT_PER_MINUTE` | `60` | Process-local; raise carefully |
| `MAX_TOOL_OUTPUT_CHARS` | `24000` | |
| `LOG_LEVEL` | `INFO` | |
| `PYTHONPATH` | `.` | If `python -m app.main` needs it |

**Do not set on MCP service:**

- `MCP_API_KEY` / `MCP_USER_ACCESS_TOKEN` (shared multi-user secret)
- `SUPABASE_*` / service role / HF tokens
- Frontend Vercel secrets

### Backend prerequisites (already on Render)

Confirm production backend has:

- `MCP_API_KEY_PEPPER` set (stable; changing it invalidates all keys)
- Dual auth (JWT + `rad_…`) live
- CORS not required for MCP hosts (non-browser); no change needed for typical MCP clients
- Network reachable from the MCP service (public HTTPS URL)

---

## Auth & operator workflow (production)

1. User signs in to the **web app** (Vercel → backend).
2. Create an API key: `POST /api/v1/account/api-keys` (JWT), optionally with
   scopes / `expires_in_days`.
3. Client stores the plaintext key locally (password manager / host secret store).
4. Every MCP HTTP request sends:
   ```http
   Authorization: Bearer rad_…
   ```
5. MCP forwards the same credential to `BACKEND_API_URL`.
6. Rotate: create new key → update client → revoke old key on backend.

Optional later: Settings UI on Vercel for create/list/revoke (still deferred from
auth plan Phase 3).

---

## Client wiring (after URL is live)

### MCP Inspector / curl smoke

```bash
# Replace URL and key
curl -i "https://<mcp-service>.onrender.com/mcp" \
  -H "Authorization: Bearer rad_…" \
  -H "Accept: application/json, text/event-stream"
```

Use Inspector’s Streamable HTTP mode against the same URL + header.

### Cursor (remote)

When using a remote MCP server entry (host-dependent UI):

- URL: `https://<mcp-service>.onrender.com/mcp`
- Header: `Authorization: Bearer rad_…` **or** `X-API-Key: rad_…`

Keep **local stdio** config for repo work; use remote only when testing prod.

### Claude Desktop / other hosts

Same URL + Bearer header pattern. Do not paste keys into committed JSON.

---

## Security checklist

- [ ] TLS terminated by Render (HTTPS only)
- [ ] No API keys in git, Render build logs, or MCP tool outputs
- [ ] Backend log scrubber covers `rad_` (already in auth plan)
- [ ] HTTP MCP rejects missing key (existing middleware / providers)
- [ ] Prefer scoped keys (`mcp:read` / `mcp:write`) for shared laptops
- [ ] Admin tools still require `mcp:admin` + `profiles.is_admin` on backend
- [ ] Rate limits: MCP process + backend per-key limiter
- [ ] Render service locked to private if/when team uses Render Private Networking
  between MCP ↔ backend (optional hardening)

---

## Phased rollout

### Phase 0 — Preflight (½ day)

- [ ] Confirm production backend URL and `/api/v1/ping`
- [ ] Confirm a production user can create `rad_…` keys against prod backend
- [x] Freeze decisions in this doc (Streamable HTTP, header-only keys, `PORT` / `0.0.0.0`)
- [x] Implement `PORT` + document `0.0.0.0` bind locally (`dev:mcp` still works)
  - [x] Honor `PORT` / `MCP_HTTP_PORT` in `app/config.py`
  - [x] Document `0.0.0.0` bind + Render env in README

**Exit:** local HTTP MCP can target **prod** `BACKEND_API_URL` with a prod key
(optional smoke; careful with real data).

### Phase 1 — First Render deploy (½–1 day)

- [x] Add repo `render.yaml` Blueprint for `radestate-mcp` (`services/mcp` root)
- [x] Operator runbook: Apply Blueprint + smoke (`/healthz`, logs, `/mcp`)
- [x] `scripts/smoke_render.py` post-deploy checker
- [ ] Create / apply Blueprint (or Web Service) in Render Dashboard
- [ ] Set `BACKEND_API_URL` (no shared `MCP_API_KEY`)
- [ ] Deploy from `main` (or release branch)
- [ ] Verify process logs: `transport=streamable-http host=0.0.0.0 port=<PORT>`
- [ ] Smoke: Inspector / curl authenticated session → `ping_backend` → search

**Exit:** public `https://…onrender.com/mcp` works with a personal API key.

### Phase 2 — Hardening (½ day)

- [x] Health check path settled (`GET /healthz`, Blueprint `healthCheckPath`)
- [ ] Timeouts tuned for backend cold start
- [ ] Instance size / no-sleep decision
- [x] README + host config samples updated (Render section)
- [ ] Optional: GitHub Action deploy on `services/mcp/**` changes

**Exit:** documented runbook; on-call knows how to rotate keys and redeploy.

### Phase 3 — Optional follow-ups (later)

- [ ] Private networking MCP → backend
- [ ] OAuth for MCP hosts (out of scope for API-key track)
- [ ] Multi-region / horizontal replicas (rate limiter is in-process today)
- [ ] Dockerfile + pinned image for reproducible builds

---

## Suggested repo artifacts (implementation PR)

| Artifact | Purpose |
|----------|---------|
| `services/mcp` config: prefer `PORT` | Render compatibility |
| `render.yaml` | Declarative `radestate-mcp` Web Service Blueprint |
| `services/mcp/README.md` | Production / Blueprint section |
| `.github/workflows/mcp.yml` | Already tests; optionally add deploy job |
| This plan | Living checklist |

---

## Testing plan

| Layer | What |
|-------|------|
| Local | `MCP_TRANSPORT=streamable-http MCP_HTTP_HOST=0.0.0.0` + Inspector |
| Deploy | Render logs show bind + path; health check green |
| Auth | Missing key fails; valid `rad_…` can `ping_backend` and `quick_search` |
| Backend | MCP → prod backend → Supabase; no MCP service-role usage |
| Regression | Local stdio Cursor path still works unchanged |

---

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Free tier cold start + backend cold start | Longer `HTTP_TIMEOUT_SECONDS`; paid always-on for pilot users |
| Shared env API key on MCP | Never set; header-only auth |
| Pepper rotation on backend | Document: recreate all MCP keys |
| In-process rate limit with multiple MCP instances | Sticky single instance until Redis/shared limiter |
| `/mcp` fails Render health GET | `GET /healthz` + Blueprint `healthCheckPath` |

---

## Non-goals

- Deploying MCP as Vercel serverless (wrong process model for long-lived MCP HTTP)
- Putting MCP inside the FastAPI backend process (keep deploy/auth boundaries)
- Replacing Cursor stdio for local development
- MCP → Supabase direct access
- OAuth 2.1 for MCP hosts (deferred)

---

## Open questions (resolve in Phase 0)

1. Exact production backend URL on Render?
2. Free vs always-on Render instance for MCP?
3. Who may create production API keys (all users vs admins only)?
4. Publish `render.yaml` Blueprint in-repo or configure only in dashboard?

---

## Suggested first commit message (when implementing)

```
feat: prepare MCP for Render Streamable HTTP deploy

Honor PORT/0.0.0.0 bind settings and document the Render web service
blueprint for hosting services/mcp against the production backend.
```

_Stop after each implementation step and confirm before the next, if following
the same step-by-step process as the API-key auth work._
