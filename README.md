# Real estate consultant

Internal MVP for an **AI-assisted commercial real estate search** workflow: intake, lawful listing ingestion, property understanding, fit-based ranking, saved searches and watchlists, and **draft** broker outreach (no auto-send).

The app is built with **Next.js** and **FastAPI**, backed by **Supabase**, with chat LLMs routed through **OpenRouter** and/or **Hugging Face** on the backend. Details are in [Stack](#stack) below.

---

## Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | [Next.js](https://nextjs.org/) | Product UI, intake, results, watchlists; server components and Route Handlers as appropriate |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) | APIs, modular listing ingestion, normalization, and orchestration of model calls |
| **Data & platform** | [Supabase](https://supabase.com/) | Postgres, authentication, and other Supabase features (e.g. Storage) as the project needs them |
| **LLM** | [OpenRouter](https://openrouter.ai/) and/or [Hugging Face](https://huggingface.co/) | Structured chat for intake, fit summaries, and outreach drafts (`OPENROUTER_API_KEY` preferred when both keys are set) |

Ingestion may integrate additional tools (for example **Apify** or similar) behind FastAPI; those are implementation details of each connector, not replacements for the core stack above.

**MCP adapter:** `services/mcp/` exposes search, listings, and draft outreach
from FastAPI `/api/v1` to AI hosts (Cursor, Claude Desktop, remote Streamable HTTP).
See [`services/mcp/README.md`](services/mcp/README.md).

---

## Local backend (FastAPI)

The Python project and `pyproject.toml` live under **`backend/`**. After `pip install -e ".[dev]"` from `backend/`, start the API either:

- from **`backend/`**: `fastapi dev`, or  
- from **this repo root**: `fastapi dev backend/app/main.py`

Running `fastapi dev` with no path from the repo root fails because the CLI does not pick up `backend/pyproject.toml` by default.

---

## Deploy frontend (Vercel)

Production deploys use **[Vercel](https://vercel.com)** via `.github/workflows/frontend.yml` (not GitHub Pages).

1. In Vercel, import the repo and set **Root Directory** to `frontend` (or link locally: `cd frontend && npx vercel link`).
2. Add **GitHub repository secrets** for the workflow:
   - `VERCEL_TOKEN` — [Vercel account tokens](https://vercel.com/account/tokens)
   - `VERCEL_ORG_ID`, `VERCEL_FRONTEND_PROJECT_ID` — from the linked frontend project settings
3. In the Vercel project (or GitHub secrets for CI builds), set env vars from `frontend/.env.example`:
   - `NEXT_PUBLIC_BACKEND_API_URL` — public URL of the FastAPI backend
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
4. In **Supabase → Authentication → URL configuration**, add redirect URLs:
   - `https://<your-project>.vercel.app/auth/callback`
   - Preview URLs if you test OAuth on PR deployments.

**URLs:** Production is `https://<project-name>.vercel.app` (shown in the workflow deploy step and Vercel dashboard). PRs run **build only**; previews can use Vercel’s Git integration or add a preview deploy job later.

**CI:** On pull requests, the workflow runs `next build` only. On push to `main`, it builds and deploys with `vercel deploy --prebuilt --prod`.

Set `NEXT_PUBLIC_BACKEND_API_URL` in Vercel (frontend project) to the backend production URL below.

---

## Deploy backend (Vercel)

The FastAPI API deploys as a **second Vercel project** via `.github/workflows/backend.yml`.

1. In Vercel, create/import a project with **Root Directory** = `backend` (or `cd backend && npx vercel link`).
2. Add GitHub secrets **`VERCEL_BACKEND_PROJECT_ID`** (backend project ID) and reuse **`VERCEL_TOKEN`** / **`VERCEL_ORG_ID`**. The frontend workflow uses **`VERCEL_FRONTEND_PROJECT_ID`**.
3. In the **backend** Vercel project → **Environment Variables** (Production), set variables from `backend/.env.example` (at minimum `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`, `FRONTEND_ORIGIN` = your frontend Vercel URL, and at least one of `OPENROUTER_API_KEY` or `HF_TOKEN` for chat).
4. Merge to **`main`** to run production deploy (`vercel deploy --prebuilt --prod`).

**URL:** `https://<backend-project-name>.vercel.app` — use this as `NEXT_PUBLIC_BACKEND_API_URL` on the frontend. Routes are unchanged (`/health`, `/api/v1/...`, `/docs`).

**Note:** Serverless cold starts run `init_db()` per instance; keep DB connections pool-friendly. Large seed datasets are excluded via `backend/.vercelignore`.

---

## Deploy MCP (Vercel)

The MCP adapter is a **third Vercel project** (`real-estate-consultant-mcp`) with
**Root Directory** = `services/mcp`. Details: [`services/mcp/README.md`](services/mcp/README.md).

1. In Vercel (same team as the API-key-capable backend), create/import the project and set **Root Directory** = `services/mcp` (or `cd services/mcp && npx vercel link`). Connect the GitHub repo so Vercel deploys on push/PR.
2. GitHub Actions (`.github/workflows/mcp.yml`) only **lints/tests** — it does **not** call `vercel pull` with `VERCEL_TOKEN` (that secret is the frontend/backend team and cannot see this MCP project).
3. In the **MCP** Vercel project → **Environment Variables**:
   - `BACKEND_API_URL` = `https://real-estate-consultant-be-nu.vercel.app` (or your API-key BE URL; no trailing slash)
   - `HTTP_TIMEOUT_SECONDS` = `55`
   - `LOG_LEVEL` = `INFO`
   - Do **not** set `MCP_API_KEY` on the shared deployment (clients send `rad_…` per request)
4. Enable **Fluid Compute** on the MCP project.

**URL:** `https://real-estate-consultant-mcp.vercel.app/mcp` — health: `/health`. Host config template: [`.cursor/mcp.remote.example.json`](.cursor/mcp.remote.example.json). Details: [`services/mcp/README.md`](services/mcp/README.md).

---

## Local frontend (Next.js)

From `frontend/`:

```bash
cp .env.example .env.local
# edit .env.local, then:
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Concurrent from repo root

| Command | Processes |
|---------|-----------|
| `pnpm run dev` | Frontend + backend |
| `pnpm run dev:all` | Frontend + backend + MCP (HTTP `:8900`) |
| `pnpm run dev:mcp` | MCP HTTP only |

MCP stays a separate service (`services/mcp/`). Cursor still uses stdio via `.cursor/mcp.json`; `dev:all` runs the HTTP transport for shared/local clients. See [`services/mcp/README.md`](services/mcp/README.md).
