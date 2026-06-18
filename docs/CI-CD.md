# CI/CD

All pipelines run on GitHub Actions. There are four workflow files.

---

## `frontend.yml` — Frontend

**Triggers:** push to `main` or PR touching `frontend/**`

| Job | Runs on | What it does |
|---|---|---|
| `build` | PR | `next build` — verifies the app compiles |
| `deploy-preview` | PR | `vercel deploy` (preview URL) |
| `deploy-prod` | push to `main` | `vercel deploy --prod` |

**Required secrets:** `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_FRONTEND_PROJECT_ID`

---

## `backend.yml` — Backend

**Triggers:** push to `main` or PR touching `backend/**` or `services/ingestion/**`

| Job | Runs on | What it does |
|---|---|---|
| `lint` | PR + push | `ruff check` |
| `deploy-preview` | PR | `vercel deploy` (preview URL) |
| `deploy-prod` | push to `main` | `vercel deploy --prod` |

**Required secrets:** `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_BACKEND_PROJECT_ID`, `VERCEL_AUTOMATION_BYPASS_SECRET`

---

## `coverage.yml` — Coverage Report

**Triggers:** every PR

Runs three parallel jobs, then aggregates:

| Job | What it does |
|---|---|
| `frontend` | `pnpm test:coverage` → uploads `coverage-summary.json` |
| `backend` | `pytest --cov=app --cov-report=json` → uploads `coverage.json` |
| `ingestion` | `pytest --cov=app --cov-report=json` → uploads `coverage.json` |
| `comment` | Downloads all artifacts, posts/updates a coverage table comment on the PR |

The comment is updated (not duplicated) on each new push to the PR branch.

---

## `ingest-on-data-change.yml` — Ingestion trigger

**Triggers:** push to `main` touching the dataset file, or manual `workflow_dispatch`

Calls `POST /api/v1/jobs/run/loopnet-seed` on the ingestion service with the internal trigger token. This kicks off a fresh normalization and upsert of the listing dataset into Supabase.

---

## Secrets reference

| Secret | Used by |
|---|---|
| `VERCEL_TOKEN` | frontend, backend deploy |
| `VERCEL_ORG_ID` | frontend, backend deploy |
| `VERCEL_FRONTEND_PROJECT_ID` | frontend deploy |
| `VERCEL_BACKEND_PROJECT_ID` | backend deploy |
| `VERCEL_AUTOMATION_BYPASS_SECRET` | backend deploy (Vercel deployment protection) |
| `INGESTION_TRIGGER_TOKEN` | ingest-on-data-change workflow |
