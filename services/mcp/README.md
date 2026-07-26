# MCP adapter for the radestate commercial real-estate platform.

Phase 2: intake + draft-only outreach tools, plus resources/prompts. Domain
logic stays in `backend/`. See repo root `MCP_SERVER_PLAN.md`.

## Requirements

- Python 3.11+
- Backend at `BACKEND_API_URL` (default `http://127.0.0.1:8888`)
- Supabase **user** JWT in `MCP_USER_ACCESS_TOKEN` (never the service role key)

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
copy .env.example .env
```

## Run (stdio)

```powershell
python -m app.main
# or: radestate-mcp
```

Logging → **stderr** only.

## Cursor host config

```json
{
  "mcpServers": {
    "radestate": {
      "command": "D:/work/real-estate-consultant/services/mcp/.venv/Scripts/python.exe",
      "args": ["-m", "app.main"],
      "cwd": "D:/work/real-estate-consultant/services/mcp",
      "env": {
        "BACKEND_API_URL": "http://127.0.0.1:8888",
        "MCP_USER_ACCESS_TOKEN": "<supabase-access-token>"
      }
    }
  }
}
```

## Tools

| Tool | Side effects | Auth |
|------|--------------|------|
| `ping_backend` | None | No |
| `search_properties` | None (read) | Yes |
| `update_search_criteria` | **WRITE** replaces criteria | Yes |
| `get_listing` / `get_featured_listings` | None | No |
| `explain_fit` | LLM call, not persisted | Yes |
| `list_saved_listings` / `get_agent` | None | Yes |
| `start_intake_session` | **WRITE** creates session | Yes |
| `answer_intake` | **WRITE** mutates criteria | Yes |
| `complete_intake` | **WRITE** creates search profile | Yes |
| `get_intake_session` | None | Yes |
| `generate_outreach_draft` | **WRITE** draft only (never sends) | Yes |
| `get_outreach_draft` | None | Yes |
| `update_outreach_draft` | **WRITE** edits draft text only | Yes |

## Resources

- `listing://{property_id}`
- `search://{session_profile_id}`
- `intake://{session_id}`

## Prompts

- `cre_property_search` — intake → search → explain fits
- `draft_broker_outreach` — draft-only email workflow

## Tests

```powershell
pytest
```
