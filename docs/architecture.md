# Architecture

C4-style overview of the real-estate consultant system — current state, including
the microservice split done in Phase 3 of the skills roadmap.

---

## 1. Context (C4 Level 1)

Who and what interacts with the system.

```mermaid
C4Context
  title System context

  Person(admin, "Admin user", "Single internal user running searches,\nreviewing listings, drafting outreach")

  System(app, "Real-estate consultant", "AI-assisted CRE search: intake,\nproperty search, outreach drafting")

  System_Ext(supabase, "Supabase", "Postgres, Auth, Storage,\nRealtime")
  System_Ext(hf, "Hugging Face router", "OpenAI-compatible LLM API\n(intake parsing + outreach drafts)")
  System_Ext(apify, "Apify / scrapers", "Lawful listing acquisition\n(dataset source for seed pipeline)")
  System_Ext(vercel, "Vercel", "Serverless hosting for\nfrontend and backend")

  Rel(admin, app, "Uses", "HTTPS")
  Rel(app, supabase, "Reads/writes", "PostgREST + Auth SDK")
  Rel(app, hf, "LLM calls", "HTTPS / OpenAI-compat API")
  Rel(apify, app, "Supplies raw listings", "JSON export → seed pipeline")
  Rel(app, vercel, "Deployed on")
```

---

## 2. Containers (C4 Level 2)

Deployed units and their relationships.

### Before Phase 3 (monolith)

```mermaid
C4Container
  title Container diagram — before Phase 3 (monolith)

  Person(admin, "Admin user")

  Container(fe, "Next.js frontend", "Next.js / React", "Intake UI, search results,\nproperty detail, outreach editor")
  Container(be, "FastAPI backend", "Python / FastAPI\nVercel serverless", "REST API, LLM orchestration,\nseed pipeline, structured logging")
  ContainerDb(pg, "Postgres", "Supabase managed Postgres", "Properties, intake sessions,\nsearch profiles, outreach drafts,\nuser profiles, saved listings")
  Container(auth, "Supabase Auth", "Supabase", "JWT issuance and validation\n(email/password, admin gate)")
  System_Ext(hf, "Hugging Face router", "LLM completions")

  Rel(admin, fe, "Uses", "HTTPS")
  Rel(fe, be, "API calls", "HTTPS / JSON\nAuthorization: Bearer <jwt>")
  Rel(be, pg, "Queries", "asyncpg / SQLAlchemy\n(pgbouncer in prod)")
  Rel(be, auth, "Validates tokens\nManages users", "Supabase Auth SDK")
  Rel(be, hf, "Structured completions", "HTTPS")
  Rel(fe, auth, "Signs in/up\ngets JWT", "Supabase JS SDK")
```

### Current (Phase 3): ingestion service extracted

```mermaid
C4Container
  title Container diagram — current (ingestion service extracted)

  Person(admin, "Admin user")

  Container(fe, "Next.js frontend", "Next.js / React", "Intake UI, search results,\nrealtime ingestion progress")
  Container(be, "FastAPI backend", "Python / FastAPI", "REST API, LLM orchestration,\njob enqueue")
  Container(ingest, "Ingestion service", "Python / FastAPI", "Listing acquisition,\nnormalization, connector plugins")
  ContainerDb(pg, "Postgres (Supabase)", "", "Shared system of record;\n+ jobs table for queue")
  Container(auth, "Supabase Auth", "Supabase", "JWT issuance / validation")
  System_Ext(hf, "Hugging Face router", "LLM completions")
  System_Ext(sources, "Listing sources", "Apify / public pages")

  Rel(admin, fe, "Uses", "HTTPS")
  Rel(fe, be, "API calls", "HTTPS / Bearer JWT")
  Rel(be, ingest, "Enqueues jobs\nWakes processor", "HTTP + shared bearer token\n(typed client)")
  Rel(ingest, pg, "Claims jobs (SKIP LOCKED)\nWrites normalized listings\nUpdates job status", "asyncpg / PostgREST")
  Rel(be, pg, "Reads/writes", "asyncpg")
  Rel(be, auth, "Token validation", "Supabase Auth SDK")
  Rel(be, hf, "LLM calls", "HTTPS")
  Rel(ingest, sources, "Fetches listings\n(rate-limited, future connectors)", "HTTPS")
  Rel(fe, pg, "Realtime progress", "Supabase Realtime WS")
```

---

## 3. Key data models

```mermaid
erDiagram
  properties {
    uuid id PK
    text address
    text city
    text state
    text property_type
    text listing_type
    numeric price
    numeric rent
    numeric size_sqft
    numeric clear_height
    int loading_docks
    text description
  }
  property_images {
    uuid id PK
    uuid property_id FK
    text url
  }
  intake_sessions {
    uuid id PK
    uuid search_profile_id FK
    jsonb criteria
    text status
    timestamptz created_at
  }
  search_profiles {
    uuid id PK
    text user_id
    timestamptz created_at
  }
  outreach_drafts {
    uuid id PK
    text user_id
    uuid property_id FK
    text draft_email
    timestamptz created_at
  }
  profiles {
    uuid id PK
    text user_id
    text full_name
    text avatar_url
    bool is_admin
  }
  saved_listings {
    uuid id PK
    text user_id
    uuid property_id FK
  }

  properties ||--o{ property_images : "has"
  properties ||--o{ outreach_drafts : "drafted for"
  properties ||--o{ saved_listings : "saved as"
  search_profiles ||--o{ intake_sessions : "linked to"
```

---

## 4. Request flows

### 4a. Intake flow (qualification chatbot)

```mermaid
sequenceDiagram
  actor U as Admin user
  participant FE as Next.js
  participant BE as FastAPI
  participant DB as Supabase (Auth + Postgres)
  participant LLM as Hugging Face

  U->>FE: Opens intake page
  FE->>BE: POST /api/v1/intake-sessions
  BE->>DB: Create intake_session row
  BE->>LLM: generate_opening_question()
  LLM-->>BE: Opening question text
  BE-->>FE: {session_id, first_question}
  FE-->>U: Renders first question

  loop Until all required criteria collected
    U->>FE: Types answer
    FE->>BE: POST /intake-sessions/{id}/answers/llm
    BE->>DB: Load current criteria
    BE->>LLM: parse_user_input(answer, criteria, questions)
    LLM-->>BE: {extracted, missing_fields, next_question}
    BE->>DB: Save merged criteria
    BE-->>FE: {next_question, is_complete}
    FE-->>U: Renders next question
  end

  U->>FE: Submits intake
  FE->>BE: POST /api/v1/search/quick
  BE->>DB: Create search_profile linked to session
  BE-->>FE: {search_profile_id}
  FE-->>U: Redirects to search results
```

### 4b. Search flow

```mermaid
sequenceDiagram
  actor U as Admin user
  participant FE as Next.js
  participant BE as FastAPI
  participant DB as Supabase (Postgres)

  U->>FE: Views search results page
  FE->>BE: GET /api/v1/search/{search_profile_id}
  BE->>DB: Validate search profile ownership
  BE->>DB: Load intake session criteria (JSONB)
  BE->>DB: SQL search on properties\n(criteria filters + scoring)
  DB-->>BE: Ranked property rows
  loop Per property (first image)
    BE->>DB: fetch_first_image_url (Supabase SDK)
  end
  BE-->>FE: {results[], total, criteria}
  FE-->>U: Renders ranked listing cards
```

### 4c. Outreach flow

```mermaid
sequenceDiagram
  actor U as Admin user
  participant FE as Next.js
  participant BE as FastAPI
  participant DB as Supabase
  participant LLM as Hugging Face

  U->>FE: Clicks "Draft outreach" on a listing
  FE->>BE: POST /api/v1/outreach/drafts\n{property_id}
  BE->>DB: Fetch property row
  BE->>DB: Fetch user profile (name, email)
  BE->>LLM: generate_broker_outreach_draft\n(property, profile)
  LLM-->>BE: Draft email text
  BE->>DB: insert_outreach_draft
  BE-->>FE: {draft_id, draft_email}
  FE-->>U: Renders editable draft

  U->>FE: Edits draft text
  FE->>BE: PATCH /api/v1/outreach/drafts/{id}
  BE->>DB: update_outreach_draft_email
  BE-->>FE: Updated draft
```

---

## 5. Logging pipeline (Phase 1)

Every backend request produces structured JSON log events that flow through
a normalisation layer before landing in Vercel's log store.

```mermaid
flowchart LR
  subgraph FastAPI process
    MW[RequestLoggingMiddleware\nstamps request_id + timing]
    APP[Route handlers\nrepositories · LLM services]
    EH[Exception handlers\nHTTPException · unhandled]
    CV[contextvars\nrequest_id · user_id]
  end
  subgraph Logging pipeline
    FMT[_JsonFormatter\nstructured JSON]
    SCR[_scrub\nredact PII + secrets]
    FIL[_DropNoisyRequestsFilter\ndrop /health at INFO]
  end
  VERCEL[Vercel log store\nstdout capture + search]

  MW -->|sets| CV
  APP -->|logging.getLogger| FMT
  EH -->|logging.error/warning| FMT
  CV -->|injected into every record| FMT
  FMT --> SCR --> FIL --> VERCEL
```

**Normalised event schema** (every log line):

| Field | Source |
|-------|--------|
| `timestamp` | `_JsonFormatter.formatTime` |
| `level` | log level name |
| `logger` | `logging.getLogger(__name__)` |
| `message` | log message |
| `request_id` | `RequestLoggingMiddleware` via `contextvars` |
| `user_id` | auth dependency via `contextvars` (when authed) |
| `method`, `path`, `status`, `duration_ms` | `request_completed` / `request_slow` events |
| `provider`, `model`, `outcome`, `duration_ms`, `*_tokens`, `estimated_cost_usd` | `llm_call` events |
| `source`, `fetched`, `normalized`, `rejected`, `rejected_reasons` | `ingestion_run` events |

---

## 6. Job queue and live progress (Phase 3.3–3.5)

Vercel functions have a 10–60 s hard kill; a connector run that fetches and
LLM-extracts dozens of listings cannot fit in one request. A `jobs` table
in Supabase decouples enqueue (backend, fast) from processing (ingestion
service, long-running).

```mermaid
flowchart TD
  A[Admin triggers ingestion\nPOST /api/v1/admin/ingest] --> B[Backend enqueues job\nINSERT INTO jobs]
  B --> C[Returns {job_id} immediately]
  B --> W[Backend calls ingestion\nPOST /api/v1/jobs/process\nvia typed client - best effort]
  C --> D[Frontend subscribes\nSupabase Realtime on jobs row\nadmin-only RLS policy]

  W --> F{claim_next_job\nFOR UPDATE SKIP LOCKED}
  E[Vercel cron, every 15 min\nfallback if the wake call fails] --> F
  F -->|status = pending -> running| D
  F --> G[Run connector\ne.g. loopnet-seed]
  G --> H[Normalize listings]
  H --> I[Upsert into properties\n+ property_images]
  I --> J[UPDATE jobs\nstatus = done/failed, result jsonb]
  J --> D
```

**`jobs` table schema:**

| Column | Type | Purpose |
|--------|------|---------|
| `id` | `uuid` PK | Job identifier returned to frontend |
| `source` | `text` | Connector name (e.g. `loopnet-seed`) |
| `status` | `text` | `pending` → `running` → `done` / `failed` |
| `attempts` | `int` | Retry counter (max 3, then `failed`) |
| `idempotency_key` | `text` | One active job per source per day |
| `result` | `jsonb` | `{fetched, normalized, rejected, rejected_reasons, duration_ms}` on success |
| `error` | `text` | Error message on failure |
| `created_at` / `updated_at` | `timestamptz` | Enqueue / last-transition time |

**Realtime (3.5):** `public.jobs` has RLS enabled with an admin-only `SELECT`
policy (`profiles.is_admin = true`) and is added to the `supabase_realtime`
publication with `REPLICA IDENTITY FULL`. The frontend's `/admin/ingest` page
subscribes to `postgres_changes` (`UPDATE`, filtered to the triggered job's
`id`) using the browser Supabase client + user JWT — no polling.

---

## 7. Service boundaries rationale

| Split | Why here |
|-------|----------|
| Frontend ↔ Backend | Different languages (TS/Python), deploy cadences, and team concerns; Next.js BFF pattern naturally owns the UI shell |
| Backend ↔ Ingestion service | Ingestion is long-running (exceeds serverless timeout), independently deployable, and failure-isolated from the user-facing API — a connector bug cannot crash the auth or search flows |
| Shared Postgres as integration point | Avoids distributed transactions; Supabase Realtime gives the frontend live job updates without a separate message bus |
| Backend ↔ Ingestion contract (3.6) | The backend's `app/clients/ingestion` Pydantic models are generated from the ingestion service's OpenAPI schema (`scripts/generate_ingestion_client.py`); CI regenerates and diffs them, so a breaking response-shape change fails the build instead of surfacing as a runtime error in `wake_processor()` |
| Connector plugins ↔ shared infrastructure (3.7) | Each source is a `ConnectorBase` subclass registered by name (e.g. `loopnet-seed`); the job queue, retry/backoff, and `RateLimitedFetcher` (semaphore + token bucket) are shared, so adding a new source means writing one connector, not a new service |

### Modular connectors

The ingestion service's `_CONNECTORS` registry (in `app/api/ingest.py` and
`app/api/jobs.py`) maps a job's `source` string to a `ConnectorBase`
subclass. `claim_next_job()` doesn't know or care which connector runs —
it just records `source`, `status`, `attempts`, and `result`. Today's only
connector (`LoopNetSeedConnector`) reads a local dataset; a future
HTTP-fetching connector (e.g. live LoopNet pages, a second source) drops in
alongside it and reuses:

- the same job queue, idempotency key, and retry/backoff (3.3)
- the same service-to-service auth (3.4)
- the same Realtime progress reporting (3.5)
- `RateLimitedFetcher` for a per-source concurrency cap + polite request rate (3.7)

This is the "modular connectors" principle from the spec: new lawful
ingestion sources are additive, not architectural changes.

See `docs/slo.md` for availability targets and `docs/runbook.md` for incident response.
