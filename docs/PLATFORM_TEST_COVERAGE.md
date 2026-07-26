# Platform Test Coverage — T-012A

T-012A completes direct automated coverage for the foundational `travelos/`
modules introduced by T-011.

## Scope

The new tests verify public behaviour for:

- `TravelOS` SDK validation and service delegation;
- lazy and manual `ServiceRegistry` resolution;
- environment and provider-mode configuration;
- domain-event serialisation and synchronous Event Bus delivery;
- structured service logging;
- dependency-container instance, singleton, child, and reset semantics;
- repository pagination and base-service identity; and
- Result, Error, Identifier, Timestamp, Pagination, and Page value contracts.

Existing Intelligence Gateway and live-provider tests remain separate under the
same `travelos/tests/` root.

## Isolation

Platform tests:

- make no real network request;
- require no API key or `.env`;
- use no database or filesystem persistence;
- add no runtime or test dependency; and
- do not modify production behaviour.

The async SDK boundary is exercised with `asyncio.run`, preserving the
repository's deliberate decision not to require an async pytest plugin.

## Commands

```bash
# Direct T-012A scope
pytest travelos/tests/test_platform_*.py

# Complete repository
pytest
ruff check .
```

Frontend lint and production build remain required even though T-012A changes
no frontend source.

## Acceptance

- 67 new direct platform tests pass.
- 1,371 repository tests pass.
- Ruff passes.
- Frontend lint and production build pass.
- TD-015 is resolved.
