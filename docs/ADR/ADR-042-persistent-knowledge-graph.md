# ADR-042: Persist Travel Knowledge in the Existing Relational Stack

**Status:** Accepted

**Date:** 2026-07-26

**Task:** T-029

## Context

Tralvana's 199-node, 205-edge travel graph was rebuilt in memory on every
process start. Runtime additions reached itinerary generation after T-028 but
disappeared on restart and could differ across API workers.

The original T-029 backlog selected Kuzu. Kuzu's maintainers archived the
project on 10 October 2025 and no longer actively support it. Meanwhile,
Tralvana already operates a PostgreSQL/SQLAlchemy/Alembic foundation for its
commercial ledger, Goals, and Trips.

## Decision

- Preserve `KnowledgeService` as the only caller-facing graph boundary.
- Keep `KnowledgeGraph` as the zero-setup in-memory adapter when
  `DATABASE_URL` is absent.
- Add `SqlAlchemyKnowledgeGraph` when `DATABASE_URL` is configured.
- Store typed dataclass payloads as JSON nodes and typed directed
  relationships as indexed edge rows.
- Use stable node IDs and deterministic edge keys for transactional,
  idempotent baseline upserts.
- Move the SQLAlchemy base/session helpers into `travelos.persistence` and
  retain API compatibility imports, allowing AI persistence without reversing
  the T-036 API-to-AI dependency rule.
- Advance Alembic and production readiness to revision `0005`.
- Treat a configured database as authoritative and fail clearly when it is
  unavailable or unmigrated.

## Consequences

- Runtime knowledge survives restarts and is shared across workers.
- Existing reasoners and itinerary consumers do not change.
- Local/test use remains fast and database-free by default.
- Tralvana has one production database, migration chain, and readiness gate.
- SQL traversal currently performs bounded application-level graph walks.
  This is appropriate for the small curated graph; a specialised graph backend
  remains replaceable behind `KnowledgeService` if measured scale requires it.
- Exact duplicate relationships collapse to one persistent edge, preventing
  baseline duplication across repeated startup.

## Rejected alternatives

### Add archived Kuzu releases

Rejected because an unsupported core database is an avoidable operational and
security risk.

### Add Neo4j or another hosted graph service now

Rejected because current graph size and traversal patterns do not justify a
second service, credential, deployment path, or recurring cost.

### Persist only runtime additions

Rejected because it creates two sources of truth and makes reads depend on
merging an in-memory baseline with a separate mutation store.
