# ADR-007: Testing Framework

**Date**: 2026-07-08
**Status**: Accepted
**Sprint**: 2 (T-012)

## Context

TravelOS had zero test coverage entering Sprint 2. The T-010 audit flagged this as high risk (TD-005). The codebase has two distinct layers:

1. **Backend API** (`services/api/`) — FastAPI endpoints over in-memory stores
2. **AI Layer** (`ai/`) — Rule-based classifiers, planners, and agent registry

Both layers needed coverage before Sprint 3 introduces persistence and authentication.

## Decision

**pytest** — the standard Python test runner. No additional framework.

**FastAPI TestClient** — from `starlette.testclient`, wraps async FastAPI handlers in a synchronous interface. No `pytest-asyncio` required, no async complexity, no event-loop boilerplate.

**No mocks** — all data stores are in-memory singletons. Mocking them adds maintenance overhead and tests the scaffolding, not the behaviour. In-memory stores are fast (sub-millisecond) and deterministic. The T-010 audit explicitly called out mock-based tests as a risk (past incident where mocked tests passed but a real integration failed).

**pythonpath in pytest.ini** — instead of sys.path manipulation in conftest.py, use pytest's built-in `pythonpath` setting. This makes `app.*` (from `services/api/`) and `ai.*` (from project root) both importable without collision.

**Single test root** — `pytest.ini` at the project root collects both `services/api/tests/` and `ai/tests/` in one run. Avoids two separate CI steps.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| `pytest-asyncio` | Needed only if test functions are async; TestClient handles async endpoints synchronously |
| `unittest.mock` / `MagicMock` | Mocks add test-code coupling; in-memory singletons are already fast enough |
| Separate pytest configs per layer | Two CI steps for one test suite; pytest.ini `pythonpath` solves the import collision cleanly |
| Factory Boy / Faker for fixtures | Overkill for Sprint 2; conftest fixtures are 20 lines total |
| Hypothesis (property testing) | Deferred to Sprint 3 when AI classification moves to LLM; rule-based classifiers have deterministic inputs |

## Consequences

- `pip install pytest httpx` is the only test dependency beyond existing requirements
- Running `pytest` from the project root runs all 92 tests in ~0.3 seconds
- Tests are purely in-memory — no database, no network, no API keys
- When Sprint 3 swaps in-memory stores for PostgreSQL, the integration test layer will need a separate `pytest-postgres` or Docker-compose fixture — plan for this in T-019
- AI tests will break if the rule-based classifiers are replaced by LLM-backed ones; update them alongside the classifier changes

## Sprint 3+ Evolution

| Current | Sprint 3 |
|---------|----------|
| In-memory fixtures | PostgreSQL fixtures via `pytest-postgres` or `testcontainers` |
| Rule-based AI tests | Prompt-level AI tests with golden-set assertions |
| No auth tests | Auth flow tests (JWT, API keys) in T-018 |
| No load tests | Locust/k6 benchmarks in T-023 |
