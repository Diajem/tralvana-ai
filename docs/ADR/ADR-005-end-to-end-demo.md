# ADR-005: End-to-End Demo Layer

**Date**: 2026-07-08
**Status**: Accepted
**Sprint**: 1

## Context

After T-006 through T-008 built the individual layers of TravelOS (Knowledge, Goals, Trips), we needed a way to demonstrate the full pipeline end-to-end — both for stakeholder validation and as a living integration test.

## Decision

Build a thin demo layer (`services/api/app/demo/`) that wires all existing singletons together under one endpoint. The scenario is hardcoded (Japan Football & Food) to guarantee reproducibility.

Key principles:
1. **Zero new logic** — the demo calls the same singletons as the live API. No mock shortcuts.
2. **Sequential execution** — each stage completes before the next begins (not parallel), so failures are easy to trace.
3. **One response** — the full pipeline output in a single JSON object so clients can render it without further requests.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| Unit tests | Don't show the pipeline to stakeholders; don't catch integration gaps |
| Storybook / static fixture | Not real data; doesn't exercise the actual services |
| Separate demo microservice | Adds deployment overhead; can't share in-memory singletons |
| Multiple chained API calls from frontend | More complex; race conditions; harder to debug |

## Consequences

- The demo endpoint is idempotent (creates a new Goal and Trip Plan on each call)
- Demonstrates all 7 stages in < 1 second (no I/O, all in-memory)
- Serves as a living integration test — if any upstream service breaks, the demo fails
- Frontend page at `/demo` gives non-technical stakeholders a clickable demo

## Sprint 3+ Evolution

When the Knowledge Graph is replaced by Kuzu and Goals/Trips move to PostgreSQL:
- `DemoService` requires no changes — it calls service facades, not infrastructure
- Only the underlying singleton implementations change
