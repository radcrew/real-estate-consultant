# Development Setup

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.12+ | [python.org](https://python.org) |
| Node.js | 20+ | [nodejs.org](https://nodejs.org) |
| pnpm | 10+ | `npm i -g pnpm` |
| Supabase CLI | latest | [supabase.com/docs/guides/cli](https://supabase.com/docs/guides/cli) |

---

## 1. Clone and install root deps

```bash
git clone https://github.com/radcrew/real-estate-consultant.git
cd real-estate-consultant
pnpm install
```

---

## 2. Backend (FastAPI)

```bash
cd backend
cp .env.example .env          # fill in values (see below)
python -m pip install -e ".[dev]"
fastapi dev                   # runs on http://localhost:8000
```

**Required `.env` values:**

| Variable | Description |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` Supabase connection string |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (from Supabase dashboard) |
| `SUPABASE_ANON_KEY` | Anon key |
| `HF_TOKEN` | Hugging Face API token (for LLM calls) |

API docs available at `http://localhost:8000/docs`.

---

## 3. Frontend (Next.js)

```bash
cd frontend
cp .env.example .env.local    # fill in values
pnpm dev                      # runs on http://localhost:3000
```

**Required `.env.local` values:**

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_BACKEND_API_URL` | `http://localhost:8000` for local dev |
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Anon key |

---

## 4. Ingestion service

```bash
cd services/ingestion
cp .env.example .env          # fill in values
python -m pip install -e ".[dev]"
fastapi dev                   # runs on http://localhost:8001
```

**Required `.env` values:**

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key |
| `TRIGGER_TOKEN` | Shared secret for GitHub Actions trigger |
| `SERVICE_AUTH_TOKEN` | Shared secret the backend sends to call this service |

Trigger a job manually:

```bash
curl -X POST http://localhost:8001/api/v1/jobs/process \
  -H "Authorization: Bearer <TRIGGER_TOKEN>"
```

---

## Supabase local dev (optional)

```bash
supabase start                # starts local Postgres + Auth + Studio
supabase db reset             # applies migrations
```

Use the local URLs printed by `supabase start` in your `.env` files.
