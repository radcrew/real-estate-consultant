# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

The import above pulls in the cross-tool non-negotiables and command baseline from [AGENTS.md](./AGENTS.md), shared with other coding agents (Cursor, Codex, etc.). Everything below is Claude Code specific.

## What this is

RadEstate is an internal MVP for AI-assisted **commercial** real estate search: intake, listing ingestion, fit-based ranking, saved searches, and **draft** broker outreach with no auto-send. Four packages, deployed as separate Vercel projects:

| Package | Stack | Role |
|---|---|---|
| `frontend/` | Next 16, React 19, Tailwind v4, Vitest | Product UI, intake, results, account |
| `backend/` | FastAPI, SQLAlchemy async, Supabase, OpenRouter/HF | `/api/v1` plus `/health` |
| `services/mcp/` | FastMCP | Exposes search, listings and draft outreach to AI hosts |
| `services/ingestion/` | FastAPI | Dataset ingestion jobs, own OpenAPI schema |

Only `frontend/` is a pnpm workspace member; the three Python packages each carry their own venv and `pyproject.toml`.

## Working Guidelines

**Think before coding.** State assumptions explicitly rather than silently picking between interpretations. If a request is ambiguous, or a simpler approach exists than the one implied, say so before implementing.

**Simplicity first.** No speculative abstractions, no unrequested configurability, no error handling for scenarios that can't occur at the call site. If a change could be half the size, make it that size.

**Surgical changes.** Touch only what the task requires; match each file's existing style even where you'd choose differently. When your edit makes an import, variable, or function unused, remove it, but leave pre-existing dead code alone and just flag it.

**Goal-driven execution.** For multi-step work, state a short plan with a verification step per item, for example "add the embedded prop, then verify with `pnpm test tests/components/saved`". Use the smallest command that actually exercises the change, not every suite, unless the change spans packages.

**Verify locally, because CI will not.** See AGENTS.md: the frontend suite and lint run in no workflow that gates `main`. "Done" means the relevant command passed in front of you, not "looks right".

**Loops and autonomy.** Autonomous or `/loop`-driven runs need an explicit stop condition (a passing test, a clean lint run) and an iteration cap. Don't loop on judgment calls like visual design or copy tone; those are a human call. If you hit the cap or get stuck, stop and report what you tried and what's blocking, rather than thrashing.

**Text.** In commit messages, PR descriptions, and docs written for this repo: no em-dashes, no filler ("it's worth noting", "essentially"), no LLM tells ("it's not just X, it's Y", "delve"). Reread before finishing and cut anything that doesn't earn its place.

**Commit messages.** After *every* response in which you change one or more files, not just at the end of a multi-step task and not just when asked, automatically draft and show a Conventional Commits message in a copyable code block. Match this repo's history: lowercase `feat:` / `fix:` / `refactor:` / `ui:` / `test:` / `docs:` / `cleanup:` prefix, imperative mood, usually no scope. This applies to small incremental edits too. Scope it to the actual uncommitted change set (check `git status`) and call out any unrelated modified files so they can be excluded. Do not run `git commit` yourself; the user commits manually unless they explicitly ask you to.

**Pull requests.** Follow [.github/PULL_REQUEST_TEMPLATE.md](./.github/PULL_REQUEST_TEMPLATE.md). Do not tick a test checkbox unless you ran the suite and saw it pass. Remember that opening the PR deploys a backend preview.

## Commands

### Install / dev

```bash
pnpm install                 # root, installs the frontend workspace
pnpm dev                     # frontend + backend
pnpm dev:all                 # frontend + backend + MCP adapter
pnpm dev:fe                  # next dev --webpack
pnpm dev:be                  # node backend/scripts/setup.mjs
pnpm dev:mcp                 # node services/mcp/scripts/setup.mjs
```

`dev:be` and `dev:mcp` shell out to a `setup.mjs` that provisions the Python venv before starting the server. They are not bare uvicorn invocations, so a missing venv is handled for you but a broken one is not.

`dev:fe` and `build` both pass `--webpack`, so the repo deliberately opts out of Turbopack. `pnpm --filter radestate dev:turbo` is the opt-in if you want to test under it.

Python, per package:

```bash
cd backend                   # or services/mcp, or services/ingestion
python -m venv .venv
.\.venv\Scripts\Activate.ps1     # Windows; macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
```

The backend can also be started directly with `fastapi dev` from `backend/`, or `fastapi dev backend/app/main.py` from the repo root. A bare `fastapi dev` at the root fails: the CLI does not pick up `backend/pyproject.toml`.

### Lint / test / build

| Package | lint | test | build | single test |
|---|---|---|---|---|
| `frontend` | `pnpm lint` (root) or `pnpm --filter radestate lint` | `pnpm test` from `frontend/` | `pnpm build` | `pnpm test <path>` or `-t "<name>"` |
| `backend` | `ruff check app` | `pytest -q` | *(none; Vercel builds it)* | `pytest tests/api -k "name"` |
| `services/mcp` | `ruff check app tests` | `pytest -q` | *(none)* | `pytest -k "name"` |
| `services/ingestion` | *(no CI lint job)* | `pytest -q` | *(none)* | `pytest -k "name"` |

Current baselines, measured on merge commit `409b0ebc`:

| Package | Tests | Runtime |
|---|---|---|
| `frontend` | 886 across 114 files | ~50s |
| `backend` | 612 | ~3 min |
| `services/ingestion` | 155 | ~2s |
| `services/mcp` | not measured; needs its own venv | — |

ESLint on `main` reports **5 errors and 32 warnings**, all pre-existing: 3 × `react-hooks/set-state-in-effect`, 1 × `@next/next/no-html-link-for-pages`, 1 × `react/no-unescaped-entities`, and warnings dominated by `@next/next/no-img-element` in test mocks. No workflow runs ESLint, so these do not fail anything. Do not treat clearing them as part of an unrelated task, and do not read your own clean run as a clean repo.

### Frontend test setup

`vitest.config.ts` sets `environment: "node"` globally, `globals: true`, and resolves the tsconfig path aliases natively. **Component suites opt into jsdom per file** with a `// @vitest-environment jsdom` docblock on line 1. Forget it and the failure reads as a missing DOM, not as a bad assertion.

Coverage `include` covers `lib/`, `services/`, `utils/`, `config/` and `components/` only. `app/` and `hooks/` are outside the report, so a route handler or hook can be fully untested without moving the number.

## Architecture

### Frontend layout

Paths in this section and the two that follow are relative to `frontend/`.

Path aliases live in `frontend/tsconfig.json` and are resolved by Vitest through `resolve.tsconfigPaths`:

`@lib` `@utils` `@services` `@components` `@app` `@constants` `@hooks` `@contexts` `@config` `@typings` (which maps to `./types/*`, not `./typings/*`).

`components/` is organised by feature (`account`, `admin`, `agents`, `auth`, `blog`, `contact`, `landing`, `listings`, `list-property`, `property`, `saved`, `search`) plus a shared `ui/`.

### Two auth systems in one app

The most common way to get lost in this codebase. Sign-in is split:

- **Email and password** goes to the FastAPI backend: `services/auth.ts` → `POST /api/v1/auth/sign-in`, and the error surfaces through `getApiErrorMessage`.
- **Google OAuth, password reset and password update** go to Supabase directly, via `lib/supabase-browser.ts` (browser, PKCE, cookie-backed) and `lib/supabase-server.ts` (the `/auth/callback` Route Handler).

`lib/auth-session.ts` owns the app's own session under the key `radestate.session`, held in `sessionStorage` **and** mirrored to a cookie so a server render can read it. `contexts/auth.tsx` wraps both systems behind one `useAuth()`.

Consequence: a sign-in bug can live in either system, and the same user-facing string can come from either. When tracing one, find which system produces the message before reading any code. `apiClient` also redirects to `/sign-in?next=…` on any 401, so an unrelated failing request can look like an auth bug.

### Theme and the Voyager palette

`hooks/use-theme-mode.ts` toggles `.dark` on `<html>` and persists to `localStorage.theme`; `app/layout.tsx` carries an inline pre-paint script to avoid a light flash on reload. Any surface that hardcodes a dark color **without** a `dark:` variant will not follow the toggle. That was a real bug in the account sidebar, which painted `bg-neutral-950` unconditionally and stayed dark under a white header.

Much of `components/ui/` is ported from the Voyager template. `app/globals.css` replaces Tailwind's default `neutral` scale with Voyager's coolGrey and adds full `primary-*` / `secondary-*` scales **alongside** shadcn's singular `--color-primary`. A component that looks like it uses stock Tailwind colors probably does not.

Shared style atoms are the place to change spacing: `PAGE_CONTAINER` in `frontend/components/ui/styles.ts` for page width, `ACCOUNT_SECTION_CARD_CLASS` in `frontend/components/account/styles.ts` for account cards. The site header deliberately opts out of `PAGE_CONTAINER` so it spans the full viewport.

### Backend layers

```
api/ (routers)  ->  services/  ->  domain/  ->  repositories/  ->  db/
                         \-> llm/            \-> clients/ingestion/
```

- `api/v1/endpoints/`: `account`, `admin`, `agents`, `auth`, `intake_sessions`, `listings`, `outreach`, `ping`, `questions`, `search`, `submissions`, `submission_images`.
- `domain/` is pure logic (`criteria_search`, `intake_validation`, `similarity`, `search_sql`, `mcp_api_keys`, …) and is where most of the testable behaviour lives.
- `repositories/` is the only layer that talks to the database.
- `core/` holds `config`, `database`, `deps`, `middleware`, `logging`, `exceptions`, plus `api_key_rate_limit` and `db_safe`.

### LLM providers: the precedences are opposite

`llm/providers/` resolves chat and embeddings independently, and **they disagree on purpose** (see the comment in `core/config.py`):

| | `OPENROUTER_API_KEY` + `HF_TOKEN` both set | Only one set | Neither |
|---|---|---|---|
| Chat (`chat.py`) | **openrouter** wins | that one | 503 via `raise_ai_unavailable()` |
| Embeddings (`embeddings.py`) | **huggingface** wins | that one | 503 via `raise_embeddings_unavailable()` |

Reading one resolver and assuming the other matches is the trap. Neither degrades silently: both raise 503 rather than returning empty results.

### Ingestion contract

`backend/app/clients/ingestion/models.py` is **generated** from `services/ingestion/openapi.json` by `scripts/generate_ingestion_models.py`. `backend.yml` regenerates it in CI and fails on any diff, so a hand edit is a guaranteed red build. Change the ingestion schema, regenerate, commit both.

`ingest-on-data-change.yml` POSTs the deployed ingestion service when `services/ingestion/dataset/**` changes on `main`, so a dataset commit is an outward-facing action.

### MCP adapter

`services/mcp/` wraps FastAPI `/api/v1` for AI hosts (Cursor, Claude Desktop, remote Streamable HTTP). It holds no domain logic: every tool calls the backend. Read tools are `search_properties`, `get_listing`, `get_similar_listings`, `get_outreach_draft`; write tools are `quick_search` and `generate_outreach_draft`. Outreach is **draft-only** and must never be described as sent.

## Deployment and CI

Four Vercel projects. See AGENTS.md for what each workflow does and does not check.

- **Frontend** (`frontend.yml`): build only on PR; build and `vercel deploy --prebuilt --prod` on push to `main`. Vercel Root Directory is `frontend`, but `frontend/vercel.json` runs `cd .. && pnpm install --frozen-lockfile` and `cd .. && pnpm --filter radestate build`, because the lockfile lives at the repo root.
- **Backend** (`backend.yml`): Ruff and the ingestion contract check, then a **preview deploy on every PR** and a production deploy on `main`, each followed by a smoke test. Root Directory is `backend`, and the repo-root `.vercelignore` contains `backend/` so the frontend project does not pull it in.
- **MCP** (`mcp.yml`): Ruff and pytest only. Deploys come from the Vercel Git integration under a **different Vercel team**; `secrets.VERCEL_TOKEN` cannot see that project.
- **Ingestion**: no workflow of its own beyond `coverage.yml` and the dataset trigger.

The backend runs as a **single Vercel Python function**: `backend/vercel.json` rewrites `/(.*)` to `/api/index`, and `api/index.py` is a two-line re-export of `app.main:app`. Cold starts are real, around 6.5s idle versus 2.5s warm on `/health`, which is worth remembering before blaming application code for a slow first request.

`NEXT_PUBLIC_*` variables are inlined at build time, so changing one in Vercel requires a redeploy, not just a restart.

## Docs

- [README.md](./README.md) is current on stack, local setup, deploy steps and env vars, and is explicit that frontend PRs run build only. Trust it.
- [CONTRIBUTING.md](./CONTRIBUTING.md) is **stale on tooling**: it prescribes `npm` in a pnpm repo and claims parity between local checks and CI that does not exist. Do not cite it; fixing it is welcome.
- `backend/app/core/config.py` is the source of truth for backend configuration. When you change a setting's name, default or meaning, update `backend/.env.example` in the same commit.
- `services/mcp/README.md` covers the adapter and host config.
