# Skills Roadmap — Applying the Job Description to This Project

Mapping of the **Full-Stack Software Engineer / SRE** job description
(`job_description.txt`) onto this codebase: what we already demonstrate, what we
can add, and in what order.

---

## 1. Skill-by-skill assessment

| JD skill | Status in this project | Action |
|----------|------------------------|--------|
| Full-Stack (MERN) | ✅ Equivalent stack: React/Next.js + FastAPI + Postgres (Supabase). MongoDB/Express not a fit. | Document the analogy; no forced change |
| Python or Go | ✅ FastAPI backend in Python | Optionally add one small Go utility service (Phase 5) |
| System Design | 🟡 Good docs (`spec.md`), but no architecture diagram | Add C4-style architecture doc + diagrams |
| Microservices | ❌ Single FastAPI monolith | Extract ingestion into a separate worker service |
| Architect / Cloud Architect | 🟡 Two Vercel projects, serverless notes | Add deployment-architecture doc, Docker for portability |
| SRE experience | ❌ Only a bare `/health` endpoint | Health checks, SLOs, runbooks, post-deploy smoke tests, alerting |
| Deployment experience | ✅ GitHub Actions → Vercel (FE + BE) | Strengthen: smoke tests, staged deploys |
| Log Ingestion | ❌ No structured logging or pipeline | Structured JSON logs → normalization → ship to a log sink |
| Linux CLI / Bash | ❌ Only `setup.mjs` | Bash ops scripts under `scripts/ops/` |
| SecOps automation (nice) | ❌ None | CI security scanning, rate limiting, audit logging |
| EDR/cloud/SaaS telemetry | ❌ None | OpenTelemetry traces + request telemetry |

---

## 2. Phased plan

Phases are ordered by impact-per-effort and by how directly they map to the JD.
Each step is small enough for its own commit.

### Phase 1 — Structured logging & log pipeline (JD: Log Ingestion, Data normalization)

The single most JD-relevant gap. Goal: every backend request produces a
normalized, structured log event that flows through a pipeline.

1. **Structured JSON logging** in FastAPI
   - `backend/app/core/logging.py`: configure `structlog` (or stdlib + JSON formatter).
   - Normalized event schema: `timestamp`, `level`, `request_id`, `method`,
     `path`, `status`, `duration_ms`, `user_id` (when authed), `error`.
2. **Request logging middleware with context propagation**
   - Middleware in `backend/app/main.py` that stamps a `request_id`
     (honor inbound `X-Request-ID`), times the request, and emits one event per request.
   - Put `request_id` / `user_id` in `contextvars` so events emitted deep in
     repositories and LLM services automatically carry them — "show me
     everything in this failed request" becomes a single log filter.
     Extends across the ingestion service boundary in Phase 3 via `X-Request-ID`.
   - Warn-level event when `duration_ms` exceeds a threshold (e.g. 3 s) so
     latency regressions are searchable.
3. **Log filtering / scrubbing**
   - Drop noisy paths (`/health`), redact secrets/PII (emails, tokens) before emit —
     demonstrates "Data Filtering" from the JD.
4. **Global exception handler with structured error events**
   - One FastAPI exception handler that logs error class, route, and
     `request_id` in the standard schema — no error escapes as an
     unstructured traceback. Unifies the per-module `exceptions.py` modules.
5. **LLM call telemetry**
   - One event per OpenRouter/HuggingFace call in `app/llm/providers/`:
     model, latency, token usage, estimated cost, outcome
     (success / timeout / parse failure).
   - LLM calls are the slowest, flakiest, and only metered-cost part of the
     app; this gives per-feature cost attribution (intake vs. outreach).
6. **Ingestion-run reports**
   - One summary event per seed/connector run (`app/seed`, future connectors):
     source, items fetched, normalized, rejected (with reasons), duration —
     the JD's "log ingestion + data normalization" applied to the app's own
     domain; catches silently broken connectors.
7. ~~**Ship to a log sink**~~ — **omitted**: Vercel already captures stdout/stderr
   with search; once logs are structured JSON that is sufficient for an internal
   MVP. Revisit only if the app outgrows Vercel's log retention.
8. ~~**Frontend error reporting (Sentry)**~~ — **deferred**: structured backend
   logs cover the single-admin MVP; add Sentry when there are real users.

Skipped as not significant here: full OpenTelemetry tracing (needs a trace
backend; request-ID propagation covers one-to-two services), log
sampling/rate-limiting (single-user traffic), SIEM/ELK stacks.

### Phase 2 — SRE foundations (JD: SRE experience, Deployment)

1. **Timeouts + retries on external dependencies**
   - Explicit timeouts and bounded retry/backoff on LLM provider calls
     (`app/llm/providers/`) and DB/Supabase calls; fail with a clean error
     response instead of hanging until Vercel's hard kill.
   - The most real reliability gap in the app today.
2. **Richer, version-stamped health endpoints**
   - `/health/live` (process up) and `/health/ready` (DB + Supabase reachable),
     extending the existing `backend/app/api/system.py`.
   - Include git SHA + deploy time (`VERCEL_GIT_COMMIT_SHA`) so "what version
     is live?" is answerable instantly.
3. **DB connection pooling for serverless**
   - Switch `DATABASE_URL` to Supabase's pgbouncer (transaction-mode) port and
     document why — prevents connection exhaustion from per-cold-start
     `init_db()` (already flagged in the README).
4. **Post-deploy smoke tests in CI**
   - Step in `.github/workflows/backend.yml` / `frontend.yml` that curls
     `/health/ready` and one key API route after `vercel deploy`, failing the job
     on bad responses.
5. **Scheduled synthetic checks (GitHub Actions cron)**
   - Workflow running the smoke script against production every ~15 min,
     notifying on failure. Replaces an external uptime pinger — no third-party
     service needed.
6. **SLOs with error budget + runbook docs**
   - `docs/slo.md`: availability and latency targets, plus error-budget math
     (e.g. 99.5% ⇒ ~3.6 h/month) and what happens when the budget is spent.
   - `docs/runbook.md`: what to check when the backend is down (Vercel logs,
     Supabase status, env vars), and the exact rollback procedure
     (`vercel rollback` / dashboard).

Skipped as not significant for an internal MVP: load testing, a
Prometheus/Grafana stack (structured logs are the metrics source on
serverless), incident/postmortem templates, on-call tooling, chaos testing.

### Phase 3 — Microservices & architecture (JD: Microservices, System Design, Cloud Architect)

1. **Architecture doc with diagrams**
   - `docs/architecture.md`: C4-ish context + container diagrams (Mermaid),
     request flows for intake → search → outreach, the logging pipeline from
     Phase 1, and the job queue added in item 3 below.
2. **Extract ingestion as a separate service**
   - New `services/ingestion/` FastAPI app owning listing
     acquisition/normalization (today's `app/seed` + future connectors),
     deployed as its own Vercel project or container.
   - Backend talks to it over HTTP; DB stays the integration point for results.
   - This is honest microservice work: independent deploy, own healthcheck,
     own logs, secured service boundary (see item 4).
3. **Async job queue for ingestion runs**
   - The foundational item that makes the ingestion service real on serverless.
     Vercel kills functions at 10–60 s; a connector run that fetches + LLM-extracts
     dozens of listings cannot fit in one request.
   - `jobs` table in Supabase: `id`, `source`, `status`, `attempts`,
     `idempotency_key`, `result`, `error`, `created_at`.
   - Ingestion service polls (or is triggered by Vercel cron) and works jobs off
     the queue; backend enqueues and returns a job ID immediately.
   - Demonstrates queues, idempotency, and retry-with-backoff — the real
     substance behind "microservices experience."
4. **Service-to-service auth**
   - HMAC-signed requests or a static bearer token (with rotation notes) on the
     ingestion service; unauthenticated internal calls are rejected.
   - The difference between "I split a service" and "I secured a service boundary."
5. **Live ingestion progress via Supabase Realtime**
   - Frontend subscribes to the `jobs` table row for the current run; status and
     progress counters (fetched / normalized / rejected) arrive in real time.
   - No new infrastructure — Supabase Realtime is already in the stack.
   - "Event-driven architecture" talking point with visible UX value.
6. **Shared API contract (typed client)**
   - Generate a typed client from the ingestion service's OpenAPI schema (used
     by the backend to call it); a contract change breaks the build, not production.
   - The actual recurring pain of microservices is keeping contracts in sync;
     demonstrating an answer is worth more than a second service.
7. **Outbound rate limiting in connectors**
   - Per-source concurrency cap and polite throttle on listing-page fetches
     (asyncio semaphore + token bucket).
   - Required by the spec ("lawful ingestion"), and real backpressure
     engineering — prevents the ingestion service from being both a reliability
     and a ToS risk.
8. **Service boundaries doc**
   - Section in `architecture.md` on why each split (deploy cadence, failure
     isolation, serverless constraints), matching the spec's "modular connectors"
     principle.

Skipped as not significant here: gRPC (HTTP+JSON between two Vercel services
is fine), service mesh / service discovery (two services with known URLs), saga
/ distributed transactions (Postgres is the single system of record), splitting
the LLM layer into its own service (a second artificial split demonstrates less
than one honest one), formal API gateway (Next.js route handlers already cover
the BFF pattern).

### Phase 4 — SecOps automation (JD: SecOps automation, security context)

1. **CI security workflow** (`.github/workflows/security.yml`)
   - `pip-audit` + `npm audit --audit-level=high` + `gitleaks` secret scan on PRs.
2. **Dependabot** (`.github/dependabot.yml`) for pip and npm weekly updates.
3. **Runtime hardening**
   - Rate-limit middleware on auth endpoints (`slowapi`), security headers in
     `next.config.ts` (CSP, HSTS, X-Frame-Options).
4. **Audit logging**
   - `audit_events` table + repository: record sign-in/sign-up/password-change
     events — feeds the same log pipeline (SaaS telemetry angle).

### Phase 5 — Linux CLI / Bash (+ optional Go)

1. **Bash ops scripts** under `scripts/ops/` (Git Bash–compatible):
   - `smoke.sh` — hit health + key endpoints of any environment.
   - `db-backup.sh` — `pg_dump` of Supabase Postgres to a dated file.
   - `logs.sh` — query the log sink API for recent errors.
2. **Dockerfile + docker-compose** for the backend
   - Linux parity for local dev and a portable deploy story beyond Vercel
     (Cloud Architect talking point).
3. **(Optional) tiny Go service**
   - e.g. a log-forwarder or uptime-checker microservice, only if Go exposure is
     a goal; otherwise skip — Python already satisfies the JD's "Python **or** Go".

---

## 3. What we deliberately do NOT do

- **Switch to MERN** — MongoDB/Express would fight the Supabase/Postgres spec.
  The React + API + SQL skill set transfers directly.
- **Kubernetes / heavy IaC** — overkill for a Vercel-deployed MVP; Docker +
  architecture docs cover the cloud-architecture story.
- **EDR integration** — no real endpoints to monitor; the audit-log + telemetry
  pipeline demonstrates the same concepts at honest scale.

---

## 4. Suggested order of execution

| # | Step | Effort | JD coverage |
|---|------|--------|-------------|
| 1 | Phase 1.1–1.4: structured logs, middleware + context, scrubbing, exception handler | S | Log ingestion, normalization, filtering |
| 1b | Phase 1.5–1.6: LLM call telemetry + ingestion-run reports | M | Telemetry, log pipelines |
| 2 | Phase 2.1–2.3: dependency timeouts, health endpoints, DB pooling | M | SRE, reliability |
| 3 | Phase 2.4–2.5: CI smoke tests + scheduled synthetic checks | S | SRE, deployment |
| 4 | Phase 4.1–4.2: security CI + Dependabot | S | SecOps automation |
| 5 | Phase 3.1: architecture doc + diagrams | M | System design |
| 6 | Phase 5.1: bash ops scripts | S | Bash, Linux CLI |
| 7 | Phase 3.2–3.4: ingestion service + job queue + service auth | L | Microservices, architect |
| 7b | Phase 3.5–3.7: Realtime progress, typed client, connector rate limiting | M | Event-driven, contracts, backpressure |
| 8 | Phase 2.6: SLOs with error budget + runbook | S | SRE |
| 9 | Phase 4.3–4.4: rate limiting, audit log | M | Security context |
| 10 | Phase 5.2–5.3: Docker (+ optional Go) | M | Cloud architect, Go |
