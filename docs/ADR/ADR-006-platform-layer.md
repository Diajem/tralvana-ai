# ADR-006: TravelOS Platform Layer

**Date**: 2026-07-08
**Status**: Accepted
**Sprint**: 2 (foundational)

## Context

After Sprint 1 (T-004â€“T-009), TravelOS had 7 working services with no shared infrastructure:
- Each service imported Python's `logging` directly with inconsistent formats
- Configuration was read from `os.environ` in scattered places across `main.py`, service files, and reasoners
- No common error type â€” services returned raw dicts, booleans, exceptions, or mixed
- No event system â€” cross-service side effects were implemented as direct calls (coupling)
- No dependency injection â€” singletons were instantiated at module load time with hardcoded imports
- No public API contract â€” callers could import any internal module directly

The T-010 audit identified this as a scalability risk: adding services would increase coupling, making Sprint 3 (persistence, auth, horizontal scaling) difficult.

## Decision

Build a platform layer at `travelos/` â€” a zero-external-dependency internal library that provides:

1. **SDK** (`TravelOS`) â€” stable public interface; 9 methods cover all current capabilities
2. **ServiceRegistry** â€” lazy resolution of 7 core services by canonical name
3. **ConfigurationManager** â€” environment-aware config (dev/test/prod) + env var overrides
4. **TravelLogger** â€” structured, named logger wrapping Python's stdlib `logging`
5. **EventBus** â€” synchronous pub/sub; `DomainEvent` base + 6 concrete event types
6. **ServiceContainer** â€” lightweight DI container (register/singleton/resolve)
7. **Shared types** â€” `Result[T]`, `Error`, `Identifier`, `Timestamp`, `Pagination`, `Page`, `BaseRepository`, `BaseService`

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| Add a third-party DI framework (`dependency-injector`) | External dep, learning curve, overkill for 7 services |
| Use FastAPI's `Depends()` for DI | Couples platform DI to HTTP layer; unusable from AI layer |
| Async EventBus (asyncio) | Complicates non-async callers; deferred to Sprint 3 with Redis |
| Put platform inside `services/api/` | Not shareable with `ai/` layer; defeats the OS goal |
| Wrap stdlib logging with structlog | External dep; overkill before we have a log aggregator |

## Consequences

- The platform layer adds zero new packages to `requirements.txt`
- `travelos/` is importable from the project root alongside `ai/` and `services/`
- Existing APIs are unchanged â€” platform layer is additive
- New services should extend `BaseService` and use `TravelLogger`, `Result`, `Identifier`
- Sprint 3 services register in `ServiceRegistry` and `ServiceContainer` instead of creating global singletons
- `EventBus` is the prescribed way to notify other services of domain changes â€” replaces the current pattern of direct cross-service calls

## Known Limitations

- `travelos/` is a Python package named `platform`, which shadows the stdlib `platform` module. Existing code that does `import platform` (for OS detection) will need to use `import sys; sys.platform` instead. This is acceptable as we don't use stdlib `platform` anywhere currently.
- The EventBus is synchronous â€” long-running handlers will block the publisher. All current handlers are fast (logging, in-memory writes). Sprint 3 replaces with async.
- `ServiceRegistry` uses `importlib.import_module` with hardcoded path strings. If a service moves, the registry must be updated.

## Sprint 3+ Evolution

| Component | Sprint 3 Change |
|-----------|----------------|
| EventBus | Async, Redis Streams backed |
| ServiceRegistry | Service mesh / sidecar discovery |
| ConfigurationManager | Vault / AWS SSM adapter |
| ServiceContainer | Evaluate `dependency-injector` if >20 services |
| BaseRepository | Swap in-memory â†’ SQLAlchemy async adapters |
