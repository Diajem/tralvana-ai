# Duffel Sandbox Operations

Day-to-day operation of the live Duffel sandbox flight search feature
(T-038, `docs/LIVE_FLIGHT_SEARCH.md`). For the design decisions behind
it, see `docs/ADR/ADR-024-live-flight-product-integration.md`.

## Enabling Sandbox Mode Locally

1. Get a Duffel sandbox account and a `duffel_test_...` token
   (`docs/FIRST_LIVE_PROVIDER.md` — free, self-serve, no approval wait).
2. In the repo-root `.env` (gitignored — never commit this file):
   ```
   DUFFEL_API_TOKEN=duffel_test_your_real_token_here
   TRALVANA_FLIGHT_PROVIDER_MODE=LIVE_SANDBOX
   ```
3. Restart the API process (`.\scripts\start-api.ps1` on Windows, or the
   repository-root command in `scripts/local-start.md`, picks up
   `.env` on start — registration happens once, at startup, not per
   request).
4. Confirm it registered: `GET /internal/providers/status` should list
   `duffel_flight_provider` with `provider_type: LIVE`,
   `environment: SANDBOX`, `authentication_configured: true`.

If `TRALVANA_FLIGHT_PROVIDER_MODE=LIVE_SANDBOX` is set but
`DUFFEL_API_TOKEN` is missing or empty, **the API process fails to
start** — `FlightProviderMisconfiguredError`, raised by
`configure_flight_provider()` (`travelos/live_providers/flight_provider_bootstrap.py`).
This is deliberate: better to fail loudly at startup than serve
requests from a mode that can never actually work.

## Manual Live Verification

```bash
python scripts/verify_duffel_live_sandbox.py
```

Example output against a working sandbox token:

```
http_status_code: 201
provider_status: AVAILABLE
data_source: DUFFEL_SANDBOX
raw_offer_count: 235
normalised_offer_count: 235
ranked_offer_count: 235
request_id: 7a157ed9-2d02-47e8-85f0-b6ed374e826b
```

`raw_offer_count` vs `normalised_offer_count` differing means some
offers in that response failed to map (partial mapping failure,
`docs/LIVE_FLIGHT_SEARCH.md`'s Failure and Fallback table) — check
application logs for the specific `warnings` the Intelligence Gateway
recorded. This script never prints the token, request headers, or the
raw Duffel response body — only the counts and status above.

**Never run this script (or anything that makes a real Duffel call) in
CI or as part of `pytest`.** It requires a real, working
`DUFFEL_API_TOKEN` and makes an actual outbound HTTPS request to
`https://api.duffel.com`.

## Sandbox Limitations

- **Test data only.** Duffel's `SANDBOX` environment returns realistic
  but non-purchasable inventory — schedules, airlines, and prices are
  shaped like real data but not booking-grade. Never present sandbox
  results as available for purchase (enforced in the frontend — see
  `docs/LIVE_FLIGHT_SEARCH.md`'s Frontend section).
- **One adult passenger only.** `GatewayFlightProvider.search()` never
  received a passenger-count parameter from its callers even before
  T-038 — every live search sends exactly one adult to Duffel
  regardless of what the UI's "Adults" field shows. This is a
  pre-existing Discovery-layer limitation (out of scope, "no Discovery
  Layer redesign").
- **No booking.** Every offer's `provider_offer_id` is preserved
  internally (`FlightOption.provider_offer_id`) for a possible future
  booking task, but nothing in this repository ever calls Duffel's
  order-creation endpoints.
- **Duration format quirks.** Duffel's ISO 8601 durations aren't always
  `PT#H#M` — a long connection can include a day component
  (`P1DT5H15M`), discovered during T-037's live verification and now
  handled (`travelos/live_providers/adapters/duffel_flight_provider.py`).
  If a future response introduces a format this adapter still doesn't
  recognise, the affected offer is skipped (partial mapping failure),
  not the whole batch.
- **Restart-only mode switching.** Changing `TRALVANA_FLIGHT_PROVIDER_MODE`
  requires a process restart — it is read once at startup by
  `configure_flight_provider()`, not per request.

## Failure Behaviour Reference

See `docs/LIVE_FLIGHT_SEARCH.md`'s "Failure and Fallback Behaviour"
table for the full matrix. The short version: a `LIVE_SANDBOX` failure
returns a `503` by default; set
`TRALVANA_FLIGHT_MOCK_FALLBACK_ENABLED=true` to fall back to clearly-labelled
mock data instead of erroring — never a silent, unlabelled substitution.

## Credential Safety

- `DUFFEL_API_TOKEN` is read only via `SecretReference`
  (`travelos/intelligence_gateway/secret_reference.py`) — never
  hardcoded, never logged, never returned in any API response.
- `.env` is gitignored (`.gitignore:.env`) — confirmed before every
  commit in this feature's development; never commit a real token.
- Verified end to end during this task: no secret value appeared in
  any test assertion, log line, HTTP response body, or committed file
  — see `services/api/tests/test_flights_live_search.py`'s
  `TestLiveSandboxEndToEnd`/`TestLiveSandboxFailureBehaviour` classes,
  which assert the token string never appears in a live API response.

## What Remains Before Production

See `docs/LIVE_FLIGHT_SEARCH.md`'s "What Remains Before Production and
Booking" and `docs/PRODUCTION_READINESS.md`'s checklist — most items
are still open. This document covers sandbox operation only.
