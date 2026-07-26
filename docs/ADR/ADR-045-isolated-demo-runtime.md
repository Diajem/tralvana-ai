# ADR-045: Isolate the End-to-End Demo Runtime

**Status:** Accepted

**Date:** 2026-07-26

**Task:** T-057

## Context

`POST /demo/japan-football-food` exercised the real Goal, conversation, and
Trip planning services, but it used their application singletons. Every demo
click therefore created Goals, Trips, and a conversation session in the same
stores used by normal API requests. After PostgreSQL and Redis support were
added, a public demonstration could persist synthetic traveller data.

The demo must remain a living integration test of real domain and planning
logic without becoming a source of production records.

## Decision

- Construct fresh `GoalRepository`, `TripRepository`, and
  `InMemorySessionStore` instances for every demo request.
- Build normal `GoalService` and `TripPlanningService` instances on those
  repositories rather than adding demo-specific domain implementations.
- Extend `PlanningAdapter` with optional Goal/Trip service injection while
  retaining lazy application-singleton defaults.
- Allow `TripPlanningService` to receive its Goal service, preventing its
  conversation helper from escaping to the global singleton.
- Allow `ConversationEngine` to receive a request-scoped `TripBrain`, whose
  `ContextBuilder` reads the same isolated planning adapter.
- Discard the isolated runtime after the response is assembled.
- Preserve the demo endpoint and seven-stage response contract.

## Consequences

- Demo Goals, Trips, and sessions never enter PostgreSQL, Redis, or shared
  in-memory application stores.
- Repeated demo requests do not accumulate state.
- The demo still runs the production Goal, Trip Planner, Conversation Engine,
  Trip Brain, and response-composition code.
- No `is_demo` field, migration, filtering rule, or cleanup deletion is
  required.
- A regression test snapshots all three shared stores and proves they remain
  unchanged after a demo request.

## Rejected alternatives

### Mark persisted records with `is_demo`

Rejected because it still writes synthetic records to production storage and
requires every reader, report, migration, and future query to remember the
filter.

### Delete demo records after each request

Rejected because partial failure can skip cleanup, concurrent requests make
ownership harder, and cleanup adds unnecessary destructive operations.

### Replace the pipeline with static fixture output

Rejected because the endpoint would stop serving as an end-to-end integration
check of the real planning stack.
