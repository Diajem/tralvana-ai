# ADR-008: CI/CD Pipeline

**Date**: 2026-07-08
**Status**: Accepted
**Sprint**: 2 (T-013)

## Context

T-012 established a 92-test pytest suite, but nothing ran it automatically. A green local test run is not a guarantee — nothing stopped a PR with a failing test, an unformatted file, or a broken frontend build from merging to `main`.

Reviewing the repository before implementing surfaced two pre-existing issues that any CI gate would immediately trip over:

1. **Backend**: `ruff check .` reports 72 violations across the existing codebase (mostly `E701` multiple-statements-on-one-line and unused imports). Ruff itself was never added to `requirements.txt` or run before this task — `CODING_STANDARDS.md` names it as the intended enforcement tool, but it was never wired up.
2. **Frontend**: `npm run lint` and `npm run build` currently fail outright on `main`. `apps/web/src/lib/api.ts` has an `eslint-disable-next-line @typescript-eslint/no-explicit-any` comment, but `apps/web/.eslintrc.json` only extends `next/core-web-vitals` and never registers the `@typescript-eslint` rule namespace, so ESLint errors before it evaluates anything else.

Neither issue was introduced by this task, and fixing application code is out of scope for "add CI/CD." Both are logged as debt (TD-016, TD-017).

## Decision

**GitHub Actions**, single workflow at `.github/workflows/ci.yml`, triggered on push to `main` and on every pull request targeting `main`. Three independent jobs:

| Job | Runs | Gate |
|-----|------|------|
| `backend-tests` | `pytest -v` (92 tests: `services/api/tests/` + `ai/tests/`) | **Required** — currently 100% green |
| `backend-lint` | `ruff check .` | Advisory (`continue-on-error: true`) until TD-017 is cleared |
| `frontend` | `npm run lint` + `npm run build` in `apps/web/` | Advisory (`continue-on-error: true`) until TD-016 is fixed |

**Versions pinned to what the repo already uses** — Python 3.12 (matches `services/api/Dockerfile`), Node 22 (matches `apps/web/Dockerfile`). No version was invented; both come from existing Dockerfiles.

**`npm install`, not `npm ci`** — `apps/web/` has no `package-lock.json` committed (matches what `apps/web/Dockerfile` already does). `npm ci` requires a lockfile and would fail immediately.

**Only `backend-tests` is a hard gate for now.** Turning on `ruff` and frontend `lint`/`build` as required checks today would make every single PR fail immediately for reasons unrelated to that PR's changes — that's noise, not signal, and directly contradicts "keep the platform simple, avoid over-engineering." They still run and report on every PR (visibility from day one), just don't block merges yet.

## Alternatives Considered

| Option | Rejected Because |
|--------|-------------------|
| Make all three jobs required immediately | Blocks all future PRs on 72 pre-existing lint violations + a broken ESLint config unrelated to the PR's own changes |
| Fix TD-016/TD-017 as part of this task | Out of scope — T-013 is "add CI/CD," not "clean up lint debt"; that's T-014 (repository refactoring) |
| Skip lint jobs entirely until debt is cleared | Loses visibility — advisory jobs still surface regressions and track progress toward zero violations |
| `npm ci` for reproducible frontend installs | No lockfile exists in the repo; would fail on first run. Revisit once `package-lock.json` is committed |
| Matrix test across multiple Python/Node versions | Unneeded complexity — the repo only targets the versions pinned in its own Dockerfiles |

## Consequences

- `pytest` failures now block merge — the first real CI safety net for the repository.
- Ruff and frontend lint/build results are visible on every PR without blocking anyone — pressure to fix TD-016/TD-017 is now visible in CI output rather than invisible.
- Once TD-017 (Ruff violations) is cleared in T-014, remove `continue-on-error: true` from `backend-lint` and mark it required in GitHub branch protection.
- Once TD-016 (ESLint config) is fixed, remove `continue-on-error: true` from `frontend` and mark it required.
- Branch protection rules (marking `backend-tests` as a required status check on `main`) are a GitHub repository setting, not a file in this repo — that configuration step is a manual follow-up, not something this ADR can enforce by itself.

## Sprint 3+ Evolution

| Component | Sprint 3 Change |
|-----------|-------------------|
| `backend-lint` / `frontend` jobs | Flip to required once TD-016/TD-017 are resolved |
| Test matrix | Add if the platform ever needs to support more than one Python/Node version |
| Frontend tests | Add a `vitest` job once `apps/web` actually has tests (`CODING_STANDARDS.md` names `vitest`, but no test files or dependency exist yet) |
| Deploy step | Add on merge to `main` once T-018 (deployment infra) exists |
