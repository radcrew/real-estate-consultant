# Code Quality Review — `real-estate-consultant`

Scope: `backend/` (FastAPI), `frontend/` (Next.js), `services/ingestion/` (ingestion
microservice). Full read of the source trees in all three; findings below are grounded in
`file:line` citations.

---

## 1. Project structure

### Strengths

- **Backend endpoint packages are (mostly) uniform.** `account/`, `auth/`, `intake_sessions/`,
  `listings/`, `outreach/`, `questions/`, `search/`, `ping/` each follow the same shape:
  `router.py` + sibling modules + (usually) `exceptions.py`. `intake_sessions/answers/` even
  nests the same pattern one level deeper (`router.py`, `guided.py`, `llm.py`,
  `exceptions.py`) — a consistent, predictable convention for a codebase this size.
- **`app/llm/{fit,intake,outreach}/`** all follow the exact same
  `schema.py` / `prompts.py` / `service.py` / `exceptions.py` four-file shape. This holds
  100% — genuinely well-maintained convention, confirmed by diffing all three directories.
- **The ingestion microservice mirrors the main backend's shape** (`app/api/`, `app/core/`,
  `app/models/`, plus its own `app/connectors/`) rather than inventing a different layout —
  good cross-service consistency.
- **Frontend co-locates `styles.ts` per component subtree** consistently:
  `components/account/styles.ts`, `components/auth/fields/styles.ts`,
  `components/landing/hero/search-form/styles.ts`,
  `components/listings/detail/styles.ts`, `components/search/wizard/styles.ts`,
  `components/search/wizard/question-input/select/styles.ts`, etc. — a deliberate, holds-up
  pattern, not an accident.
- **Frontend hooks are named consistently**: `use-address-autocomplete.ts`,
  `use-fit-explanation.ts`, `use-listing-detail.ts`, `use-location.ts`,
  `use-outreach-draft.ts`, `use-search-results.ts` — kebab-case file, one hook, in
  `frontend/hooks/`.

### Issues

- **Some backend endpoint domains are flat files, not packages, with no clear rule for
  which gets which.** `app/api/v1/endpoints/agents.py`, `submissions.py`, and
  `submission_images.py` sit directly under `endpoints/` as single files, while
  `admin/`, `listings/`, `outreach/` etc. are full packages. `submissions.py` and
  `submission_images.py` are closely related (submission flow) yet aren't grouped into a
  `submissions/` package the way `intake_sessions/answers/` groups sub-concerns. Not wrong,
  but there's no visible rule for "package vs. flat file" — it reads as organic growth.
- **`app/admin/` is the one endpoint package missing `exceptions.py`.** Every other
  package with error paths has one (`account/exceptions.py`, `auth/exceptions.py`,
  `listings/exceptions.py`, `outreach/exceptions.py`, `intake_sessions/exceptions.py`,
  `intake_sessions/answers/exceptions.py`). `admin/router.py` has no sibling exceptions
  module — see §2 for the consequence.
- **`app/utils/` is a dumping ground mixing generic helpers with domain logic.**
  `app/utils/exceptions.py` (68 lines, generic HTTP-exception factories) and
  `app/utils/values.py` (19 lines, generic coercion) sit next to modules that are pure
  intake/search *business logic*, not utilities:
  - `app/utils/intake_criteria.py:1` — "Normalize intake answers into the flat storage
    format search expects."
  - `app/utils/intake_next_question.py`, `app/utils/intake_validation.py` — intake-flow
    state machine logic.
  - `app/utils/criteria_search.py:1` — "Parse intake search criteria dicts (no SQL / DB)."
  - `app/utils/search_sql.py` (204 lines, the largest file in `utils/`) — SQL expression
    builders for match scoring (`match_score_expr`, `component_score_exprs`).
  These five files are core domain logic for the intake/search feature, not generic
  utilities, and are ~450 of `utils/`'s 622 lines. A newcomer looking for "where does
  intake criteria get validated" would not think to check `utils/`.
- **The test tree doesn't mirror the source tree**, unlike `schemas/` and `api/`:
  - `app/repositories/` has 12 modules (`account.py`, `featured.py`, `intake_sessions.py`,
    `listing_submissions.py`, `outreach_drafts.py`, `profiles.py`, `properties.py`,
    `property_images.py`, `questions.py`, `saved_listings.py`, `search_profiles.py`,
    `search_profiles.py`) and **zero direct tests** — no `tests/repositories/` directory
    exists at all.
  - `app/llm/{fit,intake,outreach}/service.py` are tested, but as
    `tests/utils/test_fit_service.py`, `tests/utils/test_intake_service.py`,
    `tests/utils/test_outreach_service.py` — flattened into `tests/utils/` rather than a
    mirroring `tests/llm/fit/`, `tests/llm/intake/`, `tests/llm/outreach/`.
  - Same for `app/clients/ingestion/client.py` → `tests/utils/test_ingestion_client.py`,
    and `app/services/ingestion.py` → `tests/utils/test_ingestion_service.py`. Neither
    `tests/clients/` nor `tests/services/` exists.
  `tests/utils/` (28 files) has become the catch-all for "everything that isn't an
  endpoint test or a schema test," regardless of what part of `app/` it actually covers.
- **A hook lives outside `frontend/hooks/`.** `frontend/components/ui/use-theme-mode.ts`
  is named and shaped exactly like the other six hooks (`use-` prefix, `useThemeMode`
  export) but sits in `components/ui/` instead of `hooks/` — the one hook that isn't where
  a contributor would look for it.
- **Two different "ingestion" concepts share a name across module boundaries**:
  `backend/app/services/ingestion.py` (a one-function wrapper, `wake_processor()`, that
  calls the ingestion microservice) vs. the top-level `services/ingestion/` microservice
  directory itself. Reasonable in isolation, but `app/services/` contains exactly one file
  — it's a single-file directory that exists only to hold `ingestion.py`, and its name
  collides with the sibling top-level `services/` at the repo root. Grepping "ingestion
  service" turns up three different things (`app/services/ingestion.py`,
  `app/clients/ingestion/`, `services/ingestion/`).

---

## 2. Separation of concerns

### Strengths

- **The `raise_*` domain-exception convention is genuinely almost universal.** Repositories
  never construct `HTTPException` themselves — they call named helpers like
  `raise_intake_session_not_found()` (`app/repositories/exceptions.py:82`),
  `raise_intake_questions_load_empty()` (`app/repositories/exceptions.py:86`), or
  `raise_bad_gateway(...)` (`app/utils/supabase/response.py:28`), keeping HTTP-status
  knowledge out of the data-access layer. Checked broadly across `repositories/`, `llm/*/`,
  and most `endpoints/*/` — it holds.
- **Frontend components mostly do go through `services/`.** `contact/form.tsx` and
  `landing/subscribe/index.tsx` use raw `fetch()` (`components/contact/form.tsx:36`,
  `components/landing/subscribe/index.tsx:32`), but that's *correct*, not a violation —
  one hits a third-party API (`api.web3forms.com`) and the other a Next.js route handler
  (`/api/newsletter`), neither of which is the FastAPI backend `services/*.ts` wraps.
  `components/account/page.tsx` imports `axios`'s `isAxiosError` only for status-code
  checks (`components/account/page.tsx:3,190,235`) — actual calls still go through
  `accountService`. This is the pattern working as intended.

### Issues

- **`app/api/v1/endpoints/admin/router.py` is the one endpoint that skips the repository
  layer entirely and raises raw `HTTPException` directly**, breaking both conventions
  described above in the same file:
  - `admin/router.py:44-48` — `execute_db_safe(client.table("jobs").select(...)...)`
    runs directly inside the route handler, not via an `app/repositories/jobs.py` (which
    doesn't exist). Every other domain with DB access has a repository module; jobs don't.
  - `admin/router.py:54-57` — `raise HTTPException(status_code=409, detail=...)` for a
    duplicate enqueue, instead of a `raise_conflict(...)` (already exists in
    `app/utils/exceptions.py`) or a new `admin/exceptions.py` helper.
  - `admin/router.py:63` — `raise HTTPException(status_code=500, detail="Job insert
    returned no data.")` — a raw 500 raised by hand, where the rest of the codebase uses
    `raise_bad_gateway(...)` for "Supabase returned something unexpected" (see
    `app/utils/supabase/response.py:28,35` for the standard shape).
  This is a single file, so it's an easy fix, but it's a real inconsistency a new
  contributor copying "how do I add an endpoint" from `admin/` would propagate.
- **`components/admin/ingest.tsx` inlines a Supabase realtime subscription and a raw
  table query directly in the component**, with no corresponding hook — unlike every other
  data-driven view in the app:
  - `components/admin/ingest.tsx:55-63` — `getSupabaseBrowserClient()` +
    `.channel(...).on("postgres_changes", ...)` realtime subscription built inline in a
    `useEffect`.
  - `components/admin/ingest.tsx:77-84` — a second, raw `supabase.from("jobs").select(...)`
    query, also inline, right after the `adminService.enqueueIngest()` call.
  Every comparable feature (search results, listing detail, outreach draft, fit
  explanation) pushes this into a `hooks/use-*.ts`. `AdminIngestView` is the one view that
  owns both UI and data/subscription logic together — harder to test or reuse, and the one
  place Supabase's client is called directly from a component rather than through a
  hook/service.

---

## 3. Naming

### Strengths

- **Frontend service layer naming is completely consistent**: every file in
  `frontend/services/` exports a `PascalCaseService` class plus a `camelCaseService`
  singleton instance constructed from it — `AccountService`/`accountService`,
  `AdminService`/`adminService`, `AuthService`/`authService`,
  `ListingsService`/`listingsService`, `OutreachService`/`outreachService`,
  `SearchService`/`searchService`, `IntakeSessionsService`/`intakeSessionsService`. Zero
  exceptions found.
- **Backend `raise_*` exception helpers** read as a single, coherent vocabulary across
  `app/utils/exceptions.py`, `app/repositories/exceptions.py`, `app/llm/*/exceptions.py`,
  and most `endpoints/*/exceptions.py` — the one exception is `admin/router.py` (§2).

### Issues

- **Repository read functions use three interchangeable verbs with no semantic rule**:
  `get_`, `load_`, and `fetch_` are all used for "read a single row," seemingly at random:
  - `get_`: `get_auth_user` (`app/repositories/profiles.py:45`),
    `get_property_by_id` (`app/repositories/properties.py:73`),
    `get_property_match_breakdown` (`app/repositories/properties.py:82`),
    `get_featured_property_rows` (`app/repositories/featured.py:19`)
  - `load_`: `load_intake_session_row` (`app/repositories/intake_sessions.py:46`),
    `load_profile_session_row` (`app/repositories/intake_sessions.py:59`),
    `load_intake_questions` (`app/repositories/questions.py:120`),
    `load_question_key_metadata` (`app/repositories/questions.py:97`)
  - `fetch_`: `fetch_profile_row` (`app/repositories/profiles.py:47`),
    `fetch_outreach_draft_for_user` (`app/repositories/outreach_drafts.py:39`),
    `fetch_latest_outreach_draft_for_property` (`app/repositories/outreach_drafts.py:62`),
    `fetch_first_image_url` / `fetch_all_image_urls` (`app/repositories/property_images.py:13,35`)

  `fetch_profile_row` and `load_intake_session_row` are structurally identical operations
  (single Supabase row by id) yet use different verbs — there's no discoverable rule
  (e.g. `get_` = by primary key, `load_` = composite/joined, `fetch_` = remote/network) that
  explains the split; it reads as three different authors' defaults. By contrast, `list_`
  is used consistently for every multi-row read (`list_listing_submissions`,
  `list_properties_by_broker`, `list_saved_property_ids`) — worth standardizing the
  singular-read case the same way.
- **Three separate representations of the same `properties` table, in three different
  directories, with three different names** — not wrong, but worth knowing about as a
  newcomer: `app/db/property_row.py:14` (`PropertyRow`, SQLAlchemy ORM, used for
  request-time queries), `app/models/properties.py:9` (`Properties`, Pydantic, "normalized
  listing row extracted from LoopNet-style raw JSON," used at ingestion time), and
  presumably an API-facing shape under `app/schemas/listings.py`. The `models/` vs.
  `schemas/` distinction (row-shape-for-a-table vs. API-request/response-shape) is real and
  applied consistently across the other five files in `app/models/` (`intake_sessions.py`,
  `profile.py`, `property_images.py`, `questions.py`, `search_profiles.py` are all
  docstring-labeled "Row shape for `public.<table>`"), but it's implicit — nothing states
  the rule, so `models/properties.py`'s "normalized ingestion row" framing reads as a
  slightly different job than its siblings' "mirrors a DB row" framing.

---

## If you fix only a few things

1. **`admin/router.py`** — extract the jobs DB access into `app/repositories/jobs.py` and
   replace both raw `HTTPException` raises with `raise_conflict(...)` /
   `raise_bad_gateway(...)` (or a new `admin/exceptions.py`). Smallest, highest-signal fix;
   it's the one file that breaks two conventions at once.
2. **Pick one verb for single-row repository reads** (`get_` reads best, given `list_` is
   already the multi-row convention) and rename `load_*`/`fetch_*` functions in
   `app/repositories/` to match. Mechanical, low-risk, removes a real "which do I use"
   question for new code.
3. **Move `use-theme-mode.ts` into `frontend/hooks/`** — trivial, removes the one hook that
   isn't where the rest of the codebase's convention says to look for it.
4. **Give `AdminIngestView` a `use-admin-ingest.ts` hook** to own the Supabase subscription
   and job-row state, matching how every other feature in the app separates data logic
   from the component tree.
5. Lower priority: consider whether `intake_criteria.py`, `intake_next_question.py`,
   `intake_validation.py`, `criteria_search.py`, and `search_sql.py` belong in `utils/` at
   all, or would read better under something like `app/domain/intake/` — this is a bigger
   move, worth doing opportunistically rather than as a dedicated refactor.
