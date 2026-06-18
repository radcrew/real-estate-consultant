# Architecture

## Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Next.js 15 (App Router) | UI, server components, route handlers, OAuth |
| **Backend** | FastAPI + Python 3.12 | REST API, LLM orchestration, auth proxy |
| **Ingestion** | FastAPI microservice | Listing connectors, normalization, DB upsert |
| **Database** | Supabase (Postgres) | Auth, storage, RLS-protected data |
| **LLM** | Hugging Face Inference API | Intake parsing, outreach drafts |

---

## Request flow

```
Browser
  └─► Next.js (frontend)
        ├─► Supabase Auth        — sign-in / session
        ├─► FastAPI (backend)    — /api/v1/* (search, intake, outreach, account)
        │     ├─► Supabase DB    — listings, sessions, profiles
        │     └─► HF Inference   — LLM calls (intake parse, outreach draft)
        └─► Supabase Storage     — listing images, avatars
```

The ingestion service runs independently (triggered by CI or the backend):

```
GitHub Actions / Backend
  └─► Ingestion service  — /api/v1/jobs/process
        ├─► Local JSON dataset (LoopNet seed connector)
        └─► Supabase DB  — upsert properties + images
```

---

## Backend module map

```
backend/app/
├── api/v1/endpoints/
│   ├── auth/           — sign-in, sign-up, password reset
│   ├── account/        — profile, password, avatar, saved listings
│   ├── agents.py       — broker agent lookup
│   ├── intake_sessions/— guided + LLM intake session lifecycle
│   ├── search/         — criteria-based listing search
│   ├── outreach/       — LLM broker outreach draft
│   ├── listings/       — listing detail
│   ├── submissions.py  — user listing submissions
│   └── admin/          — admin submission management
├── llm/
│   ├── intake/         — intake parsing schema + service
│   └── outreach/       — outreach draft schema + service
├── repositories/       — Supabase data access layer
├── schemas/            — Pydantic request/response models
├── core/               — config, database, deps, middleware
└── utils/              — shared helpers
```

---

## Key design decisions

- **No DB in the backend for writes** — all persistence goes through Supabase (PostgREST or the Python SDK). SQLAlchemy is used for read-only search queries only.
- **LLM calls are synchronous per request** — no job queue; each intake/outreach call blocks until the HF API responds.
- **Ingestion is a separate service** — keeps the main API stateless and avoids long-running jobs blocking FastAPI workers.
- **Auth is Supabase-native** — JWTs issued by Supabase Auth; the backend validates them, never issues its own.
