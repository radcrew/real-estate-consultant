# Real estate consultant

Internal MVP for an **AI-assisted commercial real estate search** workflow: intake, lawful listing ingestion, property understanding, fit-based ranking, saved searches and watchlists, and **draft** broker outreach (no auto-send).

The app is built with **Next.js** and **FastAPI**, backed by **Supabase**, with LLMs accessed through **OpenRouter**. Details are in [Stack](#stack) below and in [docs/spec.md](docs/spec.md).

---

## Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | [Next.js](https://nextjs.org/) | Product UI, intake, results, watchlists; server components and Route Handlers as appropriate |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) | APIs, modular listing ingestion, normalization, and orchestration of model calls |
| **Data & platform** | [Supabase](https://supabase.com/) | Postgres, authentication, and other Supabase features (e.g. Storage) as the project needs them |
| **LLM** | [OpenRouter](https://openrouter.ai/) | Model routing and API for extraction, fit summaries, ranking explanations, and outreach drafts |

Ingestion may integrate additional tools (for example **Apify** or similar) behind FastAPI; those are implementation details of each connector, not replacements for the core stack above.

---

## Documentation

Start with the product spec, then drill into scope boundaries.

| Document | Description |
|----------|-------------|
| [docs/spec.md](docs/spec.md) | Product vision, MVP pillars, architecture principles, stack alignment |
| [docs/mvp-scope.md](docs/mvp-scope.md) | Structured Phase 1 scope (intake through admin foundation) |
| [docs/out-of-scope.md](docs/out-of-scope.md) | Explicit MVP exclusions |

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
   - `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` — from the linked project settings
3. In the Vercel project (or GitHub secrets for CI builds), set env vars from `frontend/.env.example`:
   - `NEXT_PUBLIC_BACKEND_API_URL` — public URL of the FastAPI backend
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
4. In **Supabase → Authentication → URL configuration**, add redirect URLs:
   - `https://<your-project>.vercel.app/auth/callback`
   - Preview URLs if you test OAuth on PR deployments.

**URLs:** Production is `https://<project-name>.vercel.app` (shown in the workflow deploy step and Vercel dashboard). PRs run **build only**; previews can use Vercel’s Git integration or add a preview deploy job later.

**CI:** On pull requests, the workflow runs `next build` only. On push to `main`, it builds and deploys with `vercel deploy --prebuilt --prod`.

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
