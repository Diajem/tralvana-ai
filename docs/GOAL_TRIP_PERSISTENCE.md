# Goal and Trip Persistence — T-034

T-034 moves Travel Goals and Trip Plans from process-local dictionaries to the
same SQLAlchemy/Alembic/PostgreSQL foundation already used by Tralvana's
commercial ledger.

## Runtime selection

- With `DATABASE_URL` configured, `goal_service` uses
  `SqlAlchemyGoalRepository` and `trip_planning_service` uses
  `SqlAlchemyTripRepository`.
- Without `DATABASE_URL`, both services retain their deterministic in-memory
  adapters for zero-setup local development and tests.

The selection occurs at application composition time. Merely importing a
repository or running a unit test does not open a database connection.

## Schema

Alembic revision `0004` adds:

- `travel_goals`, indexed by traveller and status; and
- `trip_plans`, indexed by traveller, goal reference, and status.

Nested planning structures are stored as JSON because they are already
provider-neutral domain values: budgets, timeframes, traveller counts,
interests, assumptions, itinerary days, risks, recommendation metadata, and
budget breakdowns.

Public IDs and ISO timestamps retain their existing string representation, so
the REST contracts and service outputs do not change.

## Transactions

Every persistent repository write runs in a SQLAlchemy transaction:

- Goal save, update, and delete;
- Trip save and update.

Reads open short-lived sessions and return detached domain dataclasses. A new
repository instance can reload records written by an earlier instance, proving
the data is not process-local.

## Deployment

Production startup already runs:

```bash
alembic -c services/api/alembic.ini upgrade head
```

The readiness gate now expects schema revision `0004`. It will reject traffic
when a deployment is still on `0003`.

Existing in-memory Goal/Trip records cannot be migrated because they were
ephemeral and disappeared whenever the old process stopped. This migration
preserves all existing commercial tables and data.

## Boundaries

T-034 does not persist traveller profiles or conversation sessions; those
remain separate backlog items. It also does not change planning, scoring,
provider selection, booking, or payment behaviour.
