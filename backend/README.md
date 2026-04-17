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
| `DEBUG`    | When `true`, enables `/docs` and `/redoc`; when `false`, they are hidden |

Environment values are loaded from `backend/.env` by path, so loading does not depend on the shell’s current working directory.

## Run the server

With the virtual environment activated and the working directory set to `backend/`:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Useful URLs (default port)

| URL | Description |
|-----|-------------|
| [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Liveness-style check |
| [http://127.0.0.1:8000/api/v1/ping](http://127.0.0.1:8000/api/v1/ping) | Sample versioned route |
| [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json) | OpenAPI schema |

## Linting

With dev dependencies installed:

```powershell
ruff check app
```
