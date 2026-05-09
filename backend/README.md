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
fastapi dev
```

This uses `[tool.fastapi]` in `pyproject.toml` (`entrypoint = "app.main:app"`), serves with reload on **http://127.0.0.1:8000** by default.

**If your shell is at the repository root** (parent of `backend/`), point the CLI at `main.py` so imports resolve:

```powershell
fastapi dev backend/app/main.py
```

**Production-style** (no reload, binds `0.0.0.0` by default for `fastapi run`):

```powershell
fastapi run
```

**Uvicorn directly** (same app, reload on localhost):

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Running `fastapi dev` from the repo root **without** the `backend/app/main.py` path often fails with *Could not find a default file to run* because the CLI does not see `[tool.fastapi]` or the `app` package.

### Useful URLs (default port)

| URL | Description |
|-----|-------------|
| [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Liveness-style check |
| [http://127.0.0.1:8000/api/v1/ping](http://127.0.0.1:8000/api/v1/ping) | Sample versioned route |
| [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json) | OpenAPI schema |

## Configuration

Copy `.env.example` to `.env` in this same directory and adjust values as needed.

| Variable   | Purpose |
|------------|---------|
| `APP_NAME` | Title shown in the OpenAPI metadata |
| `IS_DEV_MODE` | Reserved for future dev-only toggles; `DEBUG` is accepted as an alias (not used by routes today) |

Environment values are loaded from `backend/.env` by path, so loading does not depend on the shell’s current working directory.

## Dataset

The dev seed pipeline reads **`backend/dataset/raw-data.json`**. That file should be a **JSON array of objects** (LoopNet-style listing records). The parser maps each object into a row for Supabase **`public.properties`**.

### Dataset preparation

Follow these steps **before** running **`python -m app.seed.main`**:

1. **Scrape LoopNet** using **[Apify](https://apify.com/)**. In the Apify Store, search for **LoopNet** (or “loop”) scrapers **Actors**, pick one that fits your needs, configure the run, and start it.
2. **Trial limit:** On a **free trial**, Apify typically returns only about **50 results** per run. Paid runs can return more, depending on the Actor and your plan.
3. **Export:** When the run finishes, download or export the dataset as **JSON**. Apify may name the file something like **`raw_dataset.json`** (or another default); that is fine as an export artifact.
4. **Place the file for this backend:** Copy or rename the export so it exists exactly as **`backend/dataset/raw-data.json`** (create the **`dataset/`** folder under `backend/` if it is missing). The application code looks for that path by default—**not** `raw_dataset.json` unless you change the code in `app/seed/parse.py`.
5. **Validate shape:** The file’s root must be a **JSON array** (`[ ... ]`), and each element must be a **JSON object** (`{ ... }`). If the export is wrapped differently (e.g. one object with a `"data"` array), reshape or re-export so the root is the array of listings.

If the file is missing, not found at that path, or fails those checks, **`python -m app.seed.main`** exits with an error and logs the reason.

## Seeding

After **dataset preparation** and with **`SUPABASE_URL`** / **`SUPABASE_SERVICE_ROLE_KEY`** set in `.env`:

From **`backend/`** (virtual environment activated):

```powershell
python -m app.seed.main
```

Each successful run **upserts** properties and replaces **`property_images`** for the seeded property ids. For a clean re-seed in dev, run **`truncate table public.properties;`** (and clear related image rows if needed) in the Supabase SQL editor (or `psql`) before running **`python -m app.seed.main`** again.

## Seeding troubleshooting

If seeding fails after [Dataset preparation](#dataset-preparation) and [Seeding](#seeding):

- Run the command from **`backend/`** so `app` imports resolve (same as the server).
- **`SUPABASE_URL`** and **`SUPABASE_SERVICE_ROLE_KEY`** must be valid; connection problems are logged with an `httpx` explanation.
- Ensure **`public.properties`** (and any related tables your seed uses) exist and match the columns expected in `app/models/properties.py` and the seed code. Apply schema in the Supabase SQL editor or whatever migration workflow your team uses. After DDL, run **`NOTIFY pgrst, 'reload schema';`** if PostgREST still serves a stale schema ([docs](https://supabase.com/docs/guides/troubleshooting/refresh-postgrest-schema)). PostgREST **`PGRST204`** usually means the schema cache is stale after DDL—run the same `NOTIFY`, then retry **`python -m app.seed.main`**.
- Property rows use **upsert** on **`id`**; images for those ids are deleted then re-inserted. For a full reset in dev, truncate or delete rows as needed, then run **`python -m app.seed.main`** again.

## Linting

With dev dependencies installed:

```powershell
ruff check app
```
