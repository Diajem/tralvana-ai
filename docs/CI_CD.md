# CI/CD

T-013 — GitHub Actions pipeline for TravelOS.

## Overview

`.github/workflows/ci.yml` runs on every push to `main` and every pull request targeting `main`. Three independent jobs:

| Job | Command | Gate |
|-----|---------|------|
| `backend-tests` | `pytest -v` | **Required** — must pass to merge |
| `backend-lint` | `ruff check .` | **Required** |
| `frontend` | `npm run lint` && `npm run build` (in `apps/web/`) | **Required** |

ADR-008 records the original advisory rollout. T-014 cleared TD-016 and TD-017; T-041 removed `continue-on-error`, so failures now block the workflow.

## Versions

Pinned to what the repository's own Dockerfiles already use — not chosen independently:

- Python **3.12** (`services/api/Dockerfile`)
- Node **22** (`apps/web/Dockerfile`)

## Reproducible frontend install

T-041 added `apps/web/package-lock.json`. CI and the frontend Docker image use `npm ci`, so dependency resolution is identical across clean builds.

## Required jobs

`backend-tests`, `backend-lint`, and `frontend` must all succeed. Repository branch protection should also name them as required checks so GitHub prevents a failing change from merging.

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
npm ci
npm run lint
npm run build
```
