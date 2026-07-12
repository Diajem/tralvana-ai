# Live Provider Framework

T-026 — the reusable base every future live external provider (flights,
weather, maps, ...) must follow, built directly on top of the
Intelligence Gateway (T-025). **Foundation only — no real external API is
connected by this task.**

See also `docs/LIVE_PROVIDER_ADAPTER_GUIDE.md` (how to build a real
adapter), `docs/PROVIDER_AUTHENTICATION.md`, `docs/PROVIDER_ERROR_MODEL.md`,
`docs/PROVIDER_OBSERVABILITY.md`, and
`docs/ADR/ADR-021-live-provider-framework.md`.

## Why This Exists

T-025 built the Intelligence Gateway — provider contract, registry,
deterministic selection, caching, retry, failover, rate limiting — but
every provider registered against it so far is a wrapped mock
(`ai/discovery/*/mock_*_provider.py`). Nothing in this codebase yet
defines *how* a real vendor integration (flight search via Duffel or
Amadeus, weather via a real climate API, ...) should authenticate, map
requests, handle a vendor's specific error shapes, or report its health
— without that shape, every future live integration would reinvent its
own version of all of it. This framework is that shape, built once.

## Architecture

```
Trip Brain
  -> Discovery Module
    -> Intelligence Gateway (travelos/intelligence_gateway/, unchanged)
      -> Live Provider Adapter (BaseLiveProvider subclass)
        -> Authentication (auth/)
        -> Request Mapping (build_request)
        -> External API (Transport — FakeTransport only, today)
        -> Response Mapping (parse_response)
        -> ProviderResult (travelos.intelligence_gateway.provider_result)
```

**The key architectural fact this task confirms, rather than builds**:
`BaseLiveProvider` is a `travelos.intelligence_gateway.provider_contract.Provider`
subclass, exactly like a mock provider. The Intelligence Gateway
(`gateway.py`, `provider_registry.py`, `provider_selector.py`) needed
**zero code changes** to register, select, retry, and fail over a live
provider — it was already fully polymorphic over any `Provider`
implementation. `travelos/tests/test_live_provider_gateway_integration.py`
proves this directly: a mock stub and `ExampleFlightProvider` (the live
provider template) are registered into the same `ProviderRegistry`, and
environment-based selection, health-based eligibility, and live-to-mock
failover all work using T-025's original code, unmodified. See
ADR-021's Decision section.

## Package Layout (`travelos/live_providers/`)

| Path | Responsibility |
|---|---|
| `base_live_provider.py` | `BaseLiveProvider` — the template-method `execute()` lifecycle every concrete provider inherits |
| `transport.py` | `Transport` ABC, `FakeTransport` (deterministic, in-memory — the only transport this task implements) |
| `auth/` | `AuthStrategy` ABC + `ApiKeyAuthStrategy`, `BearerTokenAuthStrategy`, `OAuth2ClientCredentialsAuthStrategy` — see `docs/PROVIDER_AUTHENTICATION.md` |
| `adapters/` | Documents the request/response adapter pattern (expressed via `build_request()`/`parse_response()`, not a second parallel class hierarchy) |
| `errors/` | Re-exports `travelos.intelligence_gateway.exceptions` — one shared error hierarchy for mock and live providers alike |
| `health/` | `ProviderHealthResult` — a richer, structured health-check result |
| `metrics/` | `ProviderMetricsTracker` — request/success/failure/rate-limit counts, latency, optional cost |
| `tracing/` | `RequestTrace` — safe, TravelLogger-backed request tracing |
| `templates/example_flight_provider.py` | `ExampleFlightProvider` — a non-production template proving the whole lifecycle against `FakeTransport` |

## The `execute()` Lifecycle

```
validate -> authenticate -> build_request -> send_request
  -> (check HTTP status) -> parse_response -> ProviderResult
```

Implemented once, concretely, in `BaseLiveProvider.execute()`. A concrete
provider only ever implements two abstract methods:

- **`build_request(request: ProviderRequest) -> TransportRequest`** —
  internal request → vendor-shaped request. Never include an auth header
  here — `authenticate()` supplies those, merged in by `execute()`.
- **`parse_response(response: TransportResponse) -> ProviderResult`** —
  vendor-shaped response → `ProviderResult`. Called only after a
  successful HTTP status check; raise `ProviderResponseError` here if
  the body doesn't have the expected shape.

Everything else has a reusable default a concrete provider can override
only if it needs vendor-specific behaviour:

- **`authenticate()`** — returns headers from the configured
  `AuthStrategy`; raises if not configured.
- **`send_request()`** — calls `self._transport.send()`.
- **`map_error(error)`** — passes a known `ProviderError` through
  unchanged; wraps anything else as `ProviderUnavailableError`. Override
  to translate a vendor's specific error-body shape.
- **HTTP status → error mapping** (`_check_response_status`) —
  401/403 → `ProviderAuthenticationError`, 408 → `ProviderTimeoutError`,
  429 → `ProviderRateLimitError`, 5xx → `ProviderUnavailableError`,
  everything else non-2xx → `ProviderResponseError`.
- **`health_check()`** — `AVAILABLE` if the auth strategy is configured,
  `MISCONFIGURED` otherwise. `health_check_detailed()` wraps this with
  timing and safe metadata (`docs/PROVIDER_OBSERVABILITY.md`).

Every `execute()` call also, automatically:
- Records success/failure/rate-limited into `ProviderMetricsTracker`
  (`metrics/provider_metrics.py`).
- Starts and finishes a `RequestTrace`, logged through the existing
  `TravelLogger` (`tracing/request_trace.py`).
- Stamps `latency_ms`, `request_id`, and `retrieved_at` on the returned
  `ProviderResult`.

None of this needs to be re-implemented by a concrete provider.

## Environments

`BaseLiveProvider` only accepts `ProviderEnvironment.SANDBOX` or
`.PRODUCTION` — constructing one with `MOCK` raises `ValueError`
immediately. `MOCK` stays exclusively on T-025's existing mock providers
(`docs/INTELLIGENCE_GATEWAY.md`).

## Non-Goals

- No real HTTP transport is implemented — only `FakeTransport`. A real
  transport (e.g. `httpx`-backed) is deferred; see
  `docs/ADR/ADR-021-live-provider-framework.md`'s Deferred Items.
- No live OAuth2 token exchange — `OAuth2ClientCredentialsAuthStrategy`
  is an interface only (`docs/PROVIDER_AUTHENTICATION.md`).
- No billing system — `metrics/` only counts and optionally accumulates
  a cost value a caller explicitly reports; no price is invented for any
  vendor.
- No Redis, no distributed tracing platform, no new agent framework —
  every store here is a plain in-memory Python object, matching every
  other in-memory store already in this codebase.
- Trip Brain and Discovery module public APIs are untouched — this
  framework only adds a new kind of `Provider` the existing Intelligence
  Gateway can select, several layers below either of them.
