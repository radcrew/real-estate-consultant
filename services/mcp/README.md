# MCP adapter for the radestate commercial real-estate platform.

Phase 0 skeleton: stdio transport + one tool (`ping_backend`) that calls
`GET /api/v1/ping` on the FastAPI backend. Domain logic stays in `backend/`.

See repo root `MCP_SERVER_PLAN.md` for the full roadmap.

## Requirements

- Python 3.11+
- Backend reachable at `BACKEND_API_URL` (default `http://127.0.0.1:8888`)

## Setup

From this directory (`services/mcp/`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
copy .env.example .env
```

On macOS/Linux: `source .venv/bin/activate`, then the same `python -m pip` lines.

## Run (stdio)

With the venv activated and cwd still `services/mcp/`:

```powershell
python -m app.main
```

Or via the console script after editable install:

```powershell
radestate-mcp
```

The process speaks MCP over stdin/stdout. **Do not** `print()` to stdout — logging
goes to stderr only.

## Smoke test with MCP Inspector

With deps installed (`mcp[cli]`):

```powershell
mcp dev app/main.py
```

In the Inspector UI, list tools and call `ping_backend`. Expect a JSON payload
like `{"message": "pong"}` when the backend is up.

## Cursor host config

Project or user MCP settings example:

```json
{
  "mcpServers": {
    "radestate": {
      "command": "python",
      "args": ["-m", "app.main"],
      "cwd": "D:/work/real-estate-consultant/services/mcp",
      "env": {
        "BACKEND_API_URL": "http://127.0.0.1:8888"
      }
    }
  }
}
```

Prefer pointing `command` at this package’s `.venv` Python so Cursor uses the
editable install:

```json
{
  "mcpServers": {
    "radestate": {
      "command": "D:/work/real-estate-consultant/services/mcp/.venv/Scripts/python.exe",
      "args": ["-m", "app.main"],
      "cwd": "D:/work/real-estate-consultant/services/mcp",
      "env": {
        "BACKEND_API_URL": "http://127.0.0.1:8888"
      }
    }
  }
}
```

## Tools (Phase 0)

| Tool | Backend | Auth |
|------|---------|------|
| `ping_backend` | `GET /api/v1/ping` | None |

## Tests

```powershell
pytest
```
