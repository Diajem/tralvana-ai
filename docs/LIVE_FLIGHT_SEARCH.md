# Live Flight Search (T-038)

Turns the verified Duffel sandbox connection (T-027, T-037) into a
user-facing capability: a traveller can submit a flight search through
Tralvana and receive real Duffel sandbox offers, normalised, scored,
ranked, and explained by the existing Flight Intelligence Engine — the
same pipeline that has always served mock data.

**Search and recommendation only.** No booking, payment, ticketing,
order creation, seat selection, or baggage purchase is implemented
anywhere in this feature. See `docs/DUFFEL_SANDBOX_OPERATIONS.md` for
day-to-day operation and `docs/ADR/ADR-024-live-flight-product-integration.md`
for the design decisions behind it.

## Architecture

```
Flight Search UI (apps/web/src/app/flights/recommend)
  -> POST /flights/recommend (services/api/app/domains/flights/router.py)
    -> FlightIntelligenceService (services/api/app/domains/flights/service.py)
      -> [LIVE_SANDBOX only] validate_live_flight_search() — before any provider call
      -> FlightIntelligence.recommend() (ai/discovery/flights/flight_intelligence.py)
        -> GatewayFlightProvider.search() (travelos/intelligence_gateway/discovery_adapters.py)
          -> IntelligenceGateway.execute(FLIGHTS, ...) — per-capability environment resolution
            -> DuffelFlightProvider (SANDBOX) or mock_flight_provider (MOCK)
              -> HttpxTransport -> Duffel SANDBOX API (live mode only)
        -> normalised flight-option dicts (unchanged shape, mock or live)
        -> FlightScorer -> FlightReasoner -> FlightRiskAssessor -> ranked, labelled results
      -> data_source / provider_status / retrieved_at / request_id attached
    -> FlightRecommendationResponse (existing shape, additively extended)
```

No new endpoint. `POST /flights/recommend` and `GET /flights/{id}` are
unchanged in shape and continue to work exactly as before in `MOCK`
mode (the default) — every existing test and caller is unaffected.

## Switching Between MOCK and LIVE_SANDBOX

One environment variable, read by `ConfigurationManager.flight_provider_mode`
(`travelos/config/configuration_manager.py`):

```bash
TRALVANA_FLIGHT_PROVIDER_MODE=MOCK          # default — no change from before T-038
TRALVANA_FLIGHT_PROVIDER_MODE=LIVE_SANDBOX  # requires DUFFEL_API_TOKEN
```

- **Never inferred from `DUFFEL_API_TOKEN`'s presence.** A token sitting
  in `.env` with the mode left at `MOCK` (or unset) changes nothing —
  no Duffel provider is even constructed, and no network call is made.
- **Restart required.** `configure_flight_provider()`
  (`travelos/live_providers/flight_provider_bootstrap.py`) runs once,
  at application startup (`services/api/app/main.py`) — it decides
  whether Duffel gets registered at all. Flipping the env var without
  restarting the process has no effect.
- **Scoped to FLIGHTS only.** `IntelligenceGateway._environment_for(capability)`
  (`travelos/intelligence_gateway/gateway.py`) resolves FLIGHTS'
  environment from `flight_provider_mode`; every other capability
  (Accommodation, Weather) still resolves from the general
  `PROVIDER_ENVIRONMENT`/`TRALVANA_PROVIDER_ENVIRONMENT`, untouched.
  Setting FLIGHTS to `LIVE_SANDBOX` never puts Accommodation or Weather
  into a live mode they were never asked for.

### What Happens in Each Mode

| | `MOCK` (default) | `LIVE_SANDBOX` |
|---|---|---|
| Startup | No Duffel provider constructed, no credential required | `DUFFEL_API_TOKEN` required — missing token **fails application startup** (`FlightProviderMisconfiguredError`), not a per-request error |
| Request validation | None beyond existing Pydantic field types — city names like `"London"` still work | IATA codes, date sanity, passenger/cabin bounds enforced *before* any Duffel call (`ai/discovery/flights/live_search_validator.py`) |
| Network calls | Zero, ever | One `HttpxTransport` call to Duffel's real SANDBOX API per search |
| `data_source` in response | `"MOCK"` | `"DUFFEL_SANDBOX"` (or `"MOCK_FALLBACK"` — see below) |

## Manual Live Verification

```bash
python scripts/verify_duffel_live_sandbox.py
```

Reads `DUFFEL_API_TOKEN` from the repo-root `.env`, runs one real
search through the full architecture above, and prints only:
`http_status_code`, `provider_status`, `data_source`,
`raw_offer_count`, `normalised_offer_count`, `ranked_offer_count`,
`request_id`. Never prints the token, request headers, or the raw
Duffel payload. See `docs/DUFFEL_SANDBOX_OPERATIONS.md` for a worked
example and troubleshooting.

**Never run in CI or normal `pytest`.** All 100+ new automated tests
for this feature use `FakeTransport`/`httpx.MockTransport` — see
"Testing" below.

## Request Validation (LIVE_SANDBOX only)

`ai/discovery/flights/live_search_validator.py`'s
`validate_live_flight_search()`, called from
`FlightIntelligenceService.recommend()` before `FlightIntelligence.recommend()`
is ever reached — a validation failure never results in a Duffel call:

- `origin` / `destination`: 3-letter IATA code (case-insensitive), and must differ
- `departure_date`: `YYYY-MM-DD`, required, not in the past
- `return_date`: `YYYY-MM-DD` if given, must be after `departure_date`
- `adults`: 1–9
- `cabin_class`: `economy` | `business` | `first`

Every problem found is collected and returned together (not just the
first) as a `422` with `{"detail": {"errors": [...]}}`.
**Deliberately MOCK-mode-exempt** — `MockFlightProvider` has never
required IATA codes, and existing city-name-based requests (the
current default, `origin="London"`) must keep working exactly as
before T-038.

## Public API Additions

`POST /flights/recommend`'s response gains five additive fields (all
have defaults, so this is not a breaking change):

| Field | Meaning |
|---|---|
| `data_source` | `MOCK` \| `DUFFEL_SANDBOX` \| `MOCK_FALLBACK` |
| `retrieved_at` | ISO timestamp the result was retrieved (from the underlying `ProviderResult`, or "now" for a plain mock call) |
| `provider_status` | The `ProviderStatus` the Intelligence Gateway reported (`AVAILABLE`, `UNAVAILABLE`, ...) |
| `results_count` | `len(flight_options)` |
| `request_id` | The Intelligence Gateway's request id for this call |

Each individual `FlightOptionResponse` also gains `data_source` (same
values) so a single flight fetched later via `GET /flights/{id}` still
carries its own sandbox/mock label.

**Never exposed, anywhere:** the Duffel bearer token, any outbound
request header, the raw Duffel JSON payload, or Duffel's own internal
offer/offer-request IDs. Duffel's offer `id` is preserved internally
only (`FlightOption.provider_offer_id`, `services/api/app/domains/flights/models.py`)
for future booking work — deliberately excluded from `to_dict()`'s
public shape.

## Failure and Fallback Behaviour

| Situation | MOCK mode | LIVE_SANDBOX mode |
|---|---|---|
| Provider auth failure, timeout, rate limit, malformed response, or simply unavailable | Cannot happen — mock never fails this way | `ProviderResult.status != AVAILABLE` |
| Fallback disabled (default, `TRALVANA_FLIGHT_MOCK_FALLBACK_ENABLED=false`) | n/a | `503` — `LiveFlightSearchUnavailableError`, a clear message naming the provider status. **Never a silent empty result.** |
| Fallback enabled | n/a | Falls back to `MockFlightProvider` directly, labelled `data_source: "MOCK_FALLBACK"`, with an explicit assumption stating sandbox was unavailable |
| Zero offers (a valid, well-formed empty response) | `results_count: 0`, no error | Same — an empty result is not a failure |
| Partial mapping failure (some offers in a batch don't map) | n/a | The malformed offers are skipped and counted (`ProviderResult.warnings`), the rest are still returned — a batch of 235 offers with 1 bad one still returns 234, not zero |

**Mock and live offers are never mixed in one ranked result set.** A
fallback response is 100% mock data, clearly labelled — never a blend.

## Frontend

`apps/web/src/app/flights/recommend/page.tsx` — existing form fields
(origin, destination, dates, adults, cabin class, budget style,
airline preference) unchanged; added:

- A source badge next to the summary (`Test data` / `Duffel sandbox` / `Mock fallback`)
- A banner when results are live or fallback data: *"Sandbox flight
  data — not available for purchase."* (live) or a fallback-specific
  message
- Baggage/refundability/flexibility shown on every flight card
- An IATA-code hint under the origin field

`apps/web/src/app/flights/[id]/page.tsx` — same sandbox banner, driven
by the per-option `data_source` field (so a bookmarked single-flight
URL still shows the right label). Nothing anywhere presents a result
as bookable — there is no booking UI, button, or copy implying one.

## Testing

Every new automated test uses `FakeTransport` or `httpx.MockTransport`
— no real network call runs in `pytest`/CI. See:

- `travelos/tests/test_flight_provider_mode_config.py`
- `travelos/tests/test_gateway_flight_capability_environment.py`
- `travelos/tests/test_flight_provider_bootstrap.py`
- `travelos/tests/test_gateway_flight_provider_fallback.py`
- `travelos/tests/test_duffel_flight_provider.py` (extended — partial mapping failure, provider offer id, day-component durations)
- `ai/tests/test_live_search_validator.py`
- `ai/tests/test_flight_intelligence_source_metadata.py`
- `services/api/tests/test_flights_live_search.py`

The one real network call this feature makes is the manual verification
script above — never part of the automated suite.

## What Remains Before Production and Booking

- **Application-startup wiring is opt-in only via the env var** —
  nothing about default (`MOCK`) behaviour changed; `LIVE_SANDBOX` must
  be deliberately configured per deployment.
- **The rest of `docs/PRODUCTION_READINESS.md`'s checklist** — most
  items remain open (monitoring integration, rate-limit tuning against
  Duffel's real documented limits, secret rotation drill, second-engineer
  review, rollback plan). T-037/T-038 close only the Sandbox Validation
  item.
- **No booking, payment, ticketing, order creation, seat selection, or
  baggage purchase exists anywhere** — this was explicitly out of scope
  and nothing here begins that work. `provider_offer_id` is preserved
  internally specifically so a future booking task doesn't have to
  re-derive it, but no booking flow reads it yet.
- **Duffel sandbox only** — no production Duffel token has been used or
  should be, anywhere in this repository.
- **Adult-only passenger count** — `GatewayFlightProvider.search()`'s
  signature still doesn't accept a passenger count from the caller
  (pre-existing Discovery-layer limitation, out of scope per "no
  Discovery Layer redesign").
