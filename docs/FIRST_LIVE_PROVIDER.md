# First Live Provider — Duffel Flight Provider

T-027 — the first real vendor adapter built on the Live Provider
Framework (T-026, `docs/LIVE_PROVIDER_FRAMEWORK.md`). Answers the
question T-026 deliberately left open: which vendor, and why. **Not
connected to a real network anywhere in this repository — see "What
Remains Before Real Production Use" below.**

See also `docs/FLIGHT_PROVIDER_INTEGRATION.md` (how the adapter is
built and how to enable it) and `docs/ADR/ADR-022-first-live-provider.md`.

## Provider Evaluation

Four flight-data vendors were evaluated against the criteria this
task's brief specifies. Amadeus was deliberately not assumed to be
available — see the original T-027 constraints.

| Criterion | **Duffel** | Amadeus for Developers | Kiwi.com (Tequila) | Skyscanner |
|---|---|---|---|---|
| Sandbox availability | Instant self-serve signup; free `duffel_test_...` token, no approval wait | Self-serve signup; free sandbox app credentials, no approval wait | Requires an application + manual approval before any key is issued | Partner-only API access; no public self-serve signup at all |
| Documentation quality | Modern REST/JSON docs, versioned (`Duffel-Version` header), OpenAPI spec, live example responses | Good, but split across an ageing SOAP-flavoured GDS lineage in places; REST layer documented separately | Adequate but noticeably thinner, fewer worked examples | N/A — no public developer docs since partner-API-only |
| Authentication complexity | Single static bearer token — `Authorization: Bearer duffel_test_...` | **OAuth2 client-credentials** — `POST` to a token endpoint, cache + refresh a short-lived bearer token | API key in a custom header | Unknown — never reached, no self-serve access |
| Coverage | 300+ airlines via NDC content plus traditional/GDS-sourced fares | Very broad (major GDS-backed), strong on legacy full-service carriers | Broad on low-cost/OTA-style routes, weaker on NDC/full-service content | Broad, but inaccessible here |
| Commercial suitability | Transparent pay-per-booking pricing; **test mode is free and has no request-volume ceiling for development** | Free tier for sandbox; production requires a commercial agreement | Requires a commercial agreement even to move past the sandbox tier for meaningful volume | Requires an existing commercial partnership just to get sandbox credentials |
| Future scalability | Same API shape for test and live mode — swapping `duffel_test_...` for `duffel_live_...` requires no code change | Same API shape for test/production, but the OAuth2 exchange this framework doesn't implement (TD-022) is a hard blocker regardless of credential availability | Same concern as commercial suitability — sandbox-to-production is gated by the same approval process | N/A |
| Licensing/commercial restrictions | None to obtain or use a sandbox token; production requires standard commercial terms only when *making bookings*, not for read-only search | None to obtain sandbox credentials; production requires a signed IATA/GDS-style agreement in most cases | Requires signing terms before receiving *any* usable key | N/A |

## Recommendation: Duffel

**Duffel is the only vendor in this comparison an engineer without a
pre-existing account or a business-development relationship can
actually integrate against today.** The deciding factor is
authentication, not coverage or price: this repository's
`BearerTokenAuthStrategy` is fully implemented and tested; its
`OAuth2ClientCredentialsAuthStrategy` is an interface only — `headers()`
unconditionally raises `ProviderConfigurationError` because no real
token exchange exists (TD-022, ADR-021). Amadeus — the vendor this
task's constraints explicitly say not to assume — is the clearest
illustration of that gap: even with a valid Amadeus sandbox
application, this framework cannot authenticate against it until
someone implements `fetch_token()` as its own follow-on task. Kiwi and
Skyscanner fail an earlier gate — neither offers genuinely self-serve
sandbox access at all.

Duffel's coverage and commercial terms are also simply good, not just
"good enough by elimination" — NDC-plus-traditional content from 300+
airlines, a free unlimited test mode, and a production path that
requires no code change, only swapping the token prefix and the
`environment` argument from `SANDBOX` to `PRODUCTION`.

## What Was Built

- `travelos/live_providers/adapters/duffel_flight_provider.py` —
  `DuffelFlightProvider(BaseLiveProvider)`, `register_duffel_flight_provider()`
- `travelos/tests/test_duffel_flight_provider.py`,
  `travelos/tests/test_duffel_gateway_integration.py` — 35 new tests,
  all against `FakeTransport` with Duffel-shaped canned responses built
  from Duffel's public API documentation, never real inventory
- `docs/FLIGHT_PROVIDER_INTEGRATION.md`, `docs/ADR/ADR-022-first-live-provider.md`
- Updated: `docs/PRODUCTION_READINESS.md`, `docs/TASK_TRACKER.md`, `.env.example`, `README.md`

No file under `ai/discovery/flights/`, `ai/trip_brain/`, or
`services/api/app/domains/flights/` was changed — the adapter's output
is shaped to match `MockFlightProvider.search()`'s existing contract
exactly, so nothing above the Intelligence Gateway needed to change
(see `docs/FLIGHT_PROVIDER_INTEGRATION.md`'s Response Mapping section).

## What Remains Before Real Production Use

Nothing in this repository has made a real network call to Duffel or
any other vendor. Before this adapter could serve a real traveller
request:

1. **A real HTTP transport.** Only `FakeTransport` exists (TD-021,
   inherited unchanged from T-026). `DuffelFlightProvider` takes any
   `Transport`, so this is additive — no adapter code changes — but it
   is genuinely new code that has never run, and per the same
   reasoning ADR-021 gave for deferring it in T-026: nothing in this
   task's scope can safely exercise a real transport without a live
   network call, which the task's own constraints forbid.
2. **A real Duffel sandbox account and test-mode token**, set as
   `DUFFEL_API_TOKEN`, to exercise the adapter against Duffel's actual
   `SANDBOX` environment rather than only `FakeTransport` — the
   Sandbox Validation section of `docs/PRODUCTION_READINESS.md`.
3. **The full `docs/PRODUCTION_READINESS.md` checklist**, per-provider,
   for `duffel_flight_provider` specifically — secrets, monitoring,
   rate limits tuned to Duffel's documented limits, a second
   engineer's review of the request/response mapping against Duffel's
   real API docs, and a rollback plan.
4. **Passenger count.** `GatewayFlightProvider.search()`'s signature
   (unchanged, matching `MockFlightProvider.search()`) does not accept
   an `adults` count, so `build_request()` always sends exactly one
   adult passenger to Duffel — a pre-existing Discovery-layer
   limitation this task did not introduce and was explicitly
   constrained not to fix (no Discovery Layer redesign).
5. **Multi-offer price anchoring.** `_price_anchor` is set equal to
   each offer's own price (no independent baseline exists from a
   single `offer_requests` call) — this only affects one DNA-based
   scoring heuristic (`budget_consciousness`, `flight_scorer.py`) and
   never affects `estimated_price` itself.
