# MCP Server — Implementation Plan

## Goal

Expose the commercial real estate (CRE) consultant platform to AI hosts (Cursor,
Claude Desktop, custom agents) via the **Model Context Protocol (MCP)**. Agents
should be able to run intake, search listings with fit scores, explain matches,
manage saved listings, and draft broker outreach — without reimplementing domain
logic.

Product constraints stay the same: outreach is **draft-only** (no auto-send),
and secrets (`SUPABASE_SERVICE_ROLE_KEY`, `HF_TOKEN`, ingestion tokens) never
leave the server.

---

## Target project structure (scalable)

How the monorepo should look once MCP lands. Optimized for **independent
deployability**, **clear ownership boundaries**, and **horizontal growth** of
agent tools — without forking domain logic out of FastAPI.

### Scalability principles

1. **One domain authority** — `backend/` owns business rules, SQL scoring, LLM
   prompts, and Postgres/Supabase access. MCP never talks to the DB or HF
   directly.
2. **Services are adapters** — `services/*` are independently runnable processes
   (ingestion pipeline, MCP protocol adapter). They call `backend` (or shared
   infra) instead of reimplementing repositories.
3. **Transport ≠ tools** — keep stdio / Streamable HTTP behind a thin transport
   layer so the same tool registry serves Cursor locally and remote agents later.
4. **Domain-sliced tools** — one module per product domain (`search`, `intake`,
   `outreach`, …). Add tools by adding files; avoid a single god-module.
5. **Extract shared packages late** — introduce `packages/` only when a second
   consumer needs the same HTTP client/types (MCP + a future worker). Until then,
   keep the backend client inside `services/mcp/app/client/`.
6. **CI and deploy per surface** — frontend, backend, ingestion, and MCP each
   get their own workflow/root so one service can scale or fail independently.
7. **Auth at the edge, enforce in backend** — MCP resolves a user JWT and
   forwards it; `backend` remains the authorization source of truth.
8. **Do not nest MCP inside Vercel serverless `backend/`** for v1 — stdio hosts
   and long-lived MCP sessions do not fit that lifecycle. Keep `services/mcp`.

### Full tree (target)

Omits build/cache dirs (`node_modules`, `.next`, `.venv`, `__pycache__`, etc.).
Comments mark **NEW** (MCP) vs existing. Frontend/UI leaf files are collapsed
where they do not affect service boundaries.

```
real-estate-consultant/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   ├── config.yml
│   │   └── feature_request.yml
│   ├── workflows/
│   │   ├── backend.yml
│   │   ├── coverage.yml
│   │   ├── frontend.yml
│   │   ├── ingest-on-data-change.yml
│   │   └── mcp.yml                      # NEW — lint/test (and later deploy)
│   └── PULL_REQUEST_TEMPLATE.md
│
├── backend/                               # Domain API — single source of truth
│   ├── api/
│   │   └── index.py                       # Vercel ASGI entry
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── router.py
│   │   │   ├── system.py
│   │   │   └── v1/
│   │   │       ├── router.py
│   │   │       └── endpoints/
│   │   │           ├── account/           # profile, password, avatar, saved
│   │   │           ├── admin/             # ingest enqueue
│   │   │           ├── agents.py
│   │   │           ├── auth/              # sign-in / sign-up
│   │   │           ├── intake_sessions/   # guided + LLM answers, complete
│   │   │           ├── listings/          # detail + featured
│   │   │           ├── outreach/          # draft-only emails
│   │   │           ├── ping/
│   │   │           ├── questions/
│   │   │           ├── search/            # criteria search + fit explain
│   │   │           ├── submissions.py
│   │   │           └── submission_images.py
│   │   ├── clients/
│   │   │   └── ingestion/                 # typed HTTP → ingestion service
│   │   ├── core/                          # config, deps, db, supabase, logging
│   │   ├── db/
│   │   ├── domain/                        # criteria, validation, search SQL
│   │   ├── llm/
│   │   │   ├── fit/
│   │   │   ├── intake/
│   │   │   ├── outreach/
│   │   │   └── providers/                 # Hugging Face
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   ├── dataset/
│   │   └── raw-data.json
│   ├── scripts/
│   │   └── setup.mjs
│   ├── tests/
│   │   ├── api/
│   │   ├── domain/
│   │   ├── llm/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   └── utils/
│   ├── .env.example
│   ├── pyproject.toml
│   ├── README.md
│   ├── requirements.txt
│   └── vercel.json
│
├── frontend/                              # Product UI (Next.js) — unchanged role
│   ├── app/                               # App Router routes
│   │   ├── (auth)/
│   │   ├── (landing)/
│   │   ├── account/
│   │   ├── admin/
│   │   ├── api/
│   │   ├── questionnaire/
│   │   ├── search/
│   │   ├── layout.tsx
│   │   └── ...
│   ├── components/                        # UI by domain
│   │   ├── account/
│   │   ├── admin/
│   │   ├── agents/
│   │   ├── auth/
│   │   ├── landing/
│   │   ├── listings/
│   │   ├── property/
│   │   ├── search/
│   │   ├── saved/
│   │   └── ui/
│   ├── config/
│   ├── contexts/
│   ├── hooks/
│   ├── lib/                               # api-client, supabase, session
│   ├── public/
│   ├── services/                          # Axios wrappers → backend /api/v1
│   │   ├── account.ts
│   │   ├── admin.ts
│   │   ├── auth.ts
│   │   ├── intake-sessions.ts
│   │   ├── listings.ts
│   │   ├── outreach.ts
│   │   └── search.ts
│   ├── tests/
│   ├── types/
│   ├── utils/
│   ├── package.json
│   ├── README.md
│   └── vercel.json
│
├── services/
│   ├── ingestion/                         # Write-side listing pipeline
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── api/
│   │   │   │   ├── jobs.py
│   │   │   │   ├── router.py
│   │   │   │   └── system.py
│   │   │   ├── connectors/
│   │   │   │   ├── base.py
│   │   │   │   ├── loopnet_seed.py
│   │   │   │   └── rate_limit.py
│   │   │   ├── core/
│   │   │   ├── models/
│   │   │   ├── repositories/
│   │   │   └── utils/
│   │   ├── migrations/
│   │   ├── tests/
│   │   ├── .env.example
│   │   ├── openapi.json
│   │   ├── pyproject.toml
│   │   └── requirements.txt
│   │
│   └── mcp/                               # NEW — MCP protocol adapter
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py                    # process entry (transport select)
│       │   ├── server.py                  # register tools / resources / prompts
│       │   ├── config.py                  # pydantic-settings
│       │   ├── logging.py                 # stderr-only structured logs
│       │   │
│       │   ├── auth/                      # edge auth only — no service role
│       │   │   ├── __init__.py
│       │   │   ├── context.py             # current user token for a session
│       │   │   └── token.py               # env JWT (v1) / OAuth later
│       │   │
│       │   ├── transport/                 # swap without touching tools
│       │   │   ├── __init__.py
│       │   │   ├── stdio.py               # local Cursor / Claude Desktop
│       │   │   └── streamable_http.py     # remote / multi-tenant later
│       │   │
│       │   ├── client/                    # only outbound dependency: backend
│       │   │   ├── __init__.py
│       │   │   ├── backend.py             # httpx AsyncClient + /api/v1 helpers
│       │   │   ├── errors.py              # map HTTP → MCP isError payloads
│       │   │   └── models.py              # response DTOs (thin; not domain)
│       │   │
│       │   ├── middleware/                # cross-cutting, keeps tools thin
│       │   │   ├── __init__.py
│       │   │   ├── timeouts.py
│       │   │   ├── rate_limit.py
│       │   │   └── sanitize.py            # scrub tool outputs before model
│       │   │
│       │   ├── tools/                     # one file (or package) per domain
│       │   │   ├── __init__.py             # export registry / register_all()
│       │   │   ├── _common.py             # shared result helpers
│       │   │   ├── search.py              # search_properties, update_criteria
│       │   │   ├── listings.py            # get_listing, get_featured_listings
│       │   │   ├── fit.py                 # explain_fit
│       │   │   ├── intake.py              # start / answer / complete / get
│       │   │   ├── outreach.py            # draft generate / get / update
│       │   │   ├── account.py             # list_saved_listings
│       │   │   ├── agents.py              # get_agent
│       │   │   └── admin.py               # optional, admin-gated (phase 3)
│       │   │
│       │   ├── resources/                 # optional MCP resources
│       │   │   ├── __init__.py
│       │   │   ├── listing.py             # listing://{property_id}
│       │   │   ├── search.py              # search://{session_profile_id}
│       │   │   └── intake.py              # intake://{session_id}
│       │   │
│       │   └── prompts/                   # optional workflow templates
│       │       ├── __init__.py
│       │       ├── cre_search.py
│       │       └── draft_outreach.py
│       │
│       ├── tests/
│       │   ├── conftest.py
│       │   ├── test_server.py             # tool registration smoke
│       │   ├── test_auth.py
│       │   ├── client/
│       │   │   └── test_backend.py
│       │   ├── tools/
│       │   │   ├── test_search.py
│       │   │   ├── test_listings.py
│       │   │   ├── test_fit.py
│       │   │   ├── test_intake.py
│       │   │   ├── test_outreach.py
│       │   │   └── test_account.py
│       │   └── middleware/
│       │       ├── test_rate_limit.py
│       │       └── test_sanitize.py
│       │
│       ├── .env.example
│       ├── .gitignore
│       ├── pyproject.toml                 # consultant-mcp
│       ├── README.md                      # Cursor / Claude host wiring
│       └── requirements.txt
│
├── packages/                              # OPTIONAL later (extract when needed)
│   └── README.md                          # e.g. shared OpenAPI backend client
│       # packages/backend-client/         # only after 2+ Python consumers
│
├── scripts/
│   └── generate_ingestion_models.py
│
├── docs/                                  # OPTIONAL — move long plans here later
│   └── MCP_SERVER_PLAN.md                 # (or keep at repo root for now)
│
├── .gitignore
├── .vercelignore
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── FEATURE_IDEAS.md
├── FIT_EXPLAINABILITY_PLAN.md
├── LICENSE
├── MCP_SERVER_PLAN.md
├── SECURITY.md
├── code-quality-review.md
├── package.json                           # pnpm root: FE+BE dev scripts
├── pnpm-workspace.yaml                    # JS workspace: frontend only
└── README.md
```

### Boundary diagram (what talks to what)

```
                    ┌─────────────────────────────────────────┐
                    │           AI hosts (Cursor, etc.)       │
                    └────────────────────┬────────────────────┘
                                         │ MCP (stdio / HTTP)
                                         ▼
┌──────────────┐   HTTPS JWT    ┌────────────────┐   internal    ┌──────────────┐
│   frontend   │ ─────────────► │    backend     │ ────────────► │  ingestion   │
│   (Next.js)  │                │   (FastAPI)    │               │  (jobs)      │
└──────────────┘                │  /api/v1/*     │               └──────────────┘
                                └───────▲────────┘
                                        │ HTTPS + user JWT
                                ┌───────┴────────┐
                                │  services/mcp  │
                                │  (adapter)     │
                                └────────────────┘

  ✓ MCP → backend only
  ✗ MCP → database / HF / Apify / service-role key
  ✗ MCP → ingestion job processor (admin tools go via backend)
```

### What not to do (anti-patterns)

| Anti-pattern | Why it hurts scale |
|--------------|--------------------|
| Copy SQL / LLM prompts into MCP | Two sources of truth; drift and double maintenance |
| One `tools.py` with every tool | Merge conflicts; models confuse overlapping tools |
| Mount MCP on Vercel `backend` for stdio | Wrong process model; cold starts break hosts |
| MCP uses `SUPABASE_SERVICE_ROLE_KEY` | Bypasses user auth; over-privileged agent surface |
| Shared `packages/` on day one | Premature abstraction; extract after second consumer |
| God tool `run_anything(sql=...)` | Unbounded blast radius; impossible to reason about |

### Growth path

| Stage | Structure change |
|-------|------------------|
| **v1** | Add `services/mcp/` as above; tools call backend HTTP |
| **v1.1** | Add `transport/streamable_http.py` + remote auth |
| **v2** | If another Python service needs the same API client, extract `packages/backend-client/` |
| **Later** | Optional `docs/` for architecture plans; optional second MCP server only if tool count / tenancy demands isolation |

## Why MCP here

Today the product surface is:

| Client | How it talks to the platform |
|--------|------------------------------|
| Next.js UI | Axios → `/api/v1/*` with Supabase JWT |
| Ingestion | Internal bearer → job endpoints |
| LLM features | Hugging Face inside FastAPI (`intake` / `fit` / `outreach`) |

MCP adds a third client class: **AI hosts** that discover tools/resources and
call them over stdio or Streamable HTTP. The backend already has the domain
APIs and LLM services; MCP should be a thin adapter over those, not a second
business layer.

---

## Recommended architecture

### Preferred: new package `services/mcp/`

Mirror `services/ingestion/`: a standalone Python service that:

1. Speaks MCP (tools, resources, optional prompts).
2. Calls the existing FastAPI backend over HTTP (`BACKEND_API_URL` + user JWT).
3. Stays deployable and auth-scoped separately from the browser API.

```
┌─────────────────┐     MCP (stdio / Streamable HTTP)     ┌──────────────────┐
│  Cursor / Claude│ ─────────────────────────────────────►│  services/mcp    │
│  / custom agent │                                       │  (MCP adapter)   │
└─────────────────┘                                       └────────┬─────────┘
                                                                   │ HTTP + Bearer JWT
                                                                   ▼
                                                          ┌──────────────────┐
                                                          │  backend FastAPI │
                                                          │  /api/v1/*       │
                                                          └────────┬─────────┘
                                                                   │
                                                          Supabase + HF LLM
```

### Alternatives (not preferred for v1)

| Option | Pros | Cons |
|--------|------|------|
| **A.** Mount MCP inside `backend/app/mcp/` | In-process reuse of repos/LLM | Couples MCP lifecycle to Vercel serverless; harder stdio local DX |
| **B.** Node MCP under `frontend/` | Reuse TS types | Weak access to SQL scoring / HF unless it still proxies backend |

Stick with **`services/mcp`** unless a later phase needs in-process latency for
LLM tools (then consider Option A for fit/outreach only).

---

## Stack choices

| Concern | Choice | Notes |
|---------|--------|-------|
| Language | **Python 3.11+** | Matches backend/ingestion; team already owns FastAPI patterns |
| SDK | **`mcp` (official Python SDK)** or **FastMCP** | Prefer official SDK for longevity; FastMCP OK if it speeds v1 |
| Validation | Pydantic / JSON Schema on tool inputs | Same discipline as FastAPI request bodies |
| Local transport | **stdio** | Cursor / Claude Desktop spawn the process |
| Remote transport | **Streamable HTTP** | Not legacy SSE; for hosted agents later |
| Backend client | `httpx` AsyncClient | Typed wrappers around `/api/v1` paths |
| Auth | Supabase access token as MCP auth context | Pass as `Authorization: Bearer` to backend; never service-role |

Logging: **stderr only** when using stdio (stdout is the JSON-RPC wire).

---

## Package layout

See **Target project structure → `services/mcp/`** above for the full scalable
layout (`transport/`, `client/`, `middleware/`, domain-sliced `tools/`, tests).

Root README should link `services/mcp/README.md` the same way it documents
ingestion.


---

## Tool catalog (v1)

Keep the tool list small and non-overlapping so models pick the right one.
Prefer **read-heavy** tools first; mark writes clearly in descriptions.

### Phase 1 — Read + search (ship first)

| Tool | Maps to | Side effects |
|------|---------|--------------|
| `search_properties` | `GET /api/v1/search/{session_profile_id}` | None |
| `update_search_criteria` | `PUT /api/v1/search/{session_profile_id}` | Updates session criteria |
| `get_listing` | `GET /api/v1/listings/{id}` | None |
| `get_featured_listings` | featured listings endpoint | None |
| `explain_fit` | `POST /api/v1/search/{id}/fit/{property_id}` | LLM call (no persist) |
| `list_saved_listings` | account saved listings | None |
| `get_agent` | `GET /api/v1/agents/{broker}` | None |

### Phase 2 — Intake + outreach drafts

| Tool | Maps to | Side effects |
|------|---------|--------------|
| `start_intake_session` | `POST /api/v1/intake-sessions/?mode=…` | Creates session |
| `answer_intake` | guided / LLM answer endpoints | Mutates session |
| `complete_intake` | `POST .../complete` | Creates search profile |
| `get_intake_session` | `GET /api/v1/intake-sessions/{id}` | None |
| `generate_outreach_draft` | outreach draft create | Creates **draft only** |
| `get_outreach_draft` | get draft | None |
| `update_outreach_draft` | patch draft | Edits draft text |

### Phase 3 — Admin / ops (optional, gated)

| Tool | Maps to | Notes |
|------|---------|-------|
| `enqueue_ingest` | `POST /api/v1/admin/ingest` | Admin JWT only |
| `list_listing_submissions` | admin submissions | Admin only |

**Explicit non-goals for MCP v1**

- Sending email / contacting brokers
- Exposing service-role or HF tokens
- Raw SQL or arbitrary PostgREST
- Direct Apify / ingestion job processor control from user agents

---

## Resources & prompts (optional, after tools work)

**Resources** (context the model can read):

- `listing://{property_id}` — normalized listing JSON
- `search://{session_profile_id}` — current criteria + top matches summary
- `intake://{session_id}` — session status + criteria

**Prompts** (reusable workflows):

- `cre_property_search` — “Given user needs, run intake → search → explain top fits”
- `draft_broker_outreach` — “For property X and session Y, draft a professional email”

Ship these in Phase 2 once tool names stabilize.

---

## Auth model

1. **Local stdio (dev):** `MCP_USER_ACCESS_TOKEN` (or `SUPABASE_ACCESS_TOKEN`) in
   `services/mcp/.env`. Operator signs in via the app or Supabase, pastes a
   short-lived user JWT. Tools call backend with that bearer.
2. **Remote Streamable HTTP (later):** OAuth 2.1 / token passthrough per MCP
   auth guidance; map host identity → Supabase JWT or exchange code for one.
3. **Authorization:** Backend remains source of truth (`get_current_user`,
   `ensure_search_profile_access`, `get_current_admin`). MCP does not bypass RLS
   or admin checks.
4. **Never** put `SUPABASE_SERVICE_ROLE_KEY` in the MCP process env for tool use.

Tool descriptions should state that the caller acts as the authenticated user.

---

## Config (`.env.example`)

```
BACKEND_API_URL=http://127.0.0.1:8888
MCP_USER_ACCESS_TOKEN=
MCP_TRANSPORT=stdio          # stdio | streamable-http
MCP_HTTP_HOST=127.0.0.1
MCP_HTTP_PORT=8900
HTTP_TIMEOUT_SECONDS=60
```

---

## Host wiring (local)

### Cursor

Example MCP config (user-level or project `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "radestate": {
      "command": "python",
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

Exact schema follows Cursor’s current MCP settings; keep the README as the
source of truth once verified.

### Claude Desktop

Same idea: spawn `python -m app.main` with cwd + env. Document in
`services/mcp/README.md`.

---

## Implementation phases

### Phase 0 — Skeleton (½–1 day)

- [x] Create `services/mcp/` with `pyproject.toml`, venv, `app/main.py`
- [x] Register a no-op / `ping` tool that hits `GET /api/v1/ping`
- [x] Stdio transport + stderr logging
- [x] Smoke-test with MCP Inspector
- [x] Document run instructions in `services/mcp/README.md`

### Phase 1 — Core read tools (1–2 days)

- [x] `httpx` backend client with auth header injection
- [x] Implement Phase 1 tools (search, listing, fit, saved, agent)
- [x] Stable JSON text responses; `isError: true` on failures (don’t throw)
- [x] Unit tests with mocked HTTP
- [ ] Manual Cursor smoke: search session → get listing → explain fit

### Phase 2 — Intake + outreach (1–2 days)

- [ ] Intake tools (start / answer / complete / get)
- [ ] Outreach draft tools (generate / get / update)
- [ ] Optional resources + `cre_property_search` prompt
- [ ] Harden tool descriptions so write vs read is obvious

### Phase 3 — Hardening & remote (as needed)

- [ ] Streamable HTTP transport for hosted agents
- [ ] Rate limits / timeouts per tool
- [ ] Sanitize tool outputs before they re-enter model context (injection hygiene)
- [ ] Admin-gated tools
- [ ] CI job: lint + pytest for `services/mcp`
- [ ] Optional: link from root `README.md` and `FEATURE_IDEAS.md`

---

## Error & response conventions

- Always return MCP content results; set `isError: true` on backend 4xx/5xx.
- Map HTTP status to short recoverable messages (“session not found”, “unauthorized”).
- Keep payloads compact: prefer summaries + ids; let the model call `get_listing`
  for full detail instead of dumping large result sets.
- Cap list sizes (e.g. top 10 matches) unless the tool takes an explicit `limit`.

---

## Testing strategy

| Layer | What |
|-------|------|
| Unit | Tool handlers with mocked `BackendClient` |
| Contract | Assert tool input schemas match backend query/body fields |
| Integration (manual) | Backend + MCP Inspector + real JWT against local API |
| Regression | Don’t break existing FastAPI tests; MCP is additive |

No need to run the Next.js app for MCP-only verification.

---

## Security checklist

- [ ] User-scoped JWT only; no service role in MCP
- [ ] Draft-only outreach; no send tool
- [ ] Admin tools require admin JWT (backend enforces)
- [ ] Stdio: no `print`/`console.log` on stdout
- [ ] Timeouts on all outbound HTTP
- [ ] Do not echo secrets in tool results or logs
- [ ] Treat listing/description text as untrusted when feeding back to the model

---

## Success criteria

v1 is done when:

1. Cursor (or MCP Inspector) lists the Phase 1 tools.
2. With a valid user JWT and a real search session id, an agent can search,
   fetch a listing, and get a fit explanation through MCP alone.
3. No new secrets are required beyond a user access token + backend URL.
4. Backend domain logic remains the single source of truth (no duplicated
   scoring/LLM prompts in the MCP package).

---

## Open decisions

Resolve before or during Phase 0:

1. **SDK:** official `mcp` Python SDK vs FastMCP — default to official unless
   FastMCP clearly cuts boilerplate.
2. **Token UX:** paste JWT in env vs small CLI `mcp login` that stores a refresh
   token locally (nice-to-have after v1).
3. **In-process later?** If fit/outreach latency from HTTP hop is a problem,
   extract shared client libraries or mount MCP routes on FastAPI (Option A).
4. **Product name in host config:** `radestate` vs `real-estate-consultant` —
   match the frontend brand (`radestate`) for host-facing server name.

---

## Related docs

- Root architecture: `README.md`
- Existing LLM/API patterns: `FIT_EXPLAINABILITY_PLAN.md`, `backend/README.md`
- Security reporting: `SECURITY.md`
- Ingestion microservice precedent: `services/ingestion/`
