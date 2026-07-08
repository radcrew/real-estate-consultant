# Backend

FastAPI service for the real estate consultant MVP: APIs, ingestion orchestration, and related server-side work. The installable Python package lives under `app/` (ASGI entry: `app.main:app`).

## Requirements

- Python 3.11 or newer

## Setup

From this directory (`backend/`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

On macOS or Linux, use `source .venv/bin/activate` instead of the PowerShell activation line, then the same `python -m pip` lines.

Use **`python -m pip`** (not plain `pip`) so installs always use this venv’s interpreter. That avoids Windows launcher errors if the project was moved and an old `.venv` still pointed at another path.

## Start the backend

Do this **from `backend/`** (the directory that contains `pyproject.toml`). The app package is `app/`; the ASGI app is **`app.main:app`**.

1. **Python environment** — Create and activate a venv (see [Setup](#setup)), then install deps with `python -m pip install -e ".[dev]"`.
2. **Environment file** — Copy `.env.example` to `.env` and set at least the variables you need (see [Configuration](#configuration)).
3. **Run the API** — With the venv activated and cwd still `backend/`:

```powershell
fastapi dev --port 8888
```

This uses `[tool.fastapi]` in `pyproject.toml` (`entrypoint = "app.main:app"`), serves with reload on **http://127.0.0.1:8888**.

**If your shell is at the repository root** (parent of `backend/`), point the CLI at `main.py` so imports resolve:

```powershell
fastapi dev backend/app/main.py --port 8888
```

**Production-style** (no reload, binds `0.0.0.0` by default for `fastapi run`):

```powershell
fastapi run --port 8888
```

**Uvicorn directly** (same app, reload on localhost):

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8888
```

Running `fastapi dev` from the repo root **without** the `backend/app/main.py` path often fails with *Could not find a default file to run* because the CLI does not see `[tool.fastapi]` or the `app` package.

### Useful URLs (default port)

| URL | Description |
|-----|-------------|
| [http://127.0.0.1:8888/health](http://127.0.0.1:8888/health) | Liveness-style check |
| [http://127.0.0.1:8888/api/v1/ping](http://127.0.0.1:8888/api/v1/ping) | Sample versioned route |
| [http://127.0.0.1:8888/openapi.json](http://127.0.0.1:8888/openapi.json) | OpenAPI schema |

## Configuration

Copy `.env.example` to `.env` in this same directory and adjust values as needed.

| Variable   | Purpose |
|------------|---------|
| `APP_NAME` | Title shown in the OpenAPI metadata |

Environment values are loaded from `backend/.env` by path, so loading does not depend on the shell’s current working directory.

## Dataset

**`backend/dataset/raw-data.json`** holds the listing dataset — a **JSON array of objects** (LoopNet-style listing records). It is consumed by the **ingestion service's `loopnet-seed` connector** (`services/ingestion/app/connectors/loopnet_seed.py`), which normalizes each object into a row for Supabase **`public.properties`**. (The backend's standalone seed CLI was removed once the ingestion service took over.)

The connector reads the path in its `dataset_path` setting (default `dataset/raw-data.json`, relative to the ingestion service); for local dev you can point it at this backend copy — see `services/ingestion/app/core/config.py`.

### Dataset preparation

Follow these steps to produce the dataset file:

1. **Scrape LoopNet** using **[Apify](https://apify.com/)**. In the Apify Store, search for **LoopNet** (or “loop”) scrapers **Actors**, pick one that fits your needs, configure the run, and start it.
2. **Trial limit:** On a **free trial**, Apify typically returns only about **50 results** per run. Paid runs can return more, depending on the Actor and your plan.
3. **Export:** When the run finishes, download or export the dataset as **JSON**. Apify may name the file something like **`raw_dataset.json`** (or another default); that is fine as an export artifact.
4. **Place the file:** Copy or rename the export so it exists exactly as **`backend/dataset/raw-data.json`** (create the **`dataset/`** folder under `backend/` if it is missing).
5. **Validate shape:** The file’s root must be a **JSON array** (`[ ... ]`), and each element must be a **JSON object** (`{ ... }`). If the export is wrapped differently (e.g. one object with a `"data"` array), reshape or re-export so the root is the array of listings.

If the file is missing, not found at the configured path, or fails those checks, the connector's run fails and logs the reason.

## Database connection pooling (Vercel serverless)

Each Vercel serverless invocation starts a fresh Python process and calls `init_db()`, which opens a new SQLAlchemy engine. With a direct Postgres connection (port 5432) this creates a new physical connection on every cold start, quickly exhausting Supabase's connection limit under any real traffic.

**Recommended setup for production:** point `DATABASE_URL` at Supabase's **Transaction Pooler** (pgbouncer, port 6543) and set `DB_SERVERLESS=true`.

```
# Vercel production env vars
DATABASE_URL=postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres
DB_SERVERLESS=true
```

`DB_SERVERLESS=true` does two things:

1. **`NullPool`** — SQLAlchemy holds no idle connections between requests; pgbouncer owns the pool.
2. **`statement_cache_size=0`** — disables asyncpg prepared statements, which pgbouncer transaction mode does not support.

Keep `DATABASE_URL` pointing at the direct port (5432) for local dev and schema migrations (pgbouncer transaction mode blocks DDL and `SET` commands).

## Linting

With dev dependencies installed:

```powershell
ruff check app
```

## Deploy on Vercel

Use a **separate Vercel project** from the Next.js frontend (Root Directory = `backend/`).

1. `cd backend && npx vercel link`
2. Set **Production** env vars in Vercel from `.env.example` (`DATABASE_URL`, Supabase keys, `FRONTEND_ORIGIN`, `HF_TOKEN`, …).
3. Push to `main` — `.github/workflows/backend.yml` deploys with `VERCEL_BACKEND_PROJECT_ID`, or deploy locally with `vercel deploy --prod`.

Entrypoint for the serverless bundle: `api/index.py` → `app.main:app` (see `vercel.json`).

See the repo root [README](../README.md#deploy-backend-vercel) for GitHub secrets and wiring `NEXT_PUBLIC_BACKEND_API_URL` on the frontend.
