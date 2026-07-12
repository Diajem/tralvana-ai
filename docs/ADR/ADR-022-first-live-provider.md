# ADR-022: First Live Provider — Duffel

**Date**: 2026-07-12
**Status**: Accepted
**Sprint**: 2/3 boundary (T-027)

## Context

T-026 built `BaseLiveProvider` — a reusable base every real vendor
adapter follows — but connected no real vendor. This task's brief asks
for the first one, explicitly forbidding an assumption of Amadeus
access and asking for an evaluated recommendation instead. See
`docs/FIRST_LIVE_PROVIDER.md` for the full comparison table; this ADR
records the decision and its consequences.

## Decision

**Duffel, selected primarily on authentication compatibility with the
framework as it exists today, not on coverage or price.**
`travelos/live_providers/auth/bearer_token_auth.py`
(`BearerTokenAuthStrategy`) is fully implemented; Duffel's
authentication scheme is exactly a static bearer token. Every
alternative considered with genuinely self-serve sandbox access
(Amadeus for Developers) requires OAuth2 client-credentials — this
framework's `OAuth2ClientCredentialsAuthStrategy.headers()`
unconditionally raises `ProviderConfigurationError` because no real
token exchange is implemented (TD-022, ADR-021's own Deferred Items).
Kiwi.com and Skyscanner were eliminated earlier — neither offers
self-serve sandbox access at all, so neither could be evaluated past
that first gate regardless of their auth scheme.

**The adapter's `parse_response()` must produce the exact internal
flight-option shape `ai/discovery/flights/flight_scorer.py`,
`flight_reasoner.py`, and `flight_risk_assessor.py` already read from
`MockFlightProvider.search()` — not merely *a* valid `ProviderResult`.**
This is a stricter contract than `ExampleFlightProvider`'s template
satisfies (that template just returns `body["flights"]` verbatim,
untyped). Because `GatewayFlightProvider.search()` (T-025, unchanged)
returns `ProviderResult.data` directly to `FlightIntelligence.recommend()`,
which immediately calls `flight_scorer.score(flight, ...)` on each
element, any field those three modules read — including the
underscore-prefixed internal fields `_total_duration_minutes` and
`_layover_minutes`, popped before the API response is built but read
earlier by scoring — must be present and correctly typed. This is the
concrete reason "no Discovery Layer redesign" was achievable: the
constraint held because the adapter did the work of matching the
existing contract, not because the contract was loosened.

**Duffel's structured error body is inspected via a `send_request()`
override, not by changing `_check_response_status()`.**
`BaseLiveProvider.map_error()` only receives the raised exception, not
the `TransportResponse` that produced it — by design, so that generic
HTTP-status mapping stays generic. Duffel's 422 validation errors carry
a `{"errors": [{"type": "validation_error", ...}]}` body that the
status code alone can't distinguish from any other unrecognised
non-5xx failure. `DuffelFlightProvider` overrides `send_request()`
purely to stash the last `TransportResponse` on `self`, then
`map_error()` inspects it — using the exact override point
(`map_error()`) `docs/LIVE_PROVIDER_ADAPTER_GUIDE.md` already documents
for this purpose, rather than touching the shared
`_check_response_status()` method every other live provider also
inherits.

**Registration is explicit, not automatic at import.** T-025's mock
providers auto-register via `register_default_providers()` at the
bottom of `travelos/intelligence_gateway/discovery_adapters.py` — safe,
because a mock provider never makes an external call regardless of
whether anything selects it. `DuffelFlightProvider` cannot follow that
pattern without a default `Transport`, and no real one exists yet
(TD-021, still open — this task does not close it). Defaulting to
`FakeTransport` at import time was rejected: it would make the
provider appear registered and "ready" while silently returning canned
data the moment `PROVIDER_ENVIRONMENT` is set to `SANDBOX`, which is a
worse failure mode than requiring an explicit
`register_duffel_flight_provider(transport=...)` call.

**No real HTTP transport is built by this task either.** T-026 already
gave the reasoning (ADR-021's Deferred Items): nothing in this task's
scope can safely exercise a real transport without a live network
call, which the task's own constraints ("Do not use live credentials")
forbid. `docs/FIRST_LIVE_PROVIDER.md`'s "What Remains Before Real
Production Use" names this as the first open item.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Recommend Amadeus, since it's the most GDS-standard vendor | Explicitly forbidden by this task's own constraint ("Do not assume Amadeus"); also blocked by the same OAuth2 gap regardless — recommending it would just relocate the blocker into a future task rather than resolve it |
| Implement `OAuth2ClientCredentialsAuthStrategy.fetch_token()` now so Amadeus becomes viable | Out of scope — a real token-exchange HTTP call is exactly what T-026 deferred and this task's own constraints ("Do not use live credentials") don't authorize building now; would also require a real Transport, compounding the untested-surface-area problem ADR-021 already flagged |
| Auto-register `DuffelFlightProvider` at import with a default `FakeTransport`, matching the mock-provider pattern | Makes a live-shaped provider look production-configured while actually serving fabricated data under a real environment flag — a worse failure mode than an explicit, documented registration call |
| Have `DuffelFlightProvider.parse_response()` return Duffel's raw offer dicts and adapt them in `ai/discovery/flights/flight_intelligence.py` instead | Directly violates "no Discovery Layer redesign" and the adapter guide's own rule that vendor-shaped data must never leak past `parse_response()`; would also mean two call sites (mock and Duffel) diverging in what a "flight option" dict contains |
| Override `_check_response_status()` to add Duffel-specific status-code handling | Would special-case one adapter inside a method every other live provider inherits unmodified; `map_error()` already exists precisely as the vendor-specific hook, per `docs/PROVIDER_ERROR_MODEL.md` |

## Consequences

- `travelos/live_providers/adapters/duffel_flight_provider.py` — new
  file, ~250 lines, zero new third-party dependencies (stdlib `re` and
  `datetime` only). Every import points at `travelos.intelligence_gateway`,
  `travelos.live_providers`, or the stdlib — same dependency direction
  ADR-021 established.
- `travelos/intelligence_gateway/`, `travelos/live_providers/base_live_provider.py`,
  `ai/discovery/flights/`, `ai/trip_brain/`, and
  `services/api/app/domains/flights/` — **zero changes**. The
  Intelligence Gateway needed no changes for a second live provider any
  more than it needed changes for the first (ADR-021's own point,
  reconfirmed here for a genuinely production-shaped adapter rather
  than a template).
- No live provider is registered anywhere by default — same statement
  ADR-021 made about T-026, still true after T-027; `DuffelFlightProvider`
  exists and is fully tested, but nothing calls
  `register_duffel_flight_provider()` at import time or from
  `services/api/app/main.py`.
- 948 tests pass (913 pre-existing + 35 new), Ruff clean.

## Deferred Items

- A real HTTP transport (`httpx`-backed or otherwise) — same item
  ADR-021 deferred, still open.
- A real Duffel sandbox account and token exercised against Duffel's
  actual API, not only `FakeTransport`.
- Wiring `register_duffel_flight_provider()` into application startup,
  gated by environment/token presence — blocked on the real transport
  above.
- Passenger-count plumbing (`adults`) through `GatewayFlightProvider.search()`'s
  signature — a pre-existing Discovery-layer limitation, out of this
  task's scope per its own "no Discovery Layer redesign" constraint.
- `OAuth2ClientCredentialsAuthStrategy.fetch_token()` — still not
  implemented; still the blocker for Amadeus or any other
  OAuth2-client-credentials vendor becoming viable later (TD-022).
