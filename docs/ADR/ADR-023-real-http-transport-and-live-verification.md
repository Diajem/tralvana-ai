# ADR-023: Real HTTP Transport and First Live Provider Verification

**Date**: 2026-07-12
**Status**: Accepted
**Sprint**: 2/3 boundary (T-037)

## Context

T-026 deferred a real `Transport` implementation (TD-021) — only
`FakeTransport` existed, and ADR-021's own reasoning was that nothing
in that task's scope could safely exercise a real transport without a
live network call its constraints forbade. T-027 built
`duffel_flight_provider` fully tested against `FakeTransport`, same
constraint, same deferral (`docs/FIRST_LIVE_PROVIDER.md`'s "What
Remains Before Real Production Use"). A real Duffel sandbox token
became available for the first time in this task, changing what could
safely be verified.

## Decision

**`HttpxTransport` is a thin, provider-agnostic `Transport`
implementation — it holds no Duffel-specific logic and no
`SecretReference` of its own.** It translates `TransportRequest` to an
`httpx.Client.request()` call and the resulting `httpx.Response` back
to `TransportResponse`, nothing more. `DuffelFlightProvider` (or any
future `BaseLiveProvider` subclass) is constructed with it exactly as
it was constructed with `FakeTransport` — no adapter code changed.
`httpx==0.28.1` was already a pinned dependency (via FastAPI's
`TestClient`, per ADR-021's own note); no new third-party dependency
was added.

**Unit tests use `httpx.MockTransport`, not a real socket.** `httpx`
ships its own request-interception mechanism for exactly this purpose
— `travelos/tests/test_httpx_transport.py`'s 10 tests exercise request
translation, response translation (including a non-JSON-body fallback
to text), status/header passthrough, and client lifecycle entirely
in-process. This preserves T-027's "never require internet access
during CI" rule while still testing `HttpxTransport` against something
closer to real HTTP semantics than a hand-written stub would be.

**The one live verification call was a manual, uncommitted script, not
a pytest test.** Adding a real-network-dependent test to the automated
suite would violate the same CI-safety rule `HttpxTransport`'s own unit
tests were built to respect. The live call instead ran as a standalone
script (not part of the repository), executed once (twice, after a bug
fix — see below), reporting only `http_status_code`, `gateway_provider_status`,
`request_success`, and `offer_count` — the exact fields requested, and
the only fields printed anywhere during this task.

**Credential safety was enforced by never holding the token past the
point `SecretReference.resolve()` already resolves it, and by
structural (not full-value) diagnosis when the first call failed.**
When the first live call raised `ProviderResponseError`, the response
body was inspected via a bounded-depth recursive walk that replaces
every leaf value with its Python type name (`_key_shape()`/`shape()`
in the verification script) — enough to see field *names* and general
*shape* to diagnose a mapping bug, never enough to see actual itinerary
content, prices, or any other response value. No token, request
header, or full response payload was printed, logged, or committed at
any point.

**The bug found — and the reason `FakeTransport`-only testing couldn't
have found it — was a real vendor behaviour no documentation example
this adapter was built against showed.** Duffel's documented example
responses only ever showed durations as `PT#H#M`. A real `SANDBOX`
response for one of 235 offers returned `duration: "P1DT5H15M"` — a
day component, for a connection whose total time exceeds 24 hours.
`_ISO8601_DURATION_RE`/`_parse_iso8601_duration()` in
`duffel_flight_provider.py` only matched `PT...`, so this one offer's
mapping raised `ValueError`, which `parse_response()`'s per-offer
`try/except` correctly caught and re-raised as `ProviderResponseError`
for the *entire* batch (all 235 offers, not just the one) — proving the
error-handling contract worked exactly as designed even though the
regex it protected was incomplete. Fixed by extending the regex to
accept an optional `(\d+)D` component and adding its minutes to the
total; the fix is validated by a new unit test built from the exact
real-world value (`P1DT5H15M`), not a hypothetical.

**After the fix, a second live call succeeded completely:** HTTP 201,
`gateway_provider_status: AVAILABLE`, `request_success: True`,
`offer_count: 235` — every one of 235 real offers mapped cleanly
through `_map_offer()` into the internal flight-option shape
`ai/discovery/flights/flight_scorer.py` and friends already expect,
with zero changes to any Discovery-layer file.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Add the live call as a `pytest` test, skipped unless `DUFFEL_API_TOKEN` is set | Still risks accidentally running in CI or a contributor's environment without a token-presence guard being airtight across all runners; a manual script makes "this makes a real network call" impossible to miss |
| Print the full response body for debugging the first failure | Directly against the "safe diagnostics only" instruction this task was scoped under — even sandbox test data isn't printed wholesale; the bounded-depth type-shape technique gave enough signal to fix the bug without it |
| Fix only the specific `P1DT5H15M` value seen, via a special case | Would leave the parser broken for `P2DT3H`, `P1D` alone, or any other day-count; the regex fix generalizes to any day count, matching how the existing hour/minute groups already generalize |
| Auto-register `DuffelFlightProvider` with `HttpxTransport` now that both exist | Out of scope — this task verified the transport works, it was not asked to (and did not) wire application startup; `docs/PRODUCTION_READINESS.md` is still far from fully checked for this provider |

## Consequences

- `travelos/live_providers/httpx_transport.py` — new file, ~60 lines,
  zero new third-party dependencies.
- `travelos/live_providers/adapters/duffel_flight_provider.py` — one
  regex and one parsing function changed
  (`_ISO8601_DURATION_RE`, `_parse_iso8601_duration`) to accept an
  optional day component. No other line changed.
- `travelos/tests/test_httpx_transport.py` — new file, 10 tests.
- `travelos/tests/test_duffel_flight_provider.py` — one new regression
  test for the day-component duration case.
- Zero changes to `travelos/intelligence_gateway/`, `ai/discovery/flights/`,
  `ai/trip_brain/`, or `services/api/app/domains/flights/`.
- `duffel_flight_provider` is still not registered anywhere by default
  — this task closed the "does the real transport work" question, not
  the "should this run in production" one.
- 959 tests pass (948 pre-existing + 11 new), Ruff clean.
- One real, successful HTTP round trip to `https://api.duffel.com` was
  made against Duffel's SANDBOX environment using a user-supplied
  token this task never printed, logged, or persisted anywhere outside
  the gitignored `.env` file it was already configured in.

## Deferred Items

- Application-startup wiring for `duffel_flight_provider` — still a
  manual/explicit registration only.
- The remainder of `docs/PRODUCTION_READINESS.md`'s checklist:
  monitoring integration, rate-limit tuning against Duffel's real
  documented limits, a deliberately malformed live request (Sandbox
  Validation's second item), secret rotation drill, second-engineer
  review, rollback plan.
- `OAuth2ClientCredentialsAuthStrategy.fetch_token()` — unchanged,
  still the blocker for Amadeus or any OAuth2-client-credentials vendor
  (TD-022).
