# Contributing

Thanks for helping build the real estate consultant MVP. This project follows the [Code of Conduct](CODE_OF_CONDUCT.md) — please read it before contributing.

## Getting set up

- **Backend (FastAPI):** from `backend/`, run `pip install -e ".[dev]"`, then start the API with `fastapi dev` (or `fastapi dev backend/app/main.py` from the repo root).
- **Frontend (Next.js):** from `frontend/`, copy `.env.example` to `.env.local`, then `npm install` and `npm run dev`.

See [README.md](README.md) for full local setup and deployment details.

## Workflow

1. Create a branch off `main` for your change (e.g. `feat/short-description`, `fix/short-description`).
2. Keep changes focused — small, reviewable commits and pull requests are strongly preferred over large ones.
3. Write a clear commit message describing *why* the change was made, not just what changed.
4. Open a pull request against `main` using the [PR template](.github/PULL_REQUEST_TEMPLATE.md). Link any related issue.
5. Make sure CI is green before requesting review.

## Code style & checks

- **Backend:** lint with `ruff` (`ruff check .` from `backend/`); tests run with `pytest` (`pytest` from `backend/`, coverage via `pytest-cov`).
- **Frontend:** lint with `npm run lint`; tests run with `npm run test` (Vitest), coverage via `npm run test:coverage`.

Run the relevant checks locally before opening a PR — the same checks run in CI (`.github/workflows/backend.yml`, `.github/workflows/frontend.yml`, `.github/workflows/coverage.yml`).

## Reporting bugs & requesting features

Use the [issue templates](.github/ISSUE_TEMPLATE) to file bug reports or feature requests. For security vulnerabilities, follow [SECURITY.md](SECURITY.md) instead of opening a public issue.

## Questions

If anything here is unclear, open an issue or reach out at code@radcrew.org.
