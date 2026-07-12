# ADR-021: Live Provider Framework

**Date**: 2026-07-12
**Status**: Accepted
**Sprint**: 2 (T-026)

## Context

T-025 built the Intelligence Gateway — a `Provider` contract, registry,
deterministic selector, cache, retry, and failover policy — but every
provider registered against it is a wrapped mock. Nothing in the
codebase yet defines the shape a real vendor integration (flight search,
weather, maps, ...) must follow: how it authenticates, maps requests,
handles a vendor's error responses, or reports health. Without that
shape, every future live integration reinvents its own version of all of
it. T-026 builds that shape once, as a reusable base — **it does not
connect to any real external API**.

## Decision

**`BaseLiveProvider` is a `Provider` subclass, not a parallel type.**
`travelos.intelligence_gateway.provider_contract.Provider` is the one
contract both mock (T-025) and live (T-026) providers implement.
`BaseLiveProvider.execute()` is a template method — a concrete provider
only implements `build_request()`/`parse_response()`; authentication,
HTTP-status error mapping, metrics, tracing, and logging are handled
once, here. This is the same architectural move ADR-020 made for the
Intelligence Gateway relative to the Discovery Layer, one level down.

**The Intelligence Gateway needed zero code changes to support live
providers — this task confirms that, it doesn't build it.**
`travelos/intelligence_gateway/gateway.py`, `provider_registry.py`, and
`provider_selector.py` are untouched by T-026. Because `BaseLiveProvider`
is a `Provider`, the exact same registration, selection, retry, and
failover code T-025 shipped already works — proven directly by
`travelos/tests/test_live_provider_gateway_integration.py`, which
registers a mock stub and the live provider template into one registry
and exercises environment-based selection and live-to-mock failover
using unmodified T-025 code. This is the strongest possible validation
that T-025's `Provider` abstraction was scoped correctly the first time.

**Dependency direction: `travelos/live_providers/` depends on
`travelos/intelligence_gateway/`, never the reverse.** Every import in
this package points at the gateway package (`Provider`, `ProviderResult`,
`ProviderRequest`, exceptions, `SecretReference`) or the stdlib —
nothing in `travelos/intelligence_gateway/` imports anything from
`travelos/live_providers/`. This is why `ProviderHealthResult`
(requirement 8's richer health result) is **not** added to the shared
`Provider` contract as a new abstract method — doing so would require
the gateway package to import a `travelos.live_providers` type, inverting
the dependency. Instead, `BaseLiveProvider.health_check_detailed()` is
an *additional* method live providers expose, and the diagnostics
endpoint (`services/api/app/routers/internal.py`, itself outside both
platform packages) duck-types for it:
`getattr(provider, "health_check_detailed", None)`.

**One shared error hierarchy, not two.** T-026's brief names seven
standard error types; five already existed in
`travelos/intelligence_gateway/exceptions.py` (T-025) under the same or
a near-identical name. Rather than create a second, parallel hierarchy
under `travelos/live_providers/errors/`, that module re-exports the
existing one, and two new types this task actually needed
(`ProviderResponseError`, genuinely new; `ProviderConfigurationError`,
aliased to T-025's `ProviderMisconfiguredError`) were added directly to
the shared file. `ProviderRateLimitError` (this task's name) is
similarly aliased to T-025's `ProviderRateLimitedError`. Both aliases
resolve to the exact same class (`is`-identical), not merely
`==`-equal — `docs/PROVIDER_ERROR_MODEL.md` documents this once so it
isn't rediscovered as a surprise later. Renaming the T-025 originals was
rejected as a breaking change to already-shipped, already-tested code
for a purely cosmetic gain.

**`TRALVANA_PROVIDER_ENVIRONMENT` is additive to, not a replacement for,
T-025's `PROVIDER_ENVIRONMENT`.** T-026's brief specifies this exact env
var name, distinct from what T-025 shipped and already documented/tested
extensively. `ConfigurationManager.provider_environment` now checks
`TRALVANA_PROVIDER_ENVIRONMENT` first, falling back to
`PROVIDER_ENVIRONMENT`, falling back to the computed default — both
names work, nothing already configured against the T-025 name breaks.

**Metrics are recorded by `BaseLiveProvider.execute()` itself, not
centralized in the gateway.** This keeps the dependency direction clean
(the gateway never needs to know `travelos.live_providers.metrics`
exists) and matches the brief's framing directly ("allow future adapters
to report optional cost metadata" — adapter-level reporting, not
gateway-level). The consequence: T-025's mock providers don't
automatically get metrics from this change — `provider_metrics.snapshot_for()`
returns `None` for them, and the diagnostics endpoint reports `0`/`0`
for their request/failure counts. This is accurate (they've never been
asked to record anything) rather than a gap; retrofitting mock providers
with the same instrumentation is straightforward future work if wanted,
not required by this task's scope.

**No real HTTP transport is implemented — only `FakeTransport`.** The
`Transport` interface is fully defined and provider-agnostic (`send(TransportRequest) -> TransportResponse`,
GET/POST, headers, query params, JSON body, timeout, status code,
response body — every field this task's brief lists), but a concrete
`httpx`-backed transport is deliberately deferred. Building one with
nothing to safely exercise it against (this task explicitly forbids any
real network request) would add untested surface area for no proven
benefit — see Deferred Items below.

**`adapters/` holds the pattern's documentation, not a second class
hierarchy.** The request/response adapter pattern this task asks for
(requirement 6) is already fully expressed by `BaseLiveProvider.build_request()`/
`.parse_response()` — each concrete provider already owns its mapping by
implementing those two methods. A separate `RequestAdapter`/
`ResponseAdapter` ABC pair wrapping the same two methods would be
redundant abstraction, directly against this task's own "keep the
framework small and reusable" constraint. `adapters/__init__.py`
documents the pattern and reserves the location for genuinely
vendor-specific adapter modules as real ones are built (e.g. a future
`adapters/duffel_flight_adapter.py`), satisfying the suggested folder
structure without inventing an unnecessary layer today.

**No real OAuth2 token exchange.** `OAuth2ClientCredentialsAuthStrategy.headers()`
raises `ProviderConfigurationError` unless a token has been pre-loaded
via `set_cached_token()` — a test/simulation-only hook, never populated
by a live call anywhere in this framework. This satisfies "create
interfaces only... no real tokens or live authentication calls"
literally while still letting `is_configured()` and the success-path
header-building logic be genuinely tested.

## Alternatives Considered

| Option | Rejected Because |
|--------|-------------------|
| Give `BaseLiveProvider` its own contract, separate from `Provider` | Would require the gateway to special-case live providers, defeating the entire point of T-025's polymorphic contract; also directly against "extend the existing Intelligence Gateway... preserve current public behaviour" |
| Add `health_check_detailed()` as a new abstract/default method on the shared `Provider` contract | Creates a dependency from `travelos/intelligence_gateway/` into `travelos/live_providers/`, inverting this framework's own dependency direction for a convenience that duck-typing already provides without the coupling |
| Centralize metrics recording inside `gateway.py`'s `_call_provider`, covering mock and live providers uniformly | Also creates a gateway → live_providers dependency (for `ProviderMetricsTracker`); kept metrics adapter-level instead, matching the brief's "allow future adapters to report" framing |
| Rename T-025's `ProviderRateLimitedError`/`ProviderMisconfiguredError` to this task's `ProviderRateLimitError`/`ProviderConfigurationError` | Breaking change to already-shipped, already-tested code for a naming preference; aliasing achieves the same literal-name requirement with zero risk |
| Implement a real `httpx`-backed `Transport` now, since `httpx` is already a dependency (via FastAPI's TestClient) | Nothing in this task's scope can safely exercise it (no live network request allowed) — untested, unexercised code is worse than clearly-deferred code; see Deferred Items |
| Build a real OAuth2 token-exchange call, gated behind a "don't actually call it" test flag | Directly against the explicit constraint "No real tokens or live authentication calls" — the interface-only approach with a test-only injection hook satisfies the same testing need without the risk of the flag being accidentally left enabled somewhere |
| A separate `RequestAdapter`/`ResponseAdapter` class hierarchy under `adapters/` | Redundant given `build_request`/`parse_response` already exist on `BaseLiveProvider` and already are the adapter pattern; would violate "keep the framework small" for no behavioural gain |

## Consequences

- `travelos/live_providers/` — new package, ~20 files, zero new
  third-party dependencies. Every import points at
  `travelos.intelligence_gateway` or the stdlib.
- `travelos/intelligence_gateway/exceptions.py` and `retry_policy.py`
  gain two new error types and one retry-classification addition —
  additive only, no existing type renamed or removed.
- `travelos/intelligence_gateway/gateway.py`, `provider_registry.py`,
  `provider_selector.py` — **zero changes**. This is itself a
  consequence worth recording: it means T-025's abstraction held exactly
  as designed.
- `travelos/config/configuration_manager.py` gains four new properties,
  plus one existing property (`provider_environment`) gains a second,
  backward-compatible env var name.
- `services/api/app/routers/internal.py`'s response shape gains five new
  per-provider fields — additive, not a removal/rename of any T-025
  field; the one T-025 test that asserted an exact field set was updated
  to the new superset, not silently left to fail.
- No live provider is registered anywhere by default — the mock
  providers (T-025) remain the only ones actually running in this
  repository's normal operation.
- 913 tests pass (833 pre-existing + 80 new), Ruff clean.

## Deferred Items

- **A real HTTP transport implementation** (e.g. `httpx`-backed). The
  `Transport` interface is complete and ready; only `FakeTransport`
  exists as a concrete implementation. Building the real one is the
  natural first step of whatever task first connects an actual vendor.
- **A real OAuth2 client-credentials token exchange.** The strategy's
  shape and configuration-checking are complete; the actual `POST` to a
  vendor's token endpoint, response parsing, and expiry-based refresh
  logic are not implemented.
- **Retrofitting `ProviderMetricsTracker` onto T-025's mock providers.**
  Currently only `BaseLiveProvider.execute()` records metrics
  automatically; mock providers report `0`/`0` request/failure counts in
  diagnostics. Straightforward to add if uniform metrics across every
  provider type becomes useful.
- **Any actual vendor adapter** (Duffel, Amadeus, a real weather API,
  Maps, Currency, Events). `docs/LIVE_PROVIDER_ADAPTER_GUIDE.md`
  documents exactly how to build one on top of this framework; none is
  built here, per this task's explicit scope.
