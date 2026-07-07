# Fit Explainability — Implementation Plan

## Goal

For a property in search results, let the user see a short, plain-English reason
*why* it got its match score, instead of just the `NN% match` badge. This turns
the already-existing "matched from your search profile" placeholder blurb into
something real.

## Where this lives

`match_score` is computed deterministically in SQL
(`backend/app/utils/search_sql.py:match_score_expr`) as
`0.4·location + 0.3·price_gaussian + 0.3·size_gaussian`, from the **intake
session's `criteria`** vs. the property row. That criteria only exists in the
context of a search session (`GET/PUT /api/v1/search/{session_profile_id}`).

The standalone listing detail page (`/listings/[id]`, `useListingDetail` →
`listingsService.getListing`) has **no session/criteria context** — it just
fetches a property by id. So this feature is scoped to the **search results
page** (`/search/[id]`, backed by `useSearchResults` / `PropertyMatch[]`),
where criteria and match score already live side by side. Listing detail is a
non-goal for v1 (see below).

## Reused building blocks

- LLM call pattern: `huggingface_provider.generate_structured_output(messages, response_format, temperature, max_tokens)` — same call `generate_broker_outreach_draft` makes (`backend/app/llm/outreach/service.py`).
- Package shape: `app/llm/outreach/{schema,prompts,service,exceptions}.py` — copy this structure for a new `app/llm/fit/` package.
- Auth/access: `ensure_search_profile_access` + `load_profile_session_row` (`backend/app/repositories/intake_sessions.py`, used in `search/router.py`).
- Frontend hook shape: `useOutreachDraft` (`frontend/hooks/use-outreach-draft.ts`) — generate-on-click, local state, no polling.
- The client already has a slot for this: `ResultCardListing.matchBlurb`, currently just the property description or `"Matched from your search profile."` (`frontend/utils/search/property.ts:blurbFromProperty`). That fallback string is what gets replaced by a real, on-demand explanation.

## Data flow

1. User is on `/search/[sessionId]`, sees a result card with a match badge.
2. User expands "Why this fits" on a card.
3. Frontend calls `POST /api/v1/search/{session_profile_id}/fit/{property_id}`.
4. Backend loads the session's `criteria`, loads the property **plus its score
   components** (location/price/size, not just the blended total), and asks
   the LLM for a short narrative grounded in those components.
5. Response returns the narrative (not persisted) — cached only in frontend
   component state for that page view.

---

## Backend changes

### 1. Expose score components (`app/utils/search_sql.py`)

Today `match_score_expr` computes and *discards* the three components. Refactor
so they're reusable without duplicating the Gaussian math:

```python
def component_score_exprs(criteria: dict[str, Any]) -> tuple[Any, Any, Any]:
    """(location_expr, price_expr, size_expr), each 0.0–1.0."""
    loc = location_score_expr(*parse_location_fields(criteria))
    price = _gaussian_score_for_criterion(PropertyRow.price, criteria.get("price"))
    size = _gaussian_score_for_criterion(PropertyRow.size_sqft, criteria.get("size_sqft"))
    return loc, price, size


def match_score_expr(criteria: dict[str, Any]) -> Any:
    loc, price, size = component_score_exprs(criteria)
    raw_score_expr = _lit_float(0.4) * loc + _lit_float(0.3) * price + _lit_float(0.3) * size
    return func.least(_lit_float(100.0), func.greatest(_lit_float(0.0), _lit_float(100.0) * raw_score_expr))
```

`match_score_expr` behavior is unchanged; existing tests for it stay green.

### 2. Repository lookup (`app/repositories/properties.py`)

New function, single-row query by id, selecting the property plus the three
labeled component expressions:

```python
async def get_property_match_breakdown(
    session: AsyncSession,
    property_id: UUID,
    criteria: dict[str, Any],
) -> tuple[dict[str, Any], tuple[float, float, float, float]] | None:
    """(property_dict, (location, price, size, total)) or None if not found."""
    loc, price, size = component_score_exprs(criteria)
    total = match_score_expr(criteria)
    query = (
        select(PropertyRow, loc.label("location_score"), price.label("price_score"),
               size.label("size_score"), total.label("match_score"))
        .where(PropertyRow.id == property_id)
        .limit(1)
    )
    result = await session.execute(query)
    row = result.first()
    if row is None:
        return None
    property_row, location_score, price_score, size_score, match_score = row
    return property_row_to_search_dict(property_row), (
        float(location_score), float(price_score), float(size_score), float(match_score),
    )
```

### 3. Schemas (`app/schemas/fit.py`, new file)

```python
class FitScoreBreakdown(BaseModel):
    location: float = Field(..., ge=0.0, le=1.0)
    price: float = Field(..., ge=0.0, le=1.0)
    size: float = Field(..., ge=0.0, le=1.0)
    total: float = Field(..., ge=0.0, le=100.0)

class FitExplanationResponse(BaseModel):
    property_id: UUID
    score: FitScoreBreakdown
    summary: str
    strengths: list[str] = Field(default_factory=list)
    considerations: list[str] = Field(default_factory=list)
```

### 4. LLM package `app/llm/fit/` (mirrors `app/llm/outreach/`)

- **`schema.py`** — `FitExplanationLLM(BaseModel)`: `summary: str` (short
  paragraph, min/max length like `OutreachDraftEmailLLM`), `strengths:
  list[str]` (max 3 items), `considerations: list[str]` (max 3 items, softer
  framing than "weaknesses" — things that don't match as well).
- **`prompts.py`** — `FIT_EXPLANATION_SYSTEM_PROMPT` (rules: only use the
  criteria/property facts given; never invent numbers; don't restate the
  percentage; plain language, no jargon dump) + `build_fit_user_message(...)`.
  Convert each raw 0–1 component into a qualitative tier before handing it to
  the model (e.g. `score_to_tier(0.92) → "excellent match"`,
  `0.55 → "partial match"`, `0.0 → "no match"`) so the LLM reasons over labels,
  not floats it might mis-restate. Mirrors how `format_listing_block_for_outreach`
  turns a row into plain-text lines.
- **`service.py`** — `generate_fit_explanation(*, criteria, property_row, score)
  -> FitExplanationLLM`, calling `huggingface_provider.generate_structured_output`
  at low temperature (~0.2, this should be factual, not creative) and modest
  `max_tokens` (~400 — much shorter output than an email draft).
- **`exceptions.py`** — `raise_fit_explanation_empty()` (mirrors
  `raise_outreach_email_empty`).

**Cost short-circuit:** if `criteria` has none of `location`/`price`/`size_sqft`
set (a quick search with nothing filled in yet, so all three components are at
their neutral default), skip the LLM entirely and return a canned summary
("No specific criteria set yet — every listing scores neutrally until you add
some."). Don't spend a call explaining a score that isn't really discriminating
anything.

### 5. Endpoint (`app/api/v1/endpoints/search/fit.py`, new file)

New sibling module, same pattern as `listings/featured.py` being a sibling of
`listings/router.py` — own `router = APIRouter(prefix="/search", tags=["search"])`:

```python
@router.post(
    "/{session_profile_id}/fit/{property_id}",
    response_model=FitExplanationResponse,
    summary="Explain why a property matches the session's search criteria",
)
async def explain_fit(
    session_profile_id: UUID,
    property_id: UUID,
    client: SupabaseSdkDep,
    db: DbSession,
    current_user: CurrentUser,
) -> FitExplanationResponse:
    await ensure_search_profile_access(client, session_profile_id, current_user.id)
    session_row = await load_profile_session_row(client, session_profile_id)
    criteria = dict(session_row.get("criteria") or {})

    found = await get_property_match_breakdown(db, property_id, criteria)
    if found is None:
        raise_listing_not_found()
    property_row, (location, price, size, total) = found

    result = await generate_fit_explanation(
        criteria=criteria, property_row=property_row,
        score=(location, price, size, total),
    )
    return FitExplanationResponse(
        property_id=property_id,
        score=FitScoreBreakdown(location=location, price=price, size=size, total=total),
        summary=result.summary,
        strengths=result.strengths,
        considerations=result.considerations,
    )
```

Use `POST` (not `GET`) since it triggers a paid LLM call, same reasoning as
`POST /outreach/drafts` — even though this response isn't persisted.

### 6. Wire into router (`app/api/v1/router.py`)

```python
from app.api.v1.endpoints.search.fit import router as search_fit_router
...
protected.include_router(search_fit_router)
```

---

## Frontend changes

### 1. Service (`frontend/services/search.ts`, extend `SearchService`)

```typescript
export type FitExplanation = {
  property_id: string;
  score: { location: number; price: number; size: number; total: number };
  summary: string;
  strengths: string[];
  considerations: string[];
};

// on SearchService:
async explainFit(sessionProfileId: string, propertyId: string): Promise<FitExplanation> {
  const { data } = await this.http.post<FitExplanation>(
    `/search/${sessionProfileId}/fit/${propertyId}`,
  );
  return data;
}
```

### 2. Hook (`frontend/hooks/use-fit-explanation.ts`, new file)

Simpler than `useOutreachDraft` — no "latest saved" GET, no edit/save, just
generate-on-demand with per-property caching so re-expanding a card already
opened this page view doesn't refire the request:

```typescript
export const useFitExplanation = (sessionProfileId: string | undefined) => {
  const [cache, setCache] = useState<Record<string, FitExplanation>>({});
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const explain = useCallback(async (propertyId: string) => {
    if (!sessionProfileId || cache[propertyId]) return cache[propertyId];
    setLoadingId(propertyId);
    setError(null);
    try {
      const result = await searchService.explainFit(sessionProfileId, propertyId);
      setCache((prev) => ({ ...prev, [propertyId]: result }));
      return result;
    } catch (err) {
      setError(getApiErrorMessage(err));
      throw err;
    } finally {
      setLoadingId(null);
    }
  }, [sessionProfileId, cache]);

  return { explain, cache, loadingId, error };
};
```

### 3. UI

Add an expandable "Why this fits" affordance **on the search results view**
(`frontend/components/search/result/index.tsx`), not inside the shared
`PropertyCard` (`frontend/components/property/card.tsx`) — that card is reused
for the home grid and plain listings grid where there's no session/criteria
and `matchScore` is `0`. Concretely:

- `PropertyCard` gains an optional `onExplainFit?: () => void` render slot
  (only passed by the search-results view, so home/listings grids are
  unaffected) — a small "Why this fits" text-button next to the match badge.
- Clicking it calls `explain(property.id)` and shows a small popover/inline
  panel with `summary` + up to 3 `strengths` + up to 3 `considerations`,
  loading state from `loadingId === property.id`.
- Wire `useFitExplanation(sessionProfileId)` into
  `frontend/components/search/result/index.tsx`, pass `explain` down to each
  card.

---

## Edge cases / decisions

- **Property not in the current result set**: not restricted — the endpoint
  only needs the session's criteria + a valid property id, it doesn't check
  the property was actually among that session's ranked results. Simpler, and
  there's no correctness reason to forbid it.
- **Criteria changes after generating**: no cache invalidation logic needed
  since nothing is persisted server-side; a fresh POST always reflects current
  criteria. The frontend per-property cache is scoped to one page-load of
  `useSearchResults`, so it naturally goes stale (cleared) on navigation.
- **LLM failure/timeout**: reuse existing `huggingface_provider` exceptions
  (`raise_hf_request_timeout`, etc.) — same shape as outreach, no new error
  handling needed at the service layer.
- **Property has almost no data** (no price/size/description): `score_to_tier`
  still produces a tier from the Gaussian's null-handling (`0.0` when the
  column is null), so the prompt will correctly say "price: no data" rather
  than fabricating one.

## Explicit non-goals (v1)

- **No persistence** — no new DB table. This is a read-mostly, deterministic-input
  narrative; add a cache table later only if LLM cost/latency on repeat views
  becomes a real problem.
- **No batch/bulk generation** for a full results page — always lazy,
  per-card, on click. Generating for all 20 rows on page load would be slow
  and expensive for explanations most users won't read.
- **No listing-detail-page integration** — no criteria context exists there;
  revisit only if intake criteria becomes available outside a search session.

## Testing plan

Mirror existing outreach test coverage:

- `backend/tests/utils/test_criteria_search.py` / a new
  `test_search_sql.py` — unit-test `component_score_exprs` against
  `match_score_expr` (components should recombine to the same total).
- `backend/tests/utils/test_fit_service.py` (new, mirrors
  `test_outreach_service.py`) — `generate_fit_explanation`, mocked provider,
  including the no-criteria short-circuit path.
- `backend/tests/utils/test_fit_prompts.py` (new, mirrors
  `test_outreach_prompts.py`) — `score_to_tier` boundaries, user-message
  assembly.
- `backend/tests/schemas/test_fit.py` (new, mirrors `test_outreach.py`
  schema tests) — `FitScoreBreakdown` / `FitExplanationResponse` bounds.
- `backend/tests/api/test_search.py` — add a `TestExplainFit` class
  (mirrors `TestCreateOutreachDraft` in `test_outreach.py`): 404 on unknown
  property, 403/404 on session not owned by user, happy path shape.
- Frontend: `frontend/tests/hooks/use-fit-explanation.test.ts` (new) and a
  render test on the result card's new affordance, alongside the existing
  `frontend/tests/components/search/result/index.test.tsx`.

## Suggested build order

1. `search_sql.py` refactor + its unit test (no behavior change, safe first PR).
2. `app/llm/fit/*` + `app/schemas/fit.py` + service test — pure backend logic,
   testable without the endpoint.
3. Endpoint + repository function + API test.
4. Frontend service + hook + UI wiring.
5. Manual verification: run the app, do a real search with partial criteria,
   confirm the explanation reads sensibly and the no-criteria short-circuit
   fires on a quick search with nothing filled in.
