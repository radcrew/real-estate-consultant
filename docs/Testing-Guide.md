# Testing Guide

All tests live in each package's `tests/` directory — never co-located with source files.

---

## Backend

**Framework:** pytest + pytest-asyncio + httpx

```bash
cd backend

# Run all tests
python -m pytest tests/ -q

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=term-missing

# Run a single file
python -m pytest tests/api/test_auth.py -v
```

**Current coverage:** ~82% (401 tests)

### Key patterns

| Concern | Approach |
|---|---|
| API endpoint tests | `httpx.AsyncClient` + `ASGITransport(app=app)` |
| Auth/DB bypass | `app.dependency_overrides[get_current_user]` etc. |
| Async repo calls | `patch("module.path.fn", new_callable=AsyncMock)` |
| Admin-only routes | Override both `get_current_user` and `get_current_admin` |
| Pydantic validation | `pytest.raises(ValidationError)` |

Shared fixtures (`mock_db`, `mock_supabase`, `mock_user`, `client`) live in `tests/api/conftest.py`.

---

## Ingestion service

**Framework:** pytest + pytest-asyncio (strict mode)

```bash
cd services/ingestion

# Run all tests
python -m pytest tests/ -q

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=term-missing
```

**Current coverage:** ~96% (145 tests)

### Key patterns

| Concern | Approach |
|---|---|
| Async fixtures | `@pytest_asyncio.fixture` (required in strict mode) |
| Endpoint tests | `httpx.AsyncClient` + `ASGITransport` |
| Supabase client | `MagicMock` with chained method mocks |
| Connector run | `patch("app.api.jobs._claim_job", ...)` |
| Unhandled exceptions | `ASGITransport(raise_app_exceptions=False)` |

Required env vars are set in `tests/conftest.py` before any app import.

---

## Frontend

**Framework:** Vitest + Testing Library

```bash
cd frontend

# Run all tests
pnpm test

# Run with coverage
pnpm test:coverage

# Run a single file
pnpm vitest run tests/components/auth/sign-in-form.test.tsx
```

**Current coverage:** reported via v8 in CI

### Key patterns

| Concern | Approach |
|---|---|
| Component render | `@testing-library/react` with `jsdom` environment |
| Service mocks | `vi.mock("@services/...")` |
| Context mocks | `vi.mock("@contexts/search-wizard", ...)` |
| Toast provider | `vi.mock("@components/ui/toast", ...)` |
| Async submits | `fireEvent.submit(form)` + `await findByRole(...)` |
| Fetch calls | `vi.stubGlobal("fetch", vi.fn().mockResolvedValue(...))` |

---

## Coverage report in CI

The `Coverage Report` workflow runs on every PR and posts a comment with a summary table:

| Package | Target |
|---|---|
| Frontend | lines % from `coverage-summary.json` |
| Backend | lines % from `coverage.json` (`totals.percent_covered`) |
| Ingestion | lines % from `coverage.json` (`totals.percent_covered`) |

🟢 ≥ 80%  · 🟡 60–79%  · 🔴 < 60%  · ⬜ no data
