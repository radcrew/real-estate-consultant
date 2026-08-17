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
| **LLM (optional)** | [AWS Bedrock](https://aws.amazon.com/bedrock/) + Lambda | Per-call-site routing to Bedrock (embeddings, outreach) or a self-hosted Qwen on Lambda (intake parse). Off unless configured — see below |

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

**URLs:** Production is `https://<project-name>.vercel.app` (shown in the workflow deploy step and Vercel dashboard). Pull requests get their own preview URL, posted to the workflow run summary.

**CI:** On pull requests, the workflow builds and then deploys a preview with `vercel deploy`. On push to `main`, it builds and deploys with `vercel deploy --prod`. It runs no lint and no tests. The Vitest suite runs in `.github/workflows/coverage.yml`, on pull requests only, and ESLint runs in no workflow at all, so run `pnpm lint` locally.

Set `NEXT_PUBLIC_BACKEND_API_URL` in Vercel (frontend project) to the backend production URL below.

---

## Deploy backend (Vercel)

The FastAPI API deploys as a **second Vercel project** via `.github/workflows/backend.yml`.

1. In Vercel, create/import a project with **Root Directory** = `backend` (or `cd backend && npx vercel link`).
2. Add GitHub secrets **`VERCEL_BACKEND_PROJECT_ID`** (backend project ID) and reuse **`VERCEL_TOKEN`** / **`VERCEL_ORG_ID`**. The frontend workflow uses **`VERCEL_FRONTEND_PROJECT_ID`**.
3. In the **backend** Vercel project → **Environment Variables** (Production), set variables from `backend/.env.example` (at minimum `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`, `FRONTEND_ORIGIN` = your frontend Vercel URL, and at least one of `OPENROUTER_API_KEY` or `HF_TOKEN` for chat).
4. Merge to **`main`** to run production deploy (`vercel deploy --prod`). Opening a PR deploys a preview first; both are smoke-tested against `/health/ready` and `/api/v1/ping`.

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

## Deploy AWS components (optional)

**None of these are required to run the product.** Each is off until its environment
variable is set, and the backend behaves correctly without any of them — the LLM routes
stay on OpenRouter/Hugging Face and intake turns run inside the request. Design and
rationale: [`AWS_BEDROCK_ARCHITECTURE.md`](AWS_BEDROCK_ARCHITECTURE.md).

| Component | Turned on by | What it changes |
|---|---|---|
| Bedrock embeddings | `LLM_ROUTE_EMBEDDINGS=bedrock` | Similar-listings uses 1024-dim Cohere v3 vectors. **Required before similar-listings returns anything** — the 384-dim default cannot fill the column |
| Bedrock Qwen3-32B | `LLM_ROUTE_OUTREACH_DRAFT=bedrock_qwen` | Outreach drafts move off OpenRouter |
| [`services/qwen-lambda/`](services/qwen-lambda/README.md) | `LLM_ROUTE_INTAKE_PARSE=qwen` | Criteria extraction runs a self-hosted Qwen2.5-0.5B on Lambda |
| [`infra/chat-intake-worker/`](infra/chat-intake-worker/README.md) | `SQS_CHAT_QUEUE_URL` | Intake turns are queued instead of run inline, so a slow provider becomes latency rather than a lost message |
| Bedrock Guardrails | `BEDROCK_GUARDRAIL_ID` | Intake free text is screened (PII redaction) before it is stored |

Two of these are separate deployables with their own environments. Their `LLM_ROUTE_*`
pins must match the backend's, or the same turn gets a different model depending on which
path ran it.

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
