# CI/CD

T-013 — GitHub Actions pipeline for TravelOS.

## Overview

`.github/workflows/ci.yml` runs on every push to `main` and every pull request targeting `main`. Three independent jobs:

| Job | Command | Gate |
|-----|---------|------|
| `backend-tests` | `pytest -v` | **Required** — must pass to merge |
| `backend-lint` | `ruff check .` | Advisory — see TD-017 |
| `frontend` | `npm run lint` && `npm run build` (in `apps/web/`) | Advisory — see TD-016 |

See [ADR-008](ADR/ADR-008-cicd-pipeline.md) for the full decision record, including why the lint/build jobs are advisory rather than required today.

## Versions

Pinned to what the repository's own Dockerfiles already use — not chosen independently:

- Python **3.12** (`services/api/Dockerfile`)
- Node **22** (`apps/web/Dockerfile`)

## Why `npm install` and not `npm ci`

`apps/web/` has no committed `package-lock.json`. `npm ci` requires a lockfile and fails without one. `apps/web/Dockerfile` already uses `npm install` for the same reason — the workflow matches existing practice rather than introducing a new one.

## Advisory jobs

`backend-lint` and `frontend` run `continue-on-error: true`. Both would fail immediately today for reasons unrelated to any given PR's changes:

- **TD-017**: 72 pre-existing Ruff violations in the backend/AI codebase.
- **TD-016**: a broken ESLint rule reference in `apps/web/src/lib/api.ts` that fails `npm run lint` and `npm run build` on unmodified `main`.

Making either required now would block every PR on unrelated pre-existing debt. Both jobs still run and report on every PR — the failures are visible, just not blocking. Once T-014 (repository refactoring) clears TD-016/TD-017, remove `continue-on-error: true` from the relevant job and mark it as a required status check in GitHub branch protection settings.

## Branch protection

Marking `backend-tests` as a required check on `main` is a GitHub repository setting (Settings → Branches → Branch protection rules), not something `ci.yml` can enforce on its own. This is a manual one-time setup step, not covered by this task.

## Local equivalent

```bash
# Backend tests (same as CI)
pytest -v

# Backend lint (same as CI)
pip install ruff
ruff check .

# Frontend lint + build (same as CI)
cd apps/web
npm install
npm run lint
npm run build
```
