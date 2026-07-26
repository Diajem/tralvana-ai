# ADR-043: Promote Traveller Profiles into a Cohesive Domain

**Status:** Accepted

**Date:** 2026-07-26

**Task:** T-030

## Context

Traveller profiles predated Tralvana's domain package convention. Their
Pydantic schemas, router, repository, and service were split across top-level
`app/models`, `app/routers`, and `app/services` paths. Goals, Trips, and all
Discovery capabilities already use cohesive `app/domains/<name>/` packages.

The old location made ownership unclear and forced the SDK and lazy service
registry to depend on exceptional import paths.

## Decision

- Create `app/domains/traveller/` with explicit `models`, `schemas`,
  `repository`, `service`, and `router` modules.
- Represent stored profiles with a typed `TravellerProfile` dataclass.
- Keep the zero-setup in-memory repository and existing module-level service
  composition.
- Preserve both public routes and their response shapes:
  - `POST /traveller/profile`
  - `GET /traveller/profile/{traveller_id}`
- Update the API composition root, TravelOS SDK, and service registry to the
  canonical domain paths.
- Remove the superseded top-level Traveller modules.
- Replace mutable Pydantic defaults with factories without changing their
  serialized values.

## Consequences

- Traveller now follows the same ownership structure as Goals and Trips.
- Public HTTP and SDK behaviour are unchanged.
- Domain service/repository behaviour can be tested without the global API
  client or shared singleton state.
- Traveller persistence remains deliberately out of scope. The in-memory
  repository is now isolated behind the correct boundary for a future SQL
  adapter.

## Rejected alternatives

### Keep compatibility modules at the old paths

Rejected because repository-wide reference checks found no external caller in
this codebase, and retaining wrappers would preserve two canonical locations.

### Add PostgreSQL Traveller persistence in the same task

Rejected because T-030 is a structural ownership refactor. Persistence changes
runtime data lifetime and deserves its own migration, readiness, and privacy
review.
