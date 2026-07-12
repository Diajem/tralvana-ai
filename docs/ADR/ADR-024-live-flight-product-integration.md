# ADR-024: Live Flight Search Product Integration

**Date**: 2026-07-12
**Status**: Accepted
**Sprint**: 2/3 boundary (T-038)

## Context

T-027 built `DuffelFlightProvider`; T-037 gave it a real `Transport`
and proved one live call worked. Neither made Duffel data reachable
from a traveller-facing request — no configuration existed to turn it
on, no validation guarded a live call, and the public API had no way
to say where a result came from. T-038 closes that gap: `POST
/flights/recommend` can now return real, ranked, explained Duffel
sandbox offers, switchable via one environment variable, with MOCK
remaining the default and every existing behaviour preserved.

## Decision

**FLIGHTS gets its own environment switch, independent of the general
`PROVIDER_ENVIRONMENT`.** `TRALVANA_FLIGHT_PROVIDER_MODE` (`MOCK` /
`LIVE_SANDBOX`) is read by a new `ConfigurationManager.flight_provider_mode`
property. `IntelligenceGateway.execute()` gained
`_environment_for(capability)` — FLIGHTS resolves its environment from
this new switch; every other capability (Accommodation, Weather) still
resolves from `provider_environment`, byte-identical to before. This
was the one genuinely hard architectural problem T-038 had to solve:
`IntelligenceGateway.environment` was a single scalar shared by every
capability, so naively flipping it to `SANDBOX` to enable Duffel would
have simultaneously broken Accommodation/Weather (their mock providers
are `environment=MOCK`, and the selector requires an exact match).
Per-capability resolution inside the one existing Gateway class avoided
both a second Gateway instance and a second DI system.

**Registration is startup-only, explicit, and fail-fast.**
`travelos/live_providers/flight_provider_bootstrap.py`'s
`configure_flight_provider()` is called once from
`services/api/app/main.py` — the actual composition root, never a route
handler, never `ai/discovery/flights/` (Trip Brain and the Discovery
layer stay completely unaware this decision exists). In `MOCK` mode it
is a true no-op: no `Transport` constructed, no provider registered, no
credential required, no network call possible. In `LIVE_SANDBOX` mode
without `DUFFEL_API_TOKEN`, it raises `FlightProviderMisconfiguredError`
and the application process fails to start — deliberately, rather than
silently serving from a mode that can never work, or discovering the
misconfiguration only when the first traveller's search hits a
per-request `MISCONFIGURED` health check.

**Validation is LIVE_SANDBOX-only, not baked into the shared request
schema.** `ai/discovery/flights/live_search_validator.py`'s
`validate_live_flight_search()` enforces IATA codes, date sanity, and
passenger/cabin bounds — but only when
`FlightIntelligenceService.recommend()` sees `flight_provider_mode ==
"LIVE_SANDBOX"`. `RecommendFlightsRequest`'s Pydantic schema itself is
untouched. This was necessary, not a shortcut: the existing default
(`origin: str = "London"`) and every existing test/caller use city
names, which `MockFlightProvider` has never required to be IATA codes.
Adding a blanket schema-level validator would have broken every
existing MOCK-mode caller — a real regression T-038's own "preserve
public API" constraint forbids.

**`GatewayFlightProvider` grew `last_result`/`used_mock_fallback`
instead of returning a richer type.** The existing `search()` contract
(`list[dict]`, matching `MockFlightProvider.search()` exactly) is
unchanged — `FlightIntelligence.recommend()` (`ai/discovery/flights/flight_intelligence.py`)
duck-types these two new attributes to build `data_source`/`provider_status`/
`retrieved_at`/`request_id` without requiring every `search()` caller
(there's only one, but the principle held) to migrate to a new return
shape.

**Live failure is a `503` by default, never a silent empty result;
fallback is opt-in and never blended with live data.**
`LiveFlightSearchUnavailableError` (new, `travelos/intelligence_gateway/discovery_adapters.py`)
propagates through `FlightIntelligenceService.recommend()` to the
router, converted to `503`. `TRALVANA_FLIGHT_MOCK_FALLBACK_ENABLED=true`
switches this to calling `MockFlightProvider` directly and labelling
the result `MOCK_FALLBACK` — a completely separate code path from the
live one, so a fallback response is always 100% mock, never a mix.

**Partial mapping failure changed `DuffelFlightProvider.parse_response()`'s
behaviour: one bad offer no longer discards the whole batch.** Before
T-038, any single malformed offer raised `ProviderResponseError` for
the entire response (all-or-nothing, T-027's original design). T-038's
explicit requirement to handle "partial mapping failure" made this the
wrong default for a real vendor response that can carry 200+ offers —
`parse_response()` now skips individually-failing offers, records a
warning and `raw_offer_count`/`mapped_offer_count` in
`source_metadata`, and only raises if *every* offer in a non-empty
batch fails (a genuine response-shape problem, not a data quirk).

**`provider_offer_id` is preserved but deliberately asymmetric: internal-only
at the recommendation-response level, public at the single-flight-option
level.** `FlightOption.provider_offer_id` is excluded from
`to_dict()`'s public shape (never in `POST /flights/recommend`'s
`flight_options[]`) — Duffel's own offer id has no meaning to a
traveller and no booking flow reads it yet. `FlightOption.data_source`,
by contrast, *is* public at both the recommendation-response level and
the individual-option level, specifically so a flight fetched later via
`GET /flights/{id}` (e.g. a bookmarked or shared link) still carries
its own sandbox/mock label — the "clearly label all live sandbox
results" requirement doesn't stop being true just because the request
happened outside the original search response.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Flip the existing global `PROVIDER_ENVIRONMENT` to `SANDBOX` to enable Duffel | Breaks Accommodation/Weather's mock provider selection simultaneously — a single scalar environment can't serve two different intents for two different capabilities |
| A second, flights-only `IntelligenceGateway` instance | Works, but means two Gateway instances exist app-wide for no architectural reason beyond one config value differing — per-capability resolution inside the one existing Gateway class is smaller and matches "use the existing Intelligence Gateway" literally |
| Bake IATA/date validation into `RecommendFlightsRequest`'s Pydantic schema | Breaks every existing MOCK-mode city-name-based request and test — a real regression, not a hardening |
| Auto-register Duffel at import time (matching the T-025 mock-provider pattern) | Would make every app boot capable of a real outbound call the moment the env var flips, without a startup-time decision point — kept explicit via `configure_flight_provider()`, called once from the actual composition root |
| Silently fall back to mock on any live failure, no configuration | Directly against T-038's own "LIVE_SANDBOX failure returns a clear safe error by default" — an unconfigurable fallback would hide real sandbox outages from whoever is testing the feature |
| Discard the entire offer batch on one malformed offer (T-027's original behaviour) | A real 235-offer response with one bad entry would return zero results — worse than 234 correct ones with a recorded warning |
| Expose `provider_offer_id` publicly everywhere, since it's "just an id" | No current consumer needs it outside a future booking flow; keeping it internal-only at the recommendation-response level is the more conservative reading of "preserve provider offer identifiers internally... do not begin booking implementation" |
| Register `duffel_flight_provider` into `travelos/registry/service_registry.py` (the domain `ServiceRegistry`) | That registry resolves domain *services* by string name (`goal_service`, `trip_planning_service`, ...) — `flight_intelligence_service` isn't even registered there today. The correct existing registry for a `Provider` is `travelos.intelligence_gateway.provider_registry`, already used; adding flights to `ServiceRegistry` too would be a second, parallel lookup mechanism for the same object |

## Consequences

- New: `travelos/live_providers/flight_provider_bootstrap.py`,
  `ai/discovery/flights/live_search_validator.py`,
  `scripts/verify_duffel_live_sandbox.py`.
- Modified: `travelos/config/configuration_manager.py` (+2 properties),
  `travelos/intelligence_gateway/gateway.py` (+1 method, `execute()`'s
  selection call site changed), `travelos/intelligence_gateway/discovery_adapters.py`
  (`GatewayFlightProvider` +2 attributes, new failure/fallback branch;
  new `LiveFlightSearchUnavailableError`), `travelos/live_providers/adapters/duffel_flight_provider.py`
  (`parse_response()` partial-failure tolerance, `_provider_offer_id`),
  `ai/discovery/flights/flight_intelligence.py` (`_source_metadata()`,
  per-option `data_source`/`provider_offer_id`, conditional assumption
  text), `services/api/app/domains/flights/{models,schemas,service,router}.py`
  (additive fields, validation call, exception-to-HTTP mapping),
  `services/api/app/main.py` (one composition-root call),
  `apps/web/src/{types/flight.ts,lib/api.ts,app/flights/recommend/page.tsx,app/flights/[id]/page.tsx}`.
- Zero changes to Trip Brain (`ai/trip_brain/`), the Explainability
  Engine (`ai/explainability/`), or any other Discovery module
  (Accommodation, Destination, Budget, Visa, Weather).
- `MOCK` mode (the default) is behaviourally identical to pre-T-038 —
  every pre-existing test passes unchanged; the additive response
  fields default to values that describe exactly what was already true
  (`data_source: "MOCK"`, etc.).
- 1032 tests pass (959 pre-existing at T-038's start + 73 new), Ruff
  clean, frontend typecheck and production build both clean.
- One real, successful HTTP round trip was made to Duffel's SANDBOX
  environment via `scripts/verify_duffel_live_sandbox.py`, through the
  full product architecture (not just the raw Gateway, as T-037's
  verification was) — 235 raw offers, 235 normalised, 235 ranked.

## Deferred Items

- Application-startup wiring remains opt-in only — no deployment
  automatically enables `LIVE_SANDBOX`.
- The remainder of `docs/PRODUCTION_READINESS.md`'s checklist.
- Any booking, payment, ticketing, order-creation, seat-selection, or
  baggage-purchase work — explicitly out of scope; `provider_offer_id`
  is preserved specifically so this doesn't have to be re-derived
  later, but nothing reads it yet.
- Passenger-count plumbing through `GatewayFlightProvider.search()`'s
  signature — pre-existing limitation, unchanged.
- `OAuth2ClientCredentialsAuthStrategy.fetch_token()` — still not
  implemented (TD-022), still the blocker for Amadeus or any other
  OAuth2-client-credentials vendor.
