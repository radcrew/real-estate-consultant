# AGENTS.md

Root coordination contract for AI and human contributors in this repo. Architecture and working guidelines live in [CLAUDE.md](./CLAUDE.md); this file states the non-negotiables and where to look.

## Scope

- Applies to the whole monorepo: `frontend/`, `backend/`, `services/mcp/`, `services/ingestion/`, `scripts/`.
- No nested `AGENTS.md` files exist yet. One added under a package may tighten the rules for that subtree but must not relax the rules here.

Normative language: `MUST`/`MUST NOT` are mandatory. `SHOULD`/`SHOULD NOT` are expected by default; deviations should be explained in the PR. `MAY` is optional.

## Non-Negotiables

- `MUST` use **pnpm** for the Node side. `pnpm-lock.yaml` is the only lockfile; CI and the Vercel frontend deploy both run `pnpm install --frozen-lockfile`. `MUST NOT` run `npm install` or `yarn install`, and `MUST NOT` commit a `package-lock.json` or `yarn.lock`. Note there is no `packageManager` field pinning the version: CI pins pnpm 10 through `pnpm/action-setup@v4`, and nothing enforces that locally.
- `MUST` address the frontend as `pnpm --filter radestate <script>`. `pnpm-workspace.yaml` lists only `frontend`, so the three Python packages (`backend/`, `services/mcp/`, `services/ingestion/`) are not workspace members; each carries its own venv and `pyproject.toml`.
- `MUST NOT` hand-edit `backend/app/clients/ingestion/models.py`. It is generated from `services/ingestion/openapi.json` by `scripts/generate_ingestion_models.py`, and `backend.yml`'s contract-check job fails on any drift. Change the ingestion schema, regenerate, and commit the result in the same change.
- `MUST NOT` read a green CI run as "tested". `frontend.yml`'s only check is a **build**, with no lint and no test step. `backend.yml` runs Ruff and the contract check, **not pytest**. Both suites run only in `coverage.yml`, which triggers on `pull_request` alone, so a push straight to `main` deploys untested code. Run the suite for the package you touched locally; nothing upstream will catch it for you.
- `MUST NOT` trust [CONTRIBUTING.md](./CONTRIBUTING.md) on tooling. It tells contributors to run `npm install`, `npm run dev`, `npm run lint` and `npm run test` in `frontend/`, which would write a `package-lock.json` alongside the pnpm lockfile, and it claims "the same checks run in CI", which is not true of frontend lint or either test suite. Fixing that file is welcome; citing it is not.
- `MUST` add a `// @vitest-environment jsdom` docblock to any Vitest file that renders a component. `frontend/vitest.config.ts` sets `environment: "node"` globally and component suites opt in per file; without the docblock a suite fails on a missing DOM rather than on its assertions.
- `MUST` remember that **opening a pull request deploys live previews**, from the `deploy-preview` job in both `backend.yml` and `frontend.yml`. Each is path-filtered, so a backend-only change deploys the backend preview and a frontend-only change deploys the frontend one. Opening a PR is an outward-facing action, not just a CI run.
- `MUST NOT` commit secrets. `frontend/.env` and `frontend/.env.local` are gitignored. Anything prefixed `NEXT_PUBLIC_` is inlined into the client bundle at build time, so a value that must stay private `MUST NOT` carry that prefix.
- `MUST` treat `services/mcp/` as deploying through the Vercel **Git integration** under a different Vercel team, not through `secrets.VERCEL_TOKEN`. That token belongs to the frontend/backend team and cannot see the MCP project. See the header comment in `.github/workflows/mcp.yml`.
- `SHOULD` run only the scoped command for the package you touched, not every suite, unless the change spans packages.
- `SHOULD NOT` read an absent CI check as a passing one. `frontend.yml`, `backend.yml` and `mcp.yml` are all path-filtered; a root-only change (this file, `README.md`, `docs/`) triggers none of them. `coverage.yml` is the only workflow with no path filter.

## Command Baseline

Node, from the repo root:

- Install: `pnpm install`
- Dev: `pnpm dev` (frontend and backend together), `pnpm dev:all` (adds the MCP adapter), or `pnpm dev:fe` / `pnpm dev:be` / `pnpm dev:mcp`
- Lint: `pnpm lint` (ESLint over `frontend/`)
- Build: `pnpm build`

Frontend tests, from `frontend/`:

- All: `pnpm test`; watch: `pnpm test:watch`; coverage: `pnpm test:coverage`
- One file: `pnpm test <path>`; one case: `pnpm test -t "<name>"`

Python, from the package directory with its venv active:

- Install: `pip install -e ".[dev]"`
- Test: `pytest -q`
- Lint: `ruff check app`

Full per-package matrix and the current test baselines: see [CLAUDE.md](./CLAUDE.md#commands).

## Where To Look

- Working guidelines and full architecture: [CLAUDE.md](./CLAUDE.md)
- Repo overview, environment variables and deploy URLs: [README.md](./README.md)
- MCP adapter: [services/mcp/README.md](./services/mcp/README.md)
- Contribution workflow: [CONTRIBUTING.md](./CONTRIBUTING.md), stale on tooling, see Non-Negotiables
- PR template: [.github/PULL_REQUEST_TEMPLATE.md](./.github/PULL_REQUEST_TEMPLATE.md)
- Reporting vulnerabilities: [SECURITY.md](./SECURITY.md)

## Enforcement

Mechanical checks over prose, where they exist:

- **ESLint (`frontend/eslint.config.mjs`) is run by no workflow.** It is a local-only check. The baseline on `main` is 5 errors and 32 warnings, so a clean run over your own files does not mean a clean repo, and the existing errors are not yours to inherit blame for.
- Vitest (`frontend/**/*.{test,spec}.{ts,tsx}`), backend pytest (`backend/tests/`) and ingestion pytest (`services/ingestion/tests/`) run in `coverage.yml`, on pull requests only.
- Ruff runs in `backend.yml` (over `backend/app`) and `mcp.yml` (over `services/mcp/app` and its tests). MCP is the only package whose tests run in its own workflow.
- There is no formatter config, no pre-commit hook, and no repo-wide check. Style outside ESLint and Ruff is convention only.
