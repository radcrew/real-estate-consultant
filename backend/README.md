# Backend

FastAPI service for the real estate consultant MVP: APIs, ingestion orchestration, and related server-side work. The installable Python package lives under `app/` (ASGI entry: `app.main:app`).

## Requirements

- Python 3.11 or newer

## Setup

From this directory (`backend/`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

On macOS or Linux, use `source .venv/bin/activate` instead of the PowerShell activation line.

## Configuration

Copy `.env.example` to `.env` in this same directory and adjust values as needed.

| Variable   | Purpose |
|------------|---------|
| `APP_NAME` | Title shown in the OpenAPI metadata |
| `IS_DEV_MODE` | When `true`, enables `/docs` and `/redoc`, the **`POST /seed`** route, and other dev-only behavior; `DEBUG` is accepted as an alias |

Environment values are loaded from `backend/.env` by path, so loading does not depend on the shell’s current working directory.

## Dataset

The dev seed pipeline reads **`backend/dataset/raw-data.json`**. That file should be a **JSON array of objects** (LoopNet-style listing records). The parser maps each object into a row for Supabase **`public.properties`**.

### Dataset preparation

Follow these steps **before** calling **`POST /seed`**:

1. **Scrape LoopNet** using **[Apify](https://apify.com/)**. In the Apify Store, search for **LoopNet** (or “loop”) scrapers **Actors**, pick one that fits your needs, configure the run, and start it.
2. **Trial limit:** On a **free trial**, Apify typically returns only about **50 results** per run. Paid runs can return more, depending on the Actor and your plan.
3. **Export:** When the run finishes, download or export the dataset as **JSON**. Apify may name the file something like **`raw_dataset.json`** (or another default); that is fine as an export artifact.
4. **Place the file for this backend:** Copy or rename the export so it exists exactly as **`backend/dataset/raw-data.json`** (create the **`dataset/`** folder under `backend/` if it is missing). The application code looks for that path by default—**not** `raw_dataset.json` unless you change the code in `app/seed/parse.py`.
5. **Validate shape:** The file’s root must be a **JSON array** (`[ ... ]`), and each element must be a **JSON object** (`{ ... }`). If the export is wrapped differently (e.g. one object with a `"data"` array), reshape or re-export so the root is the array of listings.

If the file is missing, not found at that path, or fails those checks, **`POST /seed`** responds with **400** or **422** and a short error message.

## Seeding (`POST /seed`)

After **dataset preparation** and with Supabase configured (see troubleshooting below):

1. Set **`IS_DEV_MODE=true`** in `.env` and **restart** the API. The **`/seed`** route is **not registered** when dev mode is off—you will get **404** on `POST /seed`.
2. Start the server (see **Run the server**).
3. Send a **`POST`** request to **`http://127.0.0.1:8000/seed`** (no body required for the default dataset path).

Examples (Windows, server on default port):

```powershell
curl.exe -X POST http://127.0.0.1:8000/seed
```

```powershell
Invoke-WebRequest -Method POST -Uri http://127.0.0.1:8000/seed
```

Each successful call **INSERT**s rows; repeated calls **append**. For a clean re-seed in dev, run **`truncate table public.properties;`** in the Supabase SQL editor (or `psql`) before calling **`POST /seed`** again.

## Run the server

With the virtual environment activated.

**Working directory must be `backend/`** (where this `pyproject.toml` lives). If you run `fastapi dev` from the repository root, the CLI shows *Could not find a default file to run* because it does not see `[tool.fastapi]` or the `app` package.

From `backend/`:

**Development** (reload on `127.0.0.1:8000`, uses `[tool.fastapi]` entrypoint in `pyproject.toml`):

```powershell
fastapi dev
```

From the **repository root** (path to `main.py` so the CLI can resolve `app` under `backend/`):

```powershell
fastapi dev backend/app/main.py
```

**Production-style** (no reload, listens on `0.0.0.0`):

```powershell
fastapi run
```

Equivalent with Uvicorn directly:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Useful URLs (default port)

| URL | Description |
|-----|-------------|
| [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Liveness-style check |
| `POST` [http://127.0.0.1:8000/seed](http://127.0.0.1:8000/seed) | Dev dataset seed (only when `IS_DEV_MODE=true`) |
| [http://127.0.0.1:8000/api/v1/ping](http://127.0.0.1:8000/api/v1/ping) | Sample versioned route |
| [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json) | OpenAPI schema |

### `POST /seed` troubleshooting

If seeding fails after [Dataset preparation](#dataset-preparation) and [Seeding](#seeding-post-seed):

- The route exists only when **`IS_DEV_MODE=true`** (restart the server after changing `.env`). Otherwise you get **404**.
- Call **`POST`**, not GET (opening the URL in a browser alone will not seed).
- **`SUPABASE_URL`** and **`SUPABASE_SERVICE_ROLE_KEY`** must be valid; bad URL or DNS issues return **502** with a short explanation (including `httpx` connection errors, which are not PostgREST `APIError`s).
- Apply the SQL migrations under `supabase/migrations/` so **`public.properties`** exists with the columns in `app/models/properties.py`. If you had an older `source_property_id` column, run **`20260418120000_properties_drop_source_property_id.sql`** then **`NOTIFY pgrst, 'reload schema';`** ([docs](https://supabase.com/docs/guides/troubleshooting/refresh-postgrest-schema)). PostgREST **`PGRST204`** usually means the schema cache is stale after DDL—run the same `NOTIFY`, then retry **`POST /seed`**.
- **`POST /seed`** uses **INSERT** (each run adds rows). For a clean re-seed in dev, run **`truncate table public.properties;`** (or delete rows) before calling the endpoint again.

## Linting

With dev dependencies installed:

```powershell
ruff check app
```
