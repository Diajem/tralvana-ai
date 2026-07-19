# ADR-027: Launch Stabilisation

**Date**: 2026-07-18

**Status**: Accepted

**Task**: T-041

## Context

T-040 delivered a working planner, but the documented backend command lost
access to repository-level packages after changing into `services/api`, the API
Docker image copied only that subdirectory, the web app conflicted with
Luxorahut POS on port 3000, dependencies were not locked, and CORS was hardcoded.

## Decision

1. Keep the existing Next.js 15 architecture and use the current patched
   `15.5.20` backport rather than taking an unnecessary Next 16 migration.
2. Standardise local ports on web `3001` and API `8000`.
3. Launch the API from the repository root with root and `services/api` on
   `PYTHONPATH`; use the same module layout in Docker.
4. Read CORS origins through `ConfigurationManager`, with an environment
   override and a development default of `http://localhost:3001`.
5. Add PowerShell launchers for the user's Windows workflow.
6. Commit the npm lockfile, use `npm ci` in CI, and make backend lint and
   frontend build failures blocking.

## Consequences

- The planner is repeatably runnable without using port 3000.
- Clean environments can import `app`, `ai`, and `travelos` correctly.
- Docker receives all three code roots required by the API.
- No public API, scoring, provider, booking, payment, or affiliate behaviour changes.
- Docker-engine execution remains a machine-level verification step because the
  audit environment does not provide Docker.
