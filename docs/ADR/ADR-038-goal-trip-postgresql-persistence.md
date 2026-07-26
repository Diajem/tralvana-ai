# ADR-038: Goal and Trip PostgreSQL Persistence

**Status:** Accepted
**Date:** 2026-07-26
**Task:** T-034

## Context

Goals and Trip Plans were stored in module-level dictionaries. Restarting the
API erased them and multiple API workers could not share state.

Tralvana already has a production SQLAlchemy base, PostgreSQL/Psycopg URL
normalisation, Alembic migrations, startup migration execution, and readiness
gating from T-042–T-046. A second persistence stack would duplicate solved
infrastructure.

## Decision

- Add SQLAlchemy rows and adapters for Goals and Trip Plans.
- Reuse the existing `DATABASE_URL`, engine factory, session factory, Base,
  Alembic chain, and deployment readiness gate.
- Store existing nested domain structures in JSON without changing their
  public shape.
- Use transactional repository writes and short-lived read sessions.
- Select persistent adapters when `DATABASE_URL` is configured.
- Retain in-memory adapters only when it is absent.
- Advance the expected production schema from `0003` to `0004`.
- Do not introduce a Goal-to-Trip database foreign key yet; legacy and
  conversation-created trips may legitimately carry no goal, and Goal
  lifecycle policy has not defined cascade behaviour.

## Consequences

- Goals and Trips survive restarts and are visible across workers.
- Local development and CI remain zero-setup without a database.
- Production cannot report ready until migration `0004` succeeds.
- Existing ephemeral records have no durable source from which to backfill.
- Traveller-profile and conversation persistence remain separate work.

## Rejected alternatives

| Alternative | Reason |
|---|---|
| Add a second ORM/database package | Duplicates the existing production stack |
| Use SQLite files in production | Conflicts with the established managed PostgreSQL deployment |
| Keep dictionaries and snapshot them | Still unsafe across workers and process crashes |
| Force PostgreSQL for every test | Removes the current fast zero-setup development path |
| Add cascading Goal foreign keys now | Deletion and archival policy is not yet defined |
