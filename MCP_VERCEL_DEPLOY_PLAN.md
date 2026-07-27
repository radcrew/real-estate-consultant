# MCP Vercel Deploy Plan

Plan to deploy the radestate **MCP adapter** (`services/mcp/`) to **Vercel**, alongside the existing frontend and backend.

**Backend (already live):** `https://real-estate-consultant-be.vercel.app/`  
**Database:** Supabase (unchanged — MCP never talks to Supabase directly)  
**Frontend:** Vercel (unchanged)

Complements [`MCP_SERVER_PLAN.md`](MCP_SERVER_PLAN.md) and [`MCP_AUTH_PLAN.md`](MCP_AUTH_PLAN.md).

---

## Goal

Ship a **public HTTPS MCP endpoint** (Streamable HTTP) that:

1. Exposes the same tools as local `services/mcp/`
2. Forwards each tool call to the **production FastAPI backend** with the caller’s `rad_…` API key
3. Keeps **backend + Supabase** as the source of truth for auth, data, and RLS
4. Works with Cursor / Claude / Inspector over **HTTP** (not stdio)

**Non-goals**

- Replacing local stdio (`run-mcp.cmd`) — keep stdio for local DX; production is HTTP-only.
- **Docker / containers** — no `Dockerfile`, no container image builds, no Docker Compose, and no container-based hosts (Fly / Railway / Cloud Run, etc.). Deploy only via **Vercel Functions** (same style as the existing Python backend).

---

## Current architecture (local)

```text
Cursor (stdio) ──► services/mcp ──Bearer/X-API-Key──► FastAPI :8888 ──► Supabase
                         ▲
dev:all (HTTP :8900) ────┘
```

- Transport: `stdio` (Cursor) or `streamable-http` (`pnpm run dev:mcp`)
- Auth: `MCP_API_KEY` from env (stdio) or **per-request headers** (HTTP)
- Domain logic: **none** in MCP — thin `httpx` client to `/api/v1`

---

## Target architecture (Vercel)

```text
Cursor / Claude / Inspector
        │  Streamable HTTP
        │  Authorization: Bearer rad_…  or  X-API-Key: rad_…
        ▼
┌───────────────────────────────────────┐
│  Vercel project (Root = services/mcp) │
│  ASGI: FastMCP streamable_http_app()  │
│  + CaptureApiKeyMiddleware            │
└───────────────────┬───────────────────┘
                    │ HTTPS
                    ▼
https://real-estate-consultant-be.vercel.app
                    │
                    ▼
              Supabase
```

Suggested production URL shape:

```text
https://real-estate-consultant-mcp.vercel.app/mcp
```

(Exact path depends on FastMCP `streamable_http_path` + `vercel.json` rewrites.)

---

## Why Vercel is workable (and what bites)

| Fit | Risk / constraint |
|-----|-------------------|
| Same monorepo pattern as `backend/` Python deploy | Official Vercel MCP docs favor **Node `mcp-handler`**; we stay on **Python FastMCP** |
| Fluid Compute suits bursty tool traffic | **Serverless is mostly stateless** — MCP session affinity is limited |
| HTTPS + previews + Firewall | Function **`maxDuration`** must cover backend latency (search/intake/LLM) |
| No new DB for MCP | Cold starts add latency on first tool call |
| API-key pass-through already built for HTTP | Vercel **Deployment Protection** can block MCP hosts unless configured |

**Decision:** Deploy Python MCP like the backend (ASGI entry + `vercel.json`), with **no Docker**. Prefer staying on FastMCP; only if Python Streamable HTTP cannot run reliably on Vercel Functions, fall back to a **Vercel-native Node `mcp-handler`** thin proxy (still no containers) that calls the same backend.

**Constraint:** all production MCP hosting stays on **Vercel**. Do not introduce Docker or another container platform.

---

## Principles

1. **MCP stays a thin adapter** — no Supabase keys, no HF tokens, no service role in the MCP project.
2. **`BACKEND_API_URL`** in production = `https://real-estate-consultant-be.vercel.app` (no trailing slash).
3. **Auth remains API-key pass-through** — clients send `rad_…` per request; MCP does not mint keys.
4. **No shared process `MCP_API_KEY` on the public server** for multi-user use (same rule as local HTTP today). Optional demo key only if gated and rotated.
5. **Stateless-first** — prefer FastMCP / transport settings that do not require sticky in-memory sessions across invocations.
6. **Mirror backend deploy DX** — Root Directory `services/mcp`, `api/index.py` entry, GitHub Actions on `main`.
7. **No Docker** — packaging is Vercel Python/Node install + Functions only (`vercel.json`, `requirements.txt` / `pyproject.toml` as needed).

---

## Phases

### Phase 0 — Spike: FastMCP ASGI on Vercel Python (½–1 day)

Prove the runtime before wiring CI.

**Tasks**

- [x] Confirm FastMCP exposes an ASGI app via `mcp.streamable_http_app()` (already used locally).
- [x] Research / set **stateless** Streamable HTTP mode (`stateless_http=True` on ASGI entry) + **`json_response=True`** for Functions.
- [x] Add minimal Vercel entry (draft):

```text
services/mcp/
  api/index.py          # export ASGI app (middleware-wrapped)
  app/asgi.py           # CaptureApiKeyMiddleware + FastMCP
  vercel.json           # rewrites → /api/index, maxDuration 60
  .vercelignore
  requirements.txt
```

- [x] Local ASGI check: Starlette `TestClient` POST `/mcp` initialize → 200 JSON (`radestate`).
- [x] Document `vercel link` / `vercel dev` / deploy commands in `services/mcp/README.md`.
- [ ] Create/link Vercel MCP project; deploy a preview; Inspector + `ping_backend` against prod BE.

**Note:** FastMCP requires ASGI **lifespan** so the session manager task group starts — even in `stateless_http` mode. Vercel’s Python ASGI runtime must invoke lifespan (same as Starlette). If a preview fails with `Task group is not initialized`, that is the first failure mode to debug.

**Exit criteria:** Inspector lists tools and `ping_backend` returns pong against prod BE.

**Abort criteria (still on Vercel, still no Docker):** session/streaming incompatible with Python serverless → pivot Phase 5 to a **Node `mcp-handler`** MCP surface on Vercel that proxies the same `/api/v1` backend.

---

### Phase 1 — Production packaging (½–1 day)

**Code / config**

- [x] `services/mcp/api/index.py` — build server, wrap `CaptureApiKeyMiddleware`, export `app`.
- [x] `services/mcp/vercel.json` — rewrite all traffic to the ASGI entry; set `maxDuration` (start **60s**).
- [x] `GET /health` + CORS middleware for Inspector / browser hosts.
- [x] `runtime.txt` (Python 3.12) + prod-oriented `.env.example` (`HTTP_TIMEOUT_SECONDS=55`).
- [ ] Enable **Fluid Compute** on the Vercel MCP project (dashboard).
- [ ] Env on Vercel MCP project (`BACKEND_API_URL`, timeouts) — must use the **same Vercel team** that owns `real-estate-consultant-be`.

| Variable | Value |
|----------|--------|
| `BACKEND_API_URL` | `https://real-estate-consultant-be.vercel.app` |
| `HTTP_TIMEOUT_SECONDS` | `55` (below function maxDuration) |
| `LOG_LEVEL` | `INFO` |
| `RATE_LIMIT_PER_MINUTE` | keep or raise for prod |

- [x] Do **not** set `MCP_API_KEY` / `MCP_USER_ACCESS_TOKEN` on the shared deployment (header-only auth) — documented.
- [x] CORS: allow MCP Inspector / browser clients.
- [x] Health: `GET /health`.

**Backend checklist (prod)**

- [ ] `MCP_API_KEY_PEPPER` set on **backend** Vercel env (already needed for API keys).
- [ ] Confirm `POST /api/v1/account/api-keys` works on prod for operators.

---

### Phase 2 — Auth & host configuration (½ day)

Keep **API-key pass-through** (already implemented). Defer full MCP OAuth/`mcp-handler` OAuth unless a host requires it.

**Client config (Cursor example)**

```json
{
  "mcpServers": {
    "radestate": {
      "url": "https://real-estate-consultant-mcp.vercel.app/mcp",
      "headers": {
        "Authorization": "Bearer rad_…"
      }
    }
  }
}
```

Template checked in: [`.cursor/mcp.remote.example.json`](.cursor/mcp.remote.example.json).

**Tasks**

- [x] Document create-key flow against **prod** backend (`create_mcp_api_key.py --backend-url … --print-only`)
- [x] Document rotation (create → update host headers → revoke old)
- [x] Document Deployment Protection / bypass notes for MCP hosts
- [ ] Optional: Vercel Firewall rate rules in front of `/mcp` (dashboard)

**Out of scope for this phase:** OAuth 2.1 / PKCE for MCP hosts (see auth plan non-goals). Revisit if Claude/Cursor require AS metadata endpoints.

---

### Phase 3 — CI/CD (½ day)

Mirror frontend/backend workflows.

**Tasks**

- [x] Workflow: `.github/workflows/mcp.yml` — lint/test; preview deploy on PR; prod deploy on `main`
- [x] Smoke test `GET /health` after deploy (optional protection bypass secret)
- [x] Document GitHub secret `VERCEL_MCP_PROJECT_ID` + Root Directory in root README / MCP README
- [ ] Operator: create Vercel MCP project (Root = `services/mcp`) on the backend’s team and set `VERCEL_MCP_PROJECT_ID`
- [ ] Operator: set Vercel env `BACKEND_API_URL` (+ Fluid Compute)

---

### Phase 4 — Hardening & observability (½–1 day)

- [ ] Align MCP timeouts with backend cold starts + search/intake latency.
- [ ] Structured logs: never print `rad_…` (scrubber already on backend; add MCP-side redaction if missing).
- [ ] Confirm scopes/rate limits still enforced on **prod** backend.
- [ ] Runbook: cold start, 401 (bad key), 429, backend 502.
- [ ] Update `services/mcp/README.md` + root README “Deploy MCP (Vercel)” section.
- [ ] Keep local `pnpm run dev:mcp` / stdio path working for developers.

---

### Phase 5 — Alternatives / stretch (Vercel only, no Docker)

Only if Phase 0 fails or prod reliability is poor. **Do not** add Docker or move MCP off Vercel.

| Option | When |
|--------|------|
| **Node `mcp-handler` on Vercel** | FastMCP/Python Streamable HTTP cannot run reliably as a Function — reimplement tools as thin TS proxies to BE |
| **Stateless JSON-RPC subset** | Full streaming/session MCP is unnecessary for our tool set — simplify the ASGI handler |
| **MCP OAuth metadata** | Required by a specific host ecosystem |

---

## Work estimate

| Phase | Effort |
|-------|--------|
| 0 Spike | ½–1 day |
| 1 Packaging | ½–1 day |
| 2 Auth/hosts | ½ day |
| 3 CI/CD | ½ day |
| 4 Hardening/docs | ½–1 day |
| **Total (happy path)** | **~3–4 days** |

---

## Security checklist

- [ ] No `SUPABASE_SERVICE_ROLE_KEY` / HF / ingestion tokens in MCP Vercel env
- [ ] No shared long-lived user JWT in MCP env
- [ ] Clients send `rad_…` per request; keys created/revoked via backend
- [ ] HTTPS only; no plaintext key in git or README samples
- [ ] Deployment Protection / Firewall reviewed for public `/mcp`
- [ ] Admin tools still require `mcp:admin` + `profiles.is_admin` on backend

---

## Test plan

| Layer | What |
|-------|------|
| Preview | Inspector → list tools → `ping_backend` |
| Auth | Missing key → fail closed; valid `rad_…` → tools work |
| Prod BE | `quick_search` (TX / budget) returns matches |
| Timeout | One slow intake/outreach call under `maxDuration` |
| Regression | Local stdio + `dev:mcp` still pass CI |

---

## Rollout sequence

1. **Phase 0** preview URL — prove ASGI + Inspector.
2. **Phase 1–2** production MCP project + documented Cursor HTTP config.
3. **Phase 3** auto-deploy from `main`.
4. **Phase 4** docs; announce URL to operators.
5. Local stdio remains supported indefinitely for contributors.

---

## Open questions (resolve in Phase 0)

1. Does our FastMCP version support **stateless** Streamable HTTP suitable for Vercel Functions?
2. Exact public path: `/mcp` vs `/api/mcp` after rewrites?
3. Does Cursor’s `mcp.json` `headers` field reliably send `Authorization` to remote URLs?
4. Backend cold start + MCP cold start stacked — is Pro plan / Fluid Compute enough for UX?

---

## Explicitly out of scope

- Dockerfiles, container registries, Docker Compose, Kubernetes
- Container PaaS (Fly.io, Railway, Cloud Run, ECS, etc.) as an MCP host
- Running MCP as a long-lived VM/process outside Vercel Functions

---

## Suggested first implementation commit (after plan approval)

```text
chore: add Vercel entry scaffolding for MCP Streamable HTTP

Export FastMCP ASGI app with API-key middleware and vercel.json
mirroring the backend Python deploy pattern (no Docker).
```

_Do not implement until this plan is accepted / adjusted._
