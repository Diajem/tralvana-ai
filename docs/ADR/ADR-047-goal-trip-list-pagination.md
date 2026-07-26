# ADR-047: Bound Goal and Trip List Endpoints

**Status:** Accepted

**Date:** 2026-07-26

**Task:** T-059

## Context

`GET /traveller/{traveller_id}/goals` and
`GET /traveller/{traveller_id}/trips` returned every matching record. This was
acceptable for early in-memory stores but became an unbounded database query
after T-034 added PostgreSQL persistence.

## Decision

- Add `limit` and `offset` query parameters to both endpoints.
- Default `limit` to 100, constrain it to 1–100, and require `offset >= 0`.
- Keep the existing plain-list response shape.
- Apply deterministic `(created_at, id)` ordering before SQL pagination.
- Mirror the same insertion ordering and slicing in the in-memory adapters.
- Keep service/repository `limit=None` available for trusted internal callers
  that explicitly need all records.

## Consequences

- Public requests cannot issue unbounded Goal or Trip list queries.
- Existing clients that omit pagination still receive a list, capped at 100.
- Invalid bounds fail validation with HTTP 422.
- In-memory and PostgreSQL behaviour remain aligned.

## Rejected alternatives

### Introduce a paginated response envelope

Rejected for this task because it would break the established list response
shape. A future cursor/metadata API can be added under a versioned contract.

### Slice results only in the router

Rejected because PostgreSQL would still load every matching row before the
slice, leaving the production risk unresolved.
