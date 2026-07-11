# ADR-020: Intelligence Gateway

**Date**: 2026-07-11
**Status**: Accepted
**Sprint**: 2 (T-025)

## Context

Every Discovery module (T-015–T-020) constructs its own mock provider
directly — `FlightIntelligence(provider=MockFlightProvider())`, and
identically for Accommodation, Destination, Budget, Visa, and Weather.
This was the right sequencing for Epic 2: six modules shipped
independently, each fully deterministic and testable in isolation, with
no premature abstraction for a live-vendor problem that didn't exist yet.

It leaves a real gap the business objective names directly: Tralvana
needs to switch between providers, use fallbacks, protect credentials,
control costs, and recover from provider failures — none of which any
Discovery module's direct `Mock*Provider()` construction can do.
**This task builds that infrastructure. It does not integrate a live
provider** — every provider registered by this task remains a wrapped
version of an already-existing mock.

## Decision

**Package location: `travelos/intelligence_gateway/`, not the task
brief's suggested `platform/intelligence_gateway/`.** The repository's
platform layer already exists at `travelos/` — SDK, DI container,
`ServiceRegistry`, `ConfigurationManager`, `EventBus`, `TravelLogger`
(T-011, `docs/PLATFORM_LAYER.md`). Creating a new top-level `platform/`
directory would fragment "platform infrastructure" into two
non-communicating concepts in the same repository, directly against
Engineering Principle #1 ("repository and current code are the source of
truth") and #5 ("reuse existing service interfaces"). The Intelligence
Gateway *is* platform-layer infrastructure by this task's own
description — it belongs alongside `travelos/config/`, `travelos/logging/`,
`travelos/registry/`, not in a parallel structure. Same class of judgment
call as T-023's finding that `ai/manager/`/`ai/registry/` couldn't be
retired as originally scoped: the instruction named a shape, the
repository's actual state determined where that shape actually belongs.

**One `Provider` contract, not one per capability.** Every provider —
mock today, live later — implements the same `execute()`/`supports()`/
`health_check()` interface regardless of capability. A capability
(Weather) needing multiple operations (`month`/`year`/`known_destinations`)
is expressed as `ProviderRequest.operation`, not as a different contract
shape. This keeps `ProviderRegistry`, `ProviderSelector`, and
`IntelligenceGateway` capability-agnostic — none of them need to know
anything about flights vs. weather.

**Two-layer Discovery integration, not a rewrite of any Discovery
module's internals.** `discovery_adapters.py` separates (1) a
gateway-contract wrapper around each existing `Mock*Provider` class,
registered in `provider_registry`, from (2) a drop-in adapter
(`Gateway*Provider`) matching each Discovery module's *existing* provider
constructor argument exactly. The only change to
`flight_intelligence.py`/`accommodation_intelligence.py`/`weather_intelligence.py`
is which object their bottom-of-file singleton passes to the constructor
— one line each. No scoring, reasoning, risk-assessment, or public API
response logic is touched. Proven behaviour-preserving by
`travelos/tests/test_discovery_adapters.py`'s byte-identical-output
assertions and the full 833-test suite passing unchanged.

**All three minimum-required providers (Flight, Accommodation, Weather)
were actually wired into their live singletons, not merely made
"accessible."** The task's own wording allows either ("use or are
accessible through the gateway"), and the safer-looking choice would
have been to prove the pattern with one adapter and leave the rest
merely registered. Given the adapters are provably byte-identical
pass-throughs and the existing 723-test suite (fully retained, all
passing) provides a strong regression net, the more complete integration
was chosen — a real example of every module the task named actually
running through the gateway's cache/retry/failover pipeline in
production code, not a parallel unused demonstration.

**Rate-limited providers raise, they don't return a `RATE_LIMITED`
result.** An early implementation had `IntelligenceGateway._call_provider`
return a `ProviderResult(status=RATE_LIMITED)` directly when a provider's
quota was exhausted. This was a bug, caught by
`travelos/tests/test_gateway.py`'s `TestRateLimitedFailover` case: since
`failover_policy.run_with_failover` only fails over on a *raised*
exception, a returned result — even one whose `status` says
`RATE_LIMITED` — was treated as a successful answer and returned
immediately, skipping every remaining eligible provider. Fixed by raising
`ProviderRateLimitedError` instead, letting the existing failover loop
handle it exactly like any other provider failure. `ProviderStatus.RATE_LIMITED`
remains meaningful as a `health_check()` return value and a diagnostic
signal — it just isn't how the gateway itself signals "try the next
provider" internally.

**No external retry, cache, or rate-limit library.** `requirements.txt`
has none, and the task explicitly says not to add one unless already
present. `RetryPolicy` is ~20 lines of stdlib `time.sleep` and exception
classification; `InMemoryCachePolicy`/`RateLimitTracker` are plain dicts
with TTL/window bookkeeping — matching the existing in-memory-store
convention already used throughout this codebase (`ConversationSession`'s
`_SessionStore`, in-memory Goal/Trip repositories).

**Diagnostics endpoint added at `GET /internal/providers/status`.** No
existing `/internal/` namespace precedent exists in this codebase, but
nothing in `docs/CODING_STANDARDS.md` or `docs/ARCHITECTURE.md` prevents
one, and no endpoint anywhere currently has authentication (T-031, Auth
layer, is still `planned`) — this endpoint introduces no new gap relative
to the rest of the API's current all-open state. Returns only capability,
provider name, environment, status/health, priority, cache TTL, and
rate-limit state — verified by
`services/api/tests/test_internal_diagnostics.py` that no secret,
credential, API key, password, or token string ever appears in the
response.

**Test location: new `travelos/tests/`, added to `pytest.ini`'s
`testpaths`.** The only prior test roots were `services/api/tests` and
`ai/tests`; the platform layer itself had none yet (tracked as open debt,
T-012A "Platform Layer Test Coverage", TD-015). Rather than misplace
gateway tests under `ai/tests/` (the gateway is platform infrastructure,
not AI-layer logic), `travelos/tests/` was created and registered — a
natural first step toward T-012A, not a scope expansion of it.

## Alternatives Considered

| Option | Rejected Because |
|--------|-------------------|
| Create `platform/intelligence_gateway/` exactly as suggested | Fragments the platform layer into two non-communicating concepts (`platform/` and `travelos/`) in the same repository — see Decision above |
| One `Provider` subclass hierarchy per capability (e.g. `FlightProvider`, `WeatherProvider` base classes) | Unnecessary abstraction for infrastructure that doesn't yet have more than one provider per capability; the generic `Provider` + `ProviderRequest.operation` shape already covers Weather's multi-operation need without it |
| Rewrite `FlightIntelligence`/`AccommodationIntelligence`/`WeatherIntelligence` to call the gateway directly instead of going through a `provider` constructor argument | Touches scoring/reasoning code this task has no reason to touch, and breaks the "preserve current public Discovery service interfaces" constraint for no benefit — the existing `provider=` injection point already does exactly what's needed |
| Register only one gateway-backed provider (e.g. Flight) as a "proof of pattern," leave Accommodation/Weather merely accessible but not wired | More conservative, but the task explicitly asks for all three "at minimum," and the byte-identical-output tests plus full regression suite made the complete integration low-risk enough to just do properly |
| Add Redis for caching / rate limiting now, since it's clearly coming eventually | Explicitly forbidden by this task's constraints ("No Redis yet," "No distributed rate limiter") |
| Skip the diagnostics endpoint, since no `/internal/` precedent exists | The task explicitly asks for it "if consistent with current conventions," and nothing in the current API structure actually prevents it — documented as a considered-and-taken option, not a forced one |
| Return a `RATE_LIMITED` `ProviderResult` instead of raising, to make the "RATE_LIMITED status" requirement more directly visible | Broke failover — a returned result is treated as success by the failover loop regardless of its `status` field. Raising an exception is what actually triggers "try the next provider," which the requirement also explicitly asks for ("failover when possible") |

## Consequences

- `travelos/intelligence_gateway/` — 12 new files (11 named in the task
  brief plus `__init__.py`), zero new third-party dependencies.
- `travelos/config/configuration_manager.py` gains five additive
  properties/methods — no existing property changed.
- `ai/discovery/{flights,accommodation,weather}/*_intelligence.py` — one
  singleton-construction line changed each, proven behaviour-preserving.
- `services/api/app/routers/internal.py` (new) and one `main.py` include
  line — purely additive to the API surface.
- `pytest.ini` gains `travelos/tests` as a third test root.
- `.env.example`, `README.md` updated with placeholders and structure
  notes — no real credential added anywhere.
- 833 tests pass (723 pre-existing + 110 new), Ruff clean.
- Destinations, Budget, Visa, Maps, Currency, Events remain unintegrated
  — tracked as deferred, documented in `docs/INTELLIGENCE_GATEWAY.md` and
  `docs/TECHNICAL_DEBT_REGISTER.md`, not a technical blocker.
