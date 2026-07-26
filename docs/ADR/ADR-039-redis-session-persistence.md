# ADR-039: Redis Conversation Session Persistence

**Status:** Accepted

**Date:** 2026-07-26

**Task:** T-035

## Context

`ConversationEngine` stored every `ConversationSession` in a dictionary owned
by one Python process. A follow-up routed to another worker could not recover
its history, planning facts, linked Goal/Trip, or explanation state. T-034
persisted Goals and Trips in PostgreSQL but deliberately left conversation
sessions for this task.

## Decision

Introduce a `SessionStore` contract with two adapters:

1. `InMemorySessionStore` when `REDIS_URL` is absent.
2. `RedisSessionStore` when `REDIS_URL` is explicitly configured and reachable.

The Redis adapter uses versioned JSON, a seven-day configurable TTL, and a
transactionally maintained Trip-ID index. `ConversationEngine` accepts a store
through its constructor, while the application singleton uses the
configuration-selected adapter.

A configured Redis connection is tested before use. Failure raises a
credential-safe configuration error; the application does not silently fall
back to per-process memory.

## Consequences

- Conversation and explanation continuity can survive worker and instance
  changes.
- Local development and CI still require no Redis server.
- Redis records expire and are not a permanent traveller-history archive.
- A managed Redis service and private `REDIS_URL` are still required before
  horizontal production scaling.
- The adapter adds `redis-py` as a runtime dependency.

## Alternatives considered

### Store conversations in PostgreSQL

Rejected for this short-lived state. It would add relational migrations and
write amplification for high-churn session history, while Redis directly
supports expiry and atomic key/index updates.

### Pickle the Python dataclasses

Rejected because pickle couples records to implementation details and can
execute code while deserializing untrusted data. Versioned JSON is explicit,
portable, and inspectable.

### Fall back to memory when Redis fails

Rejected when `REDIS_URL` is configured. Different workers could then serve
different versions of the same session without any visible error.

### Scan all session keys to find a Trip ID

Rejected because lookup time would grow with the number of sessions. A
same-TTL index provides constant-time resolution.
