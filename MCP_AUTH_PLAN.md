# MCP Authorization Plan

Plan for implementing **authorization** for the radestate MCP adapter
(`services/mcp/`). Complements [`MCP_SERVER_PLAN.md`](MCP_SERVER_PLAN.md).

**Goal:** Every MCP tool call runs as a real Supabase **user**, with a clear
login/refresh story for local hosts and a spec-aligned OAuth path for remote
Streamable HTTP — while **`backend/` remains the authorization source of truth**.

---

## Current state (today)

| Piece | Status |
|-------|--------|
| User JWT forwarded as `Authorization: Bearer` to FastAPI | Done (`BackendClient`) |
| Env token `MCP_USER_ACCESS_TOKEN` (stdio / `.env`) | Done |
| Local bootstrap `scripts/setup_local_auth.py` | Done (dev only) |
| Backend enforces user/admin (`get_current_user`, `get_current_admin`, profile ownership) | Done |
| Service role **never** in MCP tool path | Done (by design) |
| Dedicated `app/auth/` package | **Missing** (token still read ad hoc from settings) |
| Token refresh / expiry handling | **Missing** (JWTs expire → 401; operator re-runs setup) |
| Streamable HTTP MCP OAuth (RFC 9728 / OAuth 2.1 + PKCE) | **Missing** (HTTP mode trusts process env only) |
| Per-request identity on multi-client HTTP | **Missing** (one process-level token) |

**Pain we already hit in practice**

1. Expired JWT → all write/search tools 401 until `setup_local_auth.py` is re-run.
2. Empty Cursor-injected env can wipe `.env` values (mitigated with `env_ignore_empty` + launcher loaders; keep that invariant).
3. HTTP (`pnpm run dev:mcp` / `dev:all`) is not multi-user-safe: one shared token for the process.

---

## Principles (non-negotiable)

1. **Backend is SoT** — MCP never invents roles, never uses `SUPABASE_SERVICE_ROLE_KEY` for tool calls, never bypasses `ensure_search_profile_access` / admin checks.
2. **Edge auth only** — MCP authenticates the *host/user*, then obtains or selects a **user** Supabase access token to call `/api/v1`.
3. **Transport-specific**
   - **stdio:** OS process isolation + local secrets (env / keychain file). OAuth optional.
   - **streamable-http:** treat MCP as an **OAuth 2.1 resource server** (MCP auth guidance).
4. **No secret sprawl** — HF / ingestion / service-role keys stay in `backend/` only.
5. **Fail closed** — missing/invalid/expired auth → MCP `isError` with a recoverable message; never crash stdio.
6. **Least privilege** — tools act as the signed-in user; admin tools remain backend-gated.

---

## Target architecture

```text
┌─────────────────┐     token / OAuth      ┌──────────────────┐
│ Cursor / Claude │ ─────────────────────► │ services/mcp     │
│ (MCP host)      │                        │  auth edge       │
└─────────────────┘                        └────────┬─────────┘
                                                    │ Bearer user JWT
                                                    ▼
                                           ┌──────────────────┐
                                           │ backend FastAPI  │
                                           │  get_current_*   │
                                           └────────┬─────────┘
                                                    │
                                                    ▼
                                              Supabase Auth
                                              + Postgres RLS
```

### Module layout (new)

```text
services/mcp/app/auth/
  __init__.py
  context.py          # AuthContext: access_token, user_id?, expires_at?, source
  providers.py        # EnvTokenProvider | RefreshTokenProvider | HttpBearerProvider
  store.py            # local encrypted/plain file for refresh token (stdio)
  refresh.py          # Supabase refresh_token → new access_token
  http_oauth.py       # Phase C: PRM + bearer validation for Streamable HTTP
  errors.py           # AuthRequired / AuthExpired / AuthForbidden
```

Wire `BackendClient` to take token from `AuthContext` (request-scoped for HTTP,
process-scoped for stdio) instead of only `settings.mcp_user_access_token`.

---

## Auth modes

### Mode A — Local stdio (default for Cursor / Claude Desktop)

**Who:** single operator on a workstation.

| Step | Behavior |
|------|----------|
| Bootstrap | `mcp login` (or keep `setup_local_auth.py`) obtains access + **refresh** tokens |
| Storage | `services/mcp/.auth.json` (gitignored) or OS keychain; never commit |
| Runtime | Provider returns access token; on 401 from backend, try refresh once, then `AuthExpired` |
| Host config | `.cursor/mcp.json` / Claude config: **no** long-lived JWT in env — only `BACKEND_API_URL` |

**Authorization:** unchanged — backend JWT validation + ownership checks.

### Mode B — Streamable HTTP (remote / `dev:mcp`)

**Who:** one or more MCP clients over the network.

MCP server is an **OAuth 2.1 resource server**:

1. Unauthenticated call → `401` + `WWW-Authenticate` pointing at **Protected Resource Metadata** (RFC 9728).
2. Client discovers Authorization Server metadata (RFC 8414).
3. Authorization Code + **PKCE**; resource indicator bound to MCP URL (RFC 8707).
4. MCP validates bearer (issuer, exp, audience) **or** exchanges it for a Supabase user JWT.
5. Tools call backend with that **user** JWT.

**Recommended IdP choice for radestate**

| Option | Pros | Cons |
|--------|------|------|
| **B1. Supabase Auth as AS** (prefer if host support is enough) | One identity system already used by the app | MCP OAuth metadata / PKCE quirks; may need a thin broker |
| **B2. Backend broker** `POST /api/v1/mcp/token` (or `/auth/mcp/...`) | Full control; map host token → Supabase session; audit | Extra backend surface to design + harden |
| **B3. External IdP (Auth0/Clerk) later** | Enterprise SSO | Out of scope for v1 |

**v1 recommendation:** implement **B2 (backend broker)** behind MCP HTTP:

- MCP validates the inbound MCP-access token (or session cookie from broker callback).
- Broker endpoint uses existing Supabase sign-in / refresh (anon client — **not** the poisoned service-role data client pattern we already fixed).
- MCP stores a short-lived mapping `mcp_session → supabase_access_token` in memory (or Redis later).

### Mode C — Tool-level authorization (always)

| Class | Examples | Rule |
|-------|----------|------|
| Public / health | `ping_backend` | No user JWT required |
| User read | `get_listing`, `search_properties`, `get_featured_listings` | User JWT; backend may allow some reads anonymously — MCP still prefers user context when available |
| User write | `quick_search`, intake, outreach drafts, `update_search_criteria` | User JWT required |
| Admin | `enqueue_ingest`, `list_listing_submissions` | User JWT + `profiles.is_admin` (backend 403) |

Optional later: declare MCP **scopes** (`radestate:search`, `radestate:outreach`, `radestate:admin`) and refuse tools before calling backend if scope missing. Backend remains final enforcer.

---

## Implementation phases

### Phase A — Auth package + expiry UX (local) — 1 day

**Ship**

- [ ] Create `app/auth/` with `AuthContext` + `EnvTokenProvider`
- [ ] Centralize “require user token” (replace ad hoc `AuthRequiredError` strings)
- [ ] On backend `401`, return clear `AuthExpired` guidance (`mcp login` / re-bootstrap)
- [ ] Document: never paste JWT into committed `mcp.json`; load from `.env` / `.auth.json`
- [ ] Tests: missing token, expired → refresh miss → error text

**Out of scope:** OAuth, multi-user HTTP.

### Phase B — Login CLI + refresh tokens — 1–2 days

**Ship**

- [ ] `radestate-mcp login` (or `python -m app.auth.cli login`) → email/password or browser link against backend `/api/v1/auth/sign-in`
- [ ] Persist `access_token`, `refresh_token`, `expires_at` under `services/mcp/.auth.json` (gitignore)
- [ ] `RefreshTokenProvider`: proactive refresh if `expires_at` within N minutes; reactive refresh on 401 once
- [ ] `radestate-mcp logout` clears store
- [ ] Keep `setup_local_auth.py` as thin wrapper or deprecate in favor of CLI
- [ ] Ensure `run-mcp.cmd` / `scripts/setup.mjs` do not require JWT in Cursor env

**Acceptance:** overnight Cursor session still works without re-pasting a JWT.

### Phase C — HTTP authorization (resource server + broker) — 2–4 days

**Ship**

- [ ] Backend: minimal broker endpoints (names illustrative)
  - `POST /api/v1/mcp/oauth/token` — exchange auth code / refresh for MCP session + Supabase tokens  
  - or reuse Supabase grant and issue a signed MCP session JWT whose `sub` is the user id
- [ ] MCP HTTP middleware: require `Authorization` on tool calls (except discovery + `ping`)
- [ ] Protected Resource Metadata document at well-known URL
- [ ] Per-request `AuthContext` (no process-global user token for HTTP)
- [ ] Rate-limit auth failures; never log raw tokens
- [ ] Integration test: HTTP client without token → 401; with token → `quick_search` works

**Hardening already required in backend (done / keep)**

- Password grants must use the **anon/auth client**, not the service-role data client
  (see recent `supabase_sdk` split) so PostgREST is not poisoned by `SIGNED_IN`.

### Phase D — Scopes, admin step-up, multi-tenant (optional)

- [ ] Scope map on tools; advertise in OAuth consent
- [ ] Step-up / re-consent for admin tools
- [ ] Multi-tenant MCP deploy (separate `BACKEND_API_URL` + IdP per env)
- [ ] Audit log: `request_id`, `user_id`, tool name, status (no PII bodies)

---

## Config additions

```env
# existing
BACKEND_API_URL=http://127.0.0.1:8888
MCP_USER_ACCESS_TOKEN=          # optional override; prefer .auth.json after Phase B
MCP_TRANSPORT=stdio             # stdio | streamable-http

# Phase B+
MCP_AUTH_STORE=./.auth.json     # gitignored
MCP_AUTH_REFRESH_SKEW_SECONDS=120

# Phase C+
MCP_HTTP_PUBLIC_URL=http://127.0.0.1:8900/mcp
MCP_OAUTH_ISSUER=https://<supabase-or-broker>
MCP_OAUTH_AUDIENCE=radestate-mcp
# backend
SUPABASE_ANON_KEY=              # required for password/refresh grants on auth client
```

Update [`.gitignore`](.gitignore) for `services/mcp/.auth.json`.

---

## Security checklist

- [ ] No service role in MCP env for tools
- [ ] No tokens in git, logs, tool outputs, or commit messages
- [ ] Refresh tokens only on disk with restrictive permissions (Windows ACL / `0600`)
- [ ] HTTP: validate `aud` / `exp` / `iss` before accepting a bearer
- [ ] HTTP: bind tokens to MCP resource URL (RFC 8707) when using full OAuth
- [ ] Admin tools: backend `403` is enough for v1; do not soft-allow in MCP
- [ ] Outreach remains draft-only (auth does not imply send)

---

## Testing plan

| Layer | What |
|-------|------|
| Unit | Providers, refresh skew, 401→refresh→retry once, scope gate |
| MCP tools | `quick_search` / intake with valid token; clear error when missing |
| API | Broker token exchange; reject bad audience |
| Manual | Cursor stdio after `mcp login`; Inspector against HTTP with/without bearer |
| Regression | Sign-in must not break `intake_sessions` inserts (service-role client isolation) |

---

## Rollout sequence

1. **Phase A** behind existing env token (low risk).
2. **Phase B** for all local developers; update `services/mcp/README.md` + Cursor/Claude samples.
3. **Phase C** only after HTTP is used beyond localhost, or when a second user must share `dev:mcp`.
4. **Phase D** when product needs scoped third-party agents.

---

## Non-goals

- Replacing Supabase Auth for the Next.js app
- Putting RLS / fit scoring / admin policy into MCP
- Long-lived PATs that skip Supabase user identity
- Impersonation APIs in MCP (support/debug stays in backend admin tools)

---

## Success criteria

1. Local Cursor users authenticate once (`mcp login`) and keep working across JWT expiry via refresh.
2. No JWT required in committed host config files.
3. Streamable HTTP rejects unauthenticated tool calls; authenticated calls reach backend as that user.
4. Admin and ownership rules still enforced solely by FastAPI + Supabase.
5. Docs in `services/mcp/README.md` describe stdio vs HTTP auth clearly.

---

## Open decisions

1. **Broker vs pure Supabase AS for HTTP** — default **backend broker (B2)** unless Cursor/Claude HTTP OAuth against Supabase proves straightforward.
2. **Auth store** — file vs OS keychain first; file is enough for Phase B.
3. **Whether `ping_backend` stays anonymous on HTTP** — yes for liveness; everything else authenticated.
4. **Scopes in v1** — defer to Phase D unless a partner integration needs them immediately.

---

## References

- Repo: [`MCP_SERVER_PLAN.md`](MCP_SERVER_PLAN.md) (Auth model section)
- MCP authorization (OAuth 2.1 resource server, Streamable HTTP) — current MCP spec auth guidance
- RFC 9728 Protected Resource Metadata, RFC 8414 AS metadata, RFC 8707 Resource Indicators
- Existing backend auth: `backend/app/api/v1/endpoints/auth/`, `backend/app/core/deps.py`
- Existing MCP token injection: `services/mcp/app/client/backend.py`
