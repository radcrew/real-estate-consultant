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

Environment values are loaded from `backend/.env` by path, so loading does not depend on the shell’s current working directory.

### Core

| Variable | Required | Purpose |
|----------|----------|---------|
| `DATABASE_URL` | yes | Postgres connection string (Supabase) |
| `SUPABASE_URL` | yes | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | yes | Service role key for server-side Supabase calls |
| `SUPABASE_ANON_KEY` | recommended | Anon key where the backend needs it |
| `FRONTEND_ORIGIN` | recommended | Comma-separated CORS origins (Next dev/prod URLs) |
| `DB_SERVERLESS` | Vercel | Set `true` when `DATABASE_URL` uses Supabase pgbouncer (port 6543) |

### Chat LLM (OpenRouter + Hugging Face)

Smart Chat, intake parsing, fit explanations, and outreach drafts all call one chat entry point (`app.llm.providers.chat`). Provider selection is by API keys only:

| Keys set | Chat provider |
|----------|---------------|
| `OPENROUTER_API_KEY` | **OpenRouter** (wins even if `HF_TOKEN` is also set) |
| `HF_TOKEN` only | **Hugging Face** |
| neither | No LLM — API returns **503** with `"AI unavailable"` |

Optional tuning: `OPENROUTER_CHAT_MODEL`, `OPENROUTER_BASE_URL`, `HF_MODEL`, `HF_BASE_URL`, and per-provider cost telemetry vars (see `.env.example`). Hugging Face chat uses JSON-object responses validated locally (avoids flaky grammar-constrained structured outputs on the Inference Providers router).

### Embeddings (Bedrock + OpenRouter + Hugging Face)

`app.llm.providers.embeddings` uses a **separate** priority from chat so both keys can be set with chat on OpenRouter and embeddings on Hugging Face:

| Keys set | Embeddings provider |
|----------|---------------------|
| `HF_TOKEN` | **Hugging Face** (wins even if `OPENROUTER_API_KEY` is also set) |
| `OPENROUTER_API_KEY` only | **OpenRouter** |
| `AWS_REGION` only | **Bedrock** — checked last, so a configured region never displaces a working provider |
| none | **503** with `"Embeddings unavailable"` |

`LLM_ROUTE_EMBEDDINGS` overrides that order (`bedrock` / `huggingface` / `openrouter`, default `auto`). Because Bedrock is checked last, **an explicit pin is the only way to select it while `HF_TOKEN` is set**.

Models: `BEDROCK_EMBEDDING_MODEL` (default `cohere.embed-english-v3`), `HF_EMBEDDING_MODEL` (default `sentence-transformers/all-MiniLM-L6-v2`), `OPENROUTER_EMBEDDING_MODEL` (default `openai/text-embedding-3-small`). Hugging Face embeddings use the Inference Providers **feature-extraction** pipeline (the OpenAI-compatible `…/v1` router is chat-only).

### Listing embeddings (pgvector)

`public.properties.embedding` is a **`vector(1024)`** column with an HNSW cosine index (migration `20260813_properties_embedding.sql`). Listings are embedded **once**, not per request.

⚠️ The width is fixed at 1024 for Cohere Embed v3, so **writing embeddings requires `LLM_ROUTE_EMBEDDINGS=bedrock`** — the 384-dim Hugging Face default cannot populate the column, and a mismatch fails loudly rather than corrupting it.

Populate and keep current:

```bash
python scripts/backfill_embeddings.py                 # drain the backlog
python scripts/backfill_embeddings.py --max-batches 2 # bounded run
```

It selects rows with no vector *or* one from a superseded model, so new listings and a model change are the same case. Each batch commits before the next is selected, so an interrupted run resumes. `.github/workflows/embed-listings.yml` runs it every 30 minutes; listings are written by the ingestion microservice, which has no LLM providers, so embedding is a pull schedule rather than part of the ingest path.

**Consumer:** `GET /api/v1/listings/{property_id}/similar` — reads the seed's **stored** vector (the backfill built it from the same text, so re-embedding would recompute an identical value on a public endpoint; only an unembedded or superseded seed falls back to an embedding call), then runs an indexed k-NN query scoped to the seed's state (widening once if that returns short), returning scores on the same 0–100 scale as search `match_score`. Results are sorted by score, so state decides which rows are eligible, not how they rank. Rows without an embedding are excluded, so run the backfill before relying on it.

⚠️ **Filtered HNSW can under-return.** With a `WHERE` clause, pgvector scans `hnsw.ef_search` index candidates and *then* filters, so a query can return fewer rows than match — which here shows up as the widening path triggering when it should not. If similar-listings looks short in a state with plenty of listings, raise `hnsw.ef_search` (default 40), or enable `hnsw.iterative_scan` on pgvector ≥ 0.8. Harmless at a small corpus; check it before assuming the data is wrong.

### Intake turns (`public.intake_jobs`)

A turn of the LLM intake chat is stored before it runs (migration
`20260814_intake_jobs.sql`), so a slow or failing provider costs latency rather than the
message the user typed.

⚠️ **Apply the migration before deploying the code.** The backend deploys from `main`
automatically, and `POST /answers/llm` writes to `intake_jobs` on every request — deploy
first and intake is down until the table exists. There is no migration runner; apply it
against the direct port (5432), since pgbouncer transaction mode blocks DDL.

The endpoint returns **`202 {job_id, status}`** rather than the turn itself. The client
then polls `GET /intake-sessions/{id}/jobs/{job_id}` until the job settles.

⚠️ **An SSE stream was built here and removed — do not re-add `EventSource`.** These
routes are on the protected router and need a bearer token; `EventSource` cannot set
headers, so every browser connection 401'd and fell through to polling silently. The API
tests override `get_current_user`, so they could not have caught it. Push delivery, if
ever wanted, needs `fetch` + `ReadableStream`.

**No queue is required to run.** With `SQS_CHAT_QUEUE_URL` empty — the default, and what
local dev and CI use — the turn runs inline and the job is already terminal when the
`202` returns. Setting the variable switches dispatch to `chat-intake.fifo` and the
[`chat-intake-worker`](../infra/chat-intake-worker/README.md) Lambda.

⚠️ **The response shape is the same either way; the resilience is not.** Inline, the
`202` comes back *after* the turn finishes, so the request spans the whole provider call.
If the platform kills it first, the row survives — the user's text is safe — but the
response never arrived, so the client never learned the `job_id` and cannot follow the
job. The row then holds the session's in-flight slot until the stale sweep, so a retry
meets "still working on your last message" for several minutes. Enable the queue in
production: it is what makes a stalled provider cost latency rather than a turn.

Two behaviours worth knowing when reading the code:

- **The claim is the idempotency gate.** The worker moves a job `queued → running` with
  the update filtered on `status = 'queued'`, so a redelivered SQS message whose job
  already ran matches no row and is dropped instead of paying for the turn twice.
- **A session allows one turn in flight** (`INTAKE_MAX_ACTIVE_JOBS_PER_SESSION`). A
  worker killed mid-turn would otherwise hold that slot forever, so the enqueue endpoint
  sweeps jobs stuck in `running` past `CHAT_JOB_STALE_AFTER_SECONDS` before counting.

Both LLM intake routes are anonymous and metered per address and per session
(`INTAKE_IP_RATE_LIMIT_PER_MINUTE`, `INTAKE_SESSION_RATE_LIMIT_PER_MINUTE`) — they are
the only unauthenticated paths that spend money per request.

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
2. Set **Production** env vars in Vercel from `.env.example` (`DATABASE_URL`, Supabase keys, `FRONTEND_ORIGIN`, and at least one of `OPENROUTER_API_KEY` or `HF_TOKEN` for chat, …).
3. Push to `main` — `.github/workflows/backend.yml` deploys with `VERCEL_BACKEND_PROJECT_ID`, or deploy locally with `vercel deploy --prod`.

Entrypoint for the serverless bundle: `api/index.py` → `app.main:app` (see `vercel.json`).

See the repo root [README](../README.md#deploy-backend-vercel) for GitHub secrets and wiring `NEXT_PUBLIC_BACKEND_API_URL` on the frontend.
