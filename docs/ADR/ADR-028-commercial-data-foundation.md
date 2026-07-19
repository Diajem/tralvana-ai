# ADR-028: Commercial Data Foundation

**Date**: 2026-07-19

**Status**: Accepted

**Task**: T-042

## Context

Tralvana can recommend live sandbox inventory but has no durable model for a
commercial partner, affiliate programme, attributed click, conversion, or
commission. Adding booking buttons before that audit trail exists would make
revenue reconciliation and disclosure unreliable. Existing Goal and Trip
repositories are in-memory and their broader migration is already assigned to
T-034.

## Decision

1. Introduce SQLAlchemy 2 and Alembic with PostgreSQL through Psycopg 3.
2. Keep pure commercial domain entities separate from ORM rows and access them
   through a repository contract and SQLAlchemy adapter.
3. Model clicks, conversions, and commissions as separate records. A commission
   is not collapsed into a conversion because approval, rejection, adjustment,
   and payment have their own lifecycle.
4. Link to current Trip and recommendation objects by nullable string reference,
   avoiding a premature database migration of domains owned by T-034.
5. Store only an already-hashed anonymous session reference for attribution and
   reject raw personal-data columns from the click schema.
6. Expose only read-only, non-secret readiness metadata. Public redirect,
   booking, webhook, payment, and administrative mutations remain out of scope.
7. Use SQLite solely as a deterministic CI test dialect; deploy with PostgreSQL.

## Consequences

- Tralvana has a migration-controlled commercial audit trail before any
  traveller-facing monetisation action is introduced.
- Foreign keys, uniqueness rules, decimal values, and non-negative constraints
  protect the ledger at the database boundary.
- T-034 remains independently deliverable and can later replace the temporary
  Trip references with real relational links.
- A later task must implement authenticated partner administration, signed
  redirect/click capture, idempotent conversion webhooks, reconciliation, and
  customer-facing disclosures before commission stage is complete.
