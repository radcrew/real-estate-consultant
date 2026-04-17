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
| `IS_DEV_MODE` | When `true`, enables `/docs` and `/redoc` and other dev-only routes; `DEBUG` is accepted as an alias |

Environment values are loaded from `backend/.env` by path, so loading does not depend on the shell’s current working directory.

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
