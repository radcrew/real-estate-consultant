# MCP Authorization Plan (API Key)

Plan for implementing **API-key authorization** for the radestate MCP adapter
(`services/mcp/`). Complements [`MCP_SERVER_PLAN.md`](MCP_SERVER_PLAN.md).

**Decision:** Authorize MCP hosts with a **long-lived API key** bound to a
Supabase user (or machine principal). OAuth / refresh-token login is **out of
scope** for this plan (may return later for browser agents).

**Goal:** Cursor, Claude Desktop, and Streamable HTTP clients authenticate with
`MCP_API_KEY` (or equivalent header). Backend resolves the key to a user and
enforces the same ownership/admin rules as JWT sessions — while **`backend/`
remains the authorization source of truth**.

---

## Current state (today)

| Piece | Status |
|-------|--------|
| User JWT forwarded as `Authorization: Bearer` to FastAPI | Done |
| Env `MCP_USER_ACCESS_TOKEN` (short-lived Supabase JWT) | Done — **painful** (expires) |
| Local bootstrap `scripts/setup_local_auth.py` | Done (JWT mint for local only) |
| Backend JWT auth (`get_current_user`) | Done |
| Service role **never** in MCP tool path | Done |
| First-class API keys (create / hash / revoke / resolve) | **Missing** |
| MCP `app/auth/` package | **Missing** |
| HTTP gateway requiring a key | **Missing** (process env JWT only) |

**Pain this plan removes**

1. Expired JWT → 401 until re-bootstrap.
2. Pasting JWTs into host configs.
3. Ambiguous identity on shared HTTP MCP (`dev:mcp`).

---

## Principles (non-negotiable)

1. **Backend is SoT** — issue, hash, validate, and revoke keys in `backend/`.
   MCP never invents roles and never uses `SUPABASE_SERVICE_ROLE_KEY` for tools.
2. **Key → user** — every API key maps to exactly one `auth.users` id (the acting
   principal). Optional: `is_admin` still comes from `profiles`, not the key blob.
3. **Store hashes only** — plaintext key shown once at creation; DB keeps
   `sha256(pepper \|\| key)` hex digest + prefix for lookup.
4. **Same authorization path** — after key resolution, tool calls use the same
   ownership checks as JWT (`ensure_search_profile_access`, `get_current_admin`).
5. **Fail closed** — missing/invalid/revoked key → clear MCP `isError` or HTTP
   `401`; never crash stdio.
6. **No secret sprawl** — HF / ingestion / service-role stay in `backend/` only.
7. **Transport-agnostic credential** — same key works for stdio env and HTTP
   `Authorization` / `X-API-Key`.

---

## Target architecture

```text
┌─────────────────┐   MCP_API_KEY /     ┌──────────────────┐
│ Cursor / Claude │   X-API-Key         │ services/mcp     │
│ or HTTP client  │ ──────────────────► │  pass-through    │
└─────────────────┘                     └────────┬─────────┘
                                                 │ Authorization: Bearer <api_key>
                                                 │ (or X-API-Key)
                                                 ▼
                                        ┌──────────────────┐
                                        │ backend FastAPI  │
                                        │  resolve key →   │
                                        │  user principal  │
                                        └────────┬─────────┘
                                                 │
                                                 ▼
                                           Postgres
                                           mcp_api_keys
                                           + profiles
```

**Preferred model (pass-through):** MCP does **not** exchange the key for a
JWT. It forwards the API key on every backend call. Backend accepts **either**
Supabase JWT **or** API key in `get_current_user` (or a sibling dependency).

Alternative (not preferred): MCP edge validates key and swaps to a short-lived
internal JWT — more moving parts, skip unless we must hide keys from logs at
the proxy boundary.

---

## Credential format

| Item | Convention |
|------|------------|
| Prefix | `rad_` (or `rk_live_` / `rk_test_`) for easy detection + log redaction |
| Entropy | ≥ 32 bytes random (`secrets.token_urlsafe`) |
| Display | `{prefix}{secret}` once at create time |
| Storage | `key_prefix` (first 8 chars) + `key_hash` |
| Header (HTTP) | `Authorization: Bearer rad_…` **or** `X-API-Key: rad_…` |
| Env (stdio) | `MCP_API_KEY=rad_…` |

Redact anything matching `rad_` / `rk_` in MCP + backend logs (extend existing
log scrubbers).

---

## Data model (backend)

Table `public.mcp_api_keys` (name illustrative):

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | |
| `user_id` | uuid FK → `auth.users` | acting principal |
| `name` | text | e.g. "Cursor laptop" |
| `key_prefix` | text | indexed; for lookup candidates |
| `key_hash` | text | unique; verify with constant-time compare |
| `scopes` | text[] / jsonb | optional; default `["*"]` or `["mcp:tools"]` |
| `created_at` | timestamptz | |
| `last_used_at` | timestamptz | nullable; update throttled |
| `revoked_at` | timestamptz | nullable |
| `expires_at` | timestamptz | nullable optional TTL |

RLS: users can `SELECT` / `UPDATE` (revoke) **their own** rows; inserts via
authenticated user or service role from API. Never return `key_hash` to clients.

---

## Backend API surface

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/account/api-keys` | Create key (returns plaintext **once**) |
| `GET` | `/api/v1/account/api-keys` | List metadata (prefix, name, dates) — no secret |
| `DELETE` | `/api/v1/account/api-keys/{id}` | Revoke |
| — | all existing `/api/v1/*` | Accept API key **or** user JWT |

### Auth dependency change

```text
get_current_user:
  1. Read Bearer / X-API-Key
  2. If looks like API key (prefix) → lookup by prefix, verify hash,
     reject if revoked/expired → User(id=key.user_id)
  3. Else → existing Supabase get_user(jwt)
```

Browser app keeps using JWTs. MCP and automation use API keys.

### Optional scopes (v1.1)

| Scope | Tools |
|-------|--------|
| `mcp:read` | listings, search read, featured, ping |
| `mcp:write` | quick_search, intake, criteria, outreach drafts |
| `mcp:admin` | ingest + listing-submissions (still requires `profiles.is_admin`) |

v1 may ship with a single full-access key per user (`scopes = ["*"]`).

---

## MCP adapter changes

### Module layout

```text
services/mcp/app/auth/
  __init__.py
  context.py       # AuthContext(api_key, source=env|header)
  providers.py     # EnvApiKeyProvider | HttpHeaderApiKeyProvider
  errors.py        # AuthRequired / AuthInvalid
```

### Behavior

| Transport | How key is supplied |
|-----------|---------------------|
| **stdio** | `MCP_API_KEY` from `services/mcp/.env` (loaded by `run-mcp.cmd`) |
| **streamable-http** | Require `Authorization: Bearer` or `X-API-Key` **per request**; do not use a process-global user JWT |

`BackendClient`:

- Prefer `MCP_API_KEY` over legacy `MCP_USER_ACCESS_TOKEN`.
- Send as `Authorization: Bearer <api_key>` (backend accepts both shapes).
- On `401`, return actionable error: “API key missing/invalid/revoked — create one via POST /api/v1/account/api-keys”.

### Tool classes

| Class | Examples | Rule |
|-------|----------|------|
| Public | `ping_backend` | No key (liveness) |
| User | search, intake, outreach, saved, agents | Valid API key (or legacy JWT during migration) |
| Admin | `enqueue_ingest`, `list_listing_submissions` | Valid key whose user has `profiles.is_admin` |

---

## Host wiring

### Cursor / Claude (stdio)

```json
{
  "mcpServers": {
    "radestate": {
      "command": "cmd.exe",
      "args": ["/c", "${workspaceFolder}/services/mcp/run-mcp.cmd"],
      "cwd": "${workspaceFolder}/services/mcp",
      "env": {
        "BACKEND_API_URL": "http://127.0.0.1:8888",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

Put the secret only in gitignored `services/mcp/.env`:

```env
BACKEND_API_URL=http://127.0.0.1:8888
MCP_API_KEY=rad_xxxxxxxx
# MCP_USER_ACCESS_TOKEN=   # deprecated after migration
```

### Streamable HTTP

```http
POST /mcp HTTP/1.1
Authorization: Bearer rad_xxxxxxxx
```

Unauthenticated tool calls → `401` + short body. `ping` may remain open.

---

## Migration from JWT env tokens

1. Ship API keys alongside JWT auth (dual accept in `get_current_user`).
2. Document: create a key while signed in (UI or `curl` with JWT).
3. Replace `MCP_USER_ACCESS_TOKEN` with `MCP_API_KEY` in local `.env`.
4. Deprecate `setup_local_auth.py` for daily use (keep for minting a JWT **only** to call `POST /account/api-keys` once, or add a small `scripts/create_mcp_api_key.py`).
5. After one release: warn in MCP logs if only JWT is set; later remove JWT path from MCP docs.

---

## Implementation phases

### Phase 0 — Design freeze — ½ day

- [x] Finalize header names, key prefix, hash algorithm (`sha256` + pepper from env vs `argon2`)
- [x] Confirm dual-auth in `get_current_user` (not a separate router-only gate)
- [x] Add `mcp_api_keys` migration + RLS sketch

### Frozen decisions (Phase 0)

| Topic | Choice |
|-------|--------|
| Credential model | **Pass-through** API key on every backend call (no JWT exchange in MCP) |
| Key prefix | `rad_` |
| Headers | `Authorization: Bearer rad_…` **and** `X-API-Key: rad_…` |
| Hash | `sha256(hex)` of `pepper \|\| raw_key`; pepper = `MCP_API_KEY_PEPPER` (required in non-dev) |
| TTL | No default expiry; nullable `expires_at` supported |
| Scopes | Column present; v1 always `['*']` |
| Dual auth | Extend `get_current_user` to accept API key **or** Supabase JWT |
| MCP legacy JWT | Keep `MCP_USER_ACCESS_TOKEN` fallback one release, then docs-only remove |
| Operator UX (Phase 3) | Script first; Settings UI optional |
| OAuth for MCP | **Out of scope** on this track |

Migration file: `backend/supabase/migrations/20260727_mcp_api_keys.sql`.

### Phase 1 — Backend API keys — 1–2 days

- [x] Apply / verify `mcp_api_keys` migration on target DB
- [x] Repository: create / list / revoke / resolve(raw_key) → user_id
- [x] `POST/GET/DELETE /api/v1/account/api-keys`
- [x] Extend `get_current_user` for API key **or** JWT
- [x] Log redaction for `rad_` secrets
- [x] Tests: create → call protected route with key → revoke → 401
- [x] Tests: JWT path still works for the web app

### Phase 2 — MCP wiring — 1 day

- [x] `app/auth/` + `MCP_API_KEY` settings
- [x] `BackendClient` uses API key; legacy JWT fallback
- [x] Stdio: load from `.env` via existing launchers
- [x] HTTP: per-request key from headers; reject if missing on protected tools
- [x] Clear `AuthRequired` / `AuthInvalid` tool errors
- [x] Update `services/mcp/README.md`, `.env.example`, Cursor/Claude samples
- [x] Tests in `services/mcp/tests/` for missing/invalid key mapping

### Phase 3 — Operator UX — ½–1 day

- [x] Script or CLI: `python scripts/create_mcp_api_key.py` (signs in once / uses existing JWT, prints key)
- [ ] Optional: Settings page in Next.js “MCP API keys” (list / create / revoke) — deferred
- [x] Gitignore notes; never commit keys

### Phase 4 — Hardening

- [x] Key scopes (`mcp:read` / `mcp:write` / `mcp:admin`); HTTP method maps to read vs write; admin routes also need `mcp:admin` + `profiles.is_admin`
- [x] Per-key rate limits (`MCP_API_KEY_RATE_LIMIT_PER_MINUTE`, default 120)
- [x] `last_used_at` updates (sampled ~10%, min 5 minutes)
- [x] Key expiration (`expires_in_days` on create) + rotation docs in MCP README
- [x] Auth audit log line `mcp_api_key_auth` (key_id, prefix, user_id, scopes; no payloads)

---

## Config

### `services/mcp/.env.example`

```env
BACKEND_API_URL=http://127.0.0.1:8888
MCP_API_KEY=
# Deprecated — temporary fallback during migration:
# MCP_USER_ACCESS_TOKEN=
MCP_TRANSPORT=stdio
MCP_HTTP_HOST=127.0.0.1
MCP_HTTP_PORT=8900
```

### `backend/.env.example` (additions)

```env
# Optional pepper for API key hashing (if using sha256+pepper)
MCP_API_KEY_PEPPER=
# Per-key MCP API auth limit (requests/minute, single process)
MCP_API_KEY_RATE_LIMIT_PER_MINUTE=120
```

---

## Security checklist

- [x] Hash at rest; plaintext only in create response
- [x] Constant-time hash compare
- [x] Revoke is immediate
- [x] No keys in git, MCP tool outputs, or commit messages
- [x] Log scrubber covers API key prefixes
- [x] HTTP MCP: no fallback to a shared process JWT when a request omits the key
- [x] Admin tools still require `profiles.is_admin` after key → user resolution
- [x] Outreach remains draft-only
- [x] Per-key rate limit + sampled `last_used_at` + optional expiration

---

## Testing plan

| Layer | What |
|-------|------|
| Unit | Hash/verify, prefix detection, revoked/expired rejection |
| API | CRUD keys; dual auth on a protected route; JWT regression |
| MCP | Tool with key succeeds; without key fails; HTTP header path |
| Manual | Cursor stdio with `MCP_API_KEY`; Inspector HTTP with `Authorization` |

---

## Rollout sequence

1. **Phase 1** to production/backend — dual auth, no MCP break.
2. **Phase 2** — developers switch `.env` to `MCP_API_KEY`.
3. **Phase 3** — one-command key creation; optional UI.
4. **Phase 4** — scopes, rate limits, expiration, rotation docs (done).

---

## Non-goals

- OAuth 2.1 / PKCE for MCP hosts (deferred; not part of this API-key track)
- Replacing Supabase Auth for the Next.js cookie/JWT session
- Service-role or HF tokens inside MCP
- Impersonation (“act as user X”) via a master key
- Putting RLS / fit / admin policy into the MCP process

---

## Success criteria

1. MCP tools work with `MCP_API_KEY` and **do not** require a fresh Supabase JWT daily.
2. Backend resolves key → user; ownership and admin checks unchanged.
3. Revoked keys fail immediately on the next request.
4. Streamable HTTP rejects unauthenticated tool calls; stdio loads key from `.env`.
5. Docs describe create → configure → revoke without mentioning JWT paste (except migration).

---

## Open decisions

_None blocking Phase 1 — see **Frozen decisions (Phase 0)** above._

Historical options (resolved):

1. ~~Hash algorithm~~ → **sha256 + `MCP_API_KEY_PEPPER`**
2. ~~Header~~ → **Bearer and `X-API-Key`**
3. ~~Key TTL~~ → **optional `expires_at`, none by default**
4. ~~UI in v1~~ → **script in Phase 3; UI optional**
5. ~~Legacy JWT in MCP~~ → **fallback one transition period**

---

## References

- Repo: [`MCP_SERVER_PLAN.md`](MCP_SERVER_PLAN.md)
- Backend auth today: `backend/app/core/deps.py`, `backend/app/api/v1/endpoints/auth/`
- MCP client: `services/mcp/app/client/backend.py`
- Prior local JWT bootstrap (migration only): `services/mcp/scripts/setup_local_auth.py`
