# Flight Provider Integration — Duffel Adapter

How `DuffelFlightProvider` (`travelos/live_providers/adapters/duffel_flight_provider.py`)
is built on `BaseLiveProvider`, and how to enable it. Written as a
concrete companion to the general `docs/LIVE_PROVIDER_ADAPTER_GUIDE.md`
— read that first for the framework-level contract this adapter
implements.

## Architecture (unchanged)

```
FlightIntelligence (ai/discovery/flights/flight_intelligence.py)
  -> GatewayFlightProvider.search()            (unchanged, T-025)
    -> IntelligenceGateway.execute()           (unchanged, T-025)
      -> ProviderSelector                      (unchanged — environment/health/priority)
        -> DuffelFlightProvider.execute()      (new, T-027, extends BaseLiveProvider)
          -> authenticate() -> BearerTokenAuthStrategy
          -> build_request() -> Duffel offer_requests shape
          -> send_request()  -> Transport (FakeTransport only, still — see below)
          -> parse_response() -> internal flight-option dicts
```

Nothing in `ai/discovery/flights/`, `ai/trip_brain/`, or
`services/api/app/domains/flights/` changed. `FlightIntelligence`
still calls `self._provider.search(...)`; `GatewayFlightProvider.search()`
still builds the same `ProviderRequest` it always has. The only new
thing the Intelligence Gateway can now select is one more `Provider`
implementation — exactly ADR-021's point about T-025's abstraction
generalizing to any real vendor, now proven with a second concrete
adapter beyond `ExampleFlightProvider`.

## Authentication

`BearerTokenAuthStrategy(secret=SecretReference(env_var="DUFFEL_API_TOKEN"))`.
One environment variable, no OAuth2 exchange, no client_id/client_secret
pair. `SecretReference` — never a hardcoded value; `is_configured()`
only checks presence; `.resolve()` is called exactly once, inside
`BaseLiveProvider.authenticate()`, immediately before being merged into
the outbound request's headers.

Use a `duffel_test_...` token for `ProviderEnvironment.SANDBOX`
(the adapter's default) and a `duffel_live_...` token only if this
adapter is ever constructed with `environment=ProviderEnvironment.PRODUCTION`
— `docs/PRODUCTION_READINESS.md` must be fully checked off first.

## Request Mapping — `build_request()`

Internal `ProviderRequest.params` (`origin`, `destination`,
`departure_date`, `return_date`, `cabin_class` — exactly what
`GatewayFlightProvider.search()` already passes, no new fields) maps to
Duffel's `POST /air/offer_requests?return_offers=true`:

| Internal field | Duffel field |
|---|---|
| `origin` / `destination` / `departure_date` | `data.slices[0]` |
| `return_date` (if present) | `data.slices[1]` — omitted entirely for one-way |
| `cabin_class` (`economy`\|`business`\|`first`) | `data.cabin_class` (identity mapping — Duffel's fourth tier, `premium_economy`, is never requested) |
| *(none — not in `ProviderRequest.params`)* | `data.passengers` — always `[{"type": "adult"}]`; see Known Limitations |

`Duffel-Version: v2` is sent as a required protocol header — not an
auth header, so it's set directly in `build_request()`, not by
`authenticate()`. No `Authorization` header is ever set here; `execute()`
merges it in afterward, per the framework's own rule.

## Response Mapping — `parse_response()`

Every field `ai/discovery/flights/flight_scorer.py`,
`flight_reasoner.py`, and `flight_risk_assessor.py` read from a
`MockFlightProvider.search()` result is produced identically from a
Duffel offer — this is the adapter's actual contract, stricter than
"returns *a* `ProviderResult`":

| Internal field | Derived from |
|---|---|
| `airline` | `offer.owner.name` |
| `flight_number` | `{first_segment.marketing_carrier.iata_code}{first_segment.marketing_carrier_flight_number}` |
| `cabin_class` | `first_segment.passengers[0].cabin_class`, mapped down (`premium_economy` -> `business`) |
| `stops` | `len(outbound_slice.segments) - 1` |
| `layover_duration` / `_layover_minutes` | Gaps between consecutive segments' `arriving_at`/`departing_at` |
| `departure_time` / `arrival_time` | First/last segment's `departing_at`/`arriving_at`, `HH:MM` |
| `total_duration` / `_total_duration_minutes` | `outbound_slice.duration` (ISO 8601, e.g. `PT8H30M`), parsed |
| `estimated_price` / `currency` | `offer.total_amount` / `offer.total_currency` |
| `baggage_included` | Any `type == "checked"` baggage entry with `quantity > 0` on the first segment's first passenger |
| `refundability` | `"refundable"` if `conditions.refund_before_departure.allowed` else `"non_refundable"` |
| `flexibility` | `"flexible"` if `conditions.change_before_departure.allowed` else `"fixed"` |
| `departure_date` | Date portion of the first segment's `departing_at` |
| `return_date` | Always `None` — Duffel's return-leg detail isn't re-derived; the internal field is metadata pass-through in the mock provider too |
| `_price_anchor` | Set equal to `estimated_price` — see Known Limitations |

Nothing Duffel-shaped (an `off_...` ID, a `slices`/`segments` object, a
`conditions` block) ever leaves `parse_response()` — every Discovery
Layer field is a plain `str`/`float`/`bool`/`int`, exactly matching
`MockFlightProvider.search()`'s output shape.
`test_duffel_flight_provider.py::TestResponseMapping::test_every_option_reaches_the_flight_scorer_without_error`
proves this directly by running real `flight_scorer`/`flight_reasoner`/
`flight_risk_assessor` code against Duffel-shaped output.

## Error Handling

| Failure | How it's produced | Result |
|---|---|---|
| Authentication failure | Duffel HTTP 401/403 | `ProviderAuthenticationError` — `BaseLiveProvider`'s default status mapping, unchanged |
| Timeout | Duffel HTTP 408 | `ProviderTimeoutError` — retryable |
| Rate limit | Duffel HTTP 429 | `ProviderRateLimitError` — gateway fails over instead of retrying in place |
| Invalid request | Duffel HTTP 422 with `{"errors": [{"type": "validation_error", ...}]}` | `ProviderValidationError` — the generic status mapping alone can't tell a 422 apart from any other non-5xx failure, so `DuffelFlightProvider.map_error()` inspects the stashed response body (see below) and reclassifies it; never retried |
| Provider unavailable | Duffel HTTP 5xx | `ProviderUnavailableError` — retryable, then failover |
| Malformed response | Missing `data`/`offers`, non-list `offers`, or an offer missing an expected key (caught as `KeyError`/`IndexError`/`TypeError`/`ValueError`) | `ProviderResponseError`, raised from `parse_response()` |

**Why `map_error()` needs the response body, not just the exception:**
`BaseLiveProvider._check_response_status()` only has the HTTP status
code to work with — it can't distinguish Duffel's `validation_error`
from any other non-5xx failure it doesn't already recognise, so a 422
falls through to a generic `ProviderResponseError`. `map_error(error)`
only ever receives that exception, not the original `TransportResponse`
— so `DuffelFlightProvider` overrides `send_request()` to stash the
response on `self._last_response` before returning it (every call goes
through `send_request()`, success or failure), giving `map_error()`
something to inspect. This is the same override point
`docs/LIVE_PROVIDER_ADAPTER_GUIDE.md`'s step 5 describes, made concrete.

## Test Strategy

No real network call anywhere — `travelos/tests/test_duffel_flight_provider.py`
and `travelos/tests/test_duffel_gateway_integration.py` (35 tests) use
`FakeTransport` with response bodies shaped per Duffel's public API
documentation (`https://duffel.com/docs/api/offer-requests`), not
captured from a real account:

- Request mapping (one-way, round-trip, auth header merging, no auth
  leakage into `build_request()`'s own output)
- Response mapping (direct and one-stop offers, multi-offer responses,
  `source_metadata`, and the flight-scorer compatibility test above)
- Malformed response handling (missing keys, wrong types, non-dict body)
- Every standard error type (401/408/429/500/503) via the framework's
  existing status-code mapping
- Duffel-specific 422 body reclassification, including a direct
  assertion that the reclassified error is genuinely non-retryable
  under `RetryPolicy`, not just differently named
- Health checks (`MISCONFIGURED` without a token, `AVAILABLE` with one,
  no token value ever appears in `health_check_detailed()`'s string form)
- `environment` defaults to `SANDBOX`; `MOCK` still raises `ValueError`
  (inherited, unchanged)
- Registration, environment-based selection (`MOCK` never selects
  Duffel; `SANDBOX` does), and live-to-mock failover — mirroring
  `travelos/tests/test_live_provider_gateway_integration.py`'s existing
  pattern for the concrete adapter
- End-to-end compatibility through `GatewayFlightProvider.search()` —
  the actual Discovery-layer entry point, unmodified

## Enabling It

Registration is **still not automatic** — unlike the T-025 mock
providers (`travelos/intelligence_gateway/discovery_adapters.py`'s
`register_default_providers()`, called at import time),
`register_duffel_flight_provider()` must be called explicitly and
requires a `Transport` to be supplied by the caller. As of T-037, a
real one exists:

```python
from travelos.live_providers.adapters.duffel_flight_provider import register_duffel_flight_provider
from travelos.live_providers.httpx_transport import HttpxTransport

register_duffel_flight_provider(transport=HttpxTransport())
```

This is a deliberate difference from the mock-provider pattern: mock
providers are always safe to auto-register (they never make an
external call), but auto-registering `DuffelFlightProvider` at import
time — even now that `HttpxTransport` exists — would make every app
boot capable of a real outbound call to Duffel the moment
`PROVIDER_ENVIRONMENT=SANDBOX`/`PRODUCTION` is set, without an explicit
decision point. Explicit registration keeps that decision deliberate.

T-037 proved `HttpxTransport` works — one real call through this exact
registration pattern reached Duffel's SANDBOX API and returned 235
offers (`docs/FIRST_LIVE_PROVIDER.md`) — but did **not** wire it into
`services/api/app/main.py`'s startup. Doing so, gated by
`PROVIDER_ENVIRONMENT` and `DUFFEL_API_TOKEN` both being set, plus
checking off `docs/PRODUCTION_READINESS.md` for this provider, remains
the next step before any real application traffic reaches Duffel.

## Known Limitations

See `docs/FIRST_LIVE_PROVIDER.md`'s "What Remains Before Real
Production Use" — most of `docs/PRODUCTION_READINESS.md`'s checklist,
application-startup wiring, adult-only passenger count, and
`_price_anchor` set to each offer's own price rather than an
independent baseline. The real-transport and real-sandbox-call items
are now closed (T-037).
