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

## Repository status

Specification and planning docs are in place; application source is not added yet. When the app exists, this README should gain **local setup**, **environment variables**, and **deployment** sections (as outlined under “Project artifacts” in [docs/spec.md](docs/spec.md)).
