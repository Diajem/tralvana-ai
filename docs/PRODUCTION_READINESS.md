# Production Readiness Checklist

A practical checklist for taking any live provider built on
`BaseLiveProvider` (`docs/LIVE_PROVIDER_FRAMEWORK.md`) from a
`SANDBOX`-environment adapter tested against `FakeTransport` to a real
`PRODUCTION` credential serving live traveller requests. **Nothing in
this repository has passed this checklist yet** — T-025 and T-026 are
infrastructure only, and T-027's `duffel_flight_provider`
(`docs/FIRST_LIVE_PROVIDER.md`) is a fully-built, fully-tested adapter
that has still never made a real network call and is not registered by
default; it starts this checklist at zero, same as any other provider.

Use this per-provider, not once for the whole system — a new vendor
integration (e.g. adding Amadeus once `OAuth2ClientCredentialsAuthStrategy`
has a real token exchange, TD-022) goes through this checklist again on
its own merits.

## Secrets

- [ ] Every credential is loaded through `SecretReference`
      (`docs/SECRET_MANAGEMENT.md`) — never hardcoded, never committed
- [ ] `.env.example` lists the required env var name(s) with an empty
      placeholder — real values live only in the deployment environment's
      secret store
- [ ] `SecretReference.resolve()` is called only immediately before use
      (building an outbound header) — never stored on a long-lived object
- [ ] Confirmed via `describe()`/`is_present()` that no code path ever
      logs or returns the raw value (`docs/SECRET_MANAGEMENT.md`'s rules)
- [ ] Secret rotation plan exists and has been exercised at least once in
      SANDBOX (old value revoked, new value deployed, provider recovers
      without a code change)

## Authentication

- [ ] The chosen `AuthStrategy` (`docs/PROVIDER_AUTHENTICATION.md`)
      matches the vendor's real scheme exactly
- [ ] If OAuth2 client-credentials: the token exchange is actually
      implemented (T-026 ships an interface only —
      `OAuth2ClientCredentialsAuthStrategy.headers()` raises until a real
      `fetch_token()` is added) and token refresh-before-expiry is handled
- [ ] `health_check()` correctly reports `MISCONFIGURED` when the
      credential is absent or rejected, not `AVAILABLE`

## Provider Contract

- [ ] `provider_name` is unique across the whole registry
- [ ] `environment` is `SANDBOX` or `PRODUCTION` — never `MOCK`
- [ ] `priority` is set deliberately relative to any other provider for
      the same capability (docs/PROVIDER_SELECTION.md)
- [ ] `build_request()`/`parse_response()` own 100% of the vendor-specific
      field mapping — nothing vendor-shaped has leaked into
      `ai/shared/agent_result.py` or any Discovery domain model
      (`docs/LIVE_PROVIDER_ADAPTER_GUIDE.md`'s checklist)

## Health Checks

- [ ] `health_check()` is cheap and synchronous — no network call inside
      it beyond what `is_configured()` already does
- [ ] `health_check_detailed()`'s `metadata` field contains no secret
      value (verified once by test, per provider)
- [ ] `GET /internal/providers/status` shows the provider as `LIVE`,
      correctly reports `authentication_configured`, and its `status`
      matches reality

## Monitoring

- [ ] `ProviderMetricsTracker` counts (request/success/failure/
      rate-limited, latency) are wired to whatever external monitoring
      this deployment uses (not built by T-025/T-026 — see
      docs/PROVIDER_OBSERVABILITY.md's Diagnostics Integration section
      for the read surface to scrape)
- [ ] Alerting exists for a sustained failure rate, not just individual
      failures (a single failed request is expected and handled by
      retry/failover; a sustained pattern is not)
- [ ] Request tracing (`docs/PROVIDER_OBSERVABILITY.md`) is confirmed
      flowing into whatever log aggregation this deployment uses

## Retries

- [ ] `RetryPolicy.max_attempts` and delay strategy are tuned for this
      vendor's documented rate limits and typical latency — the
      framework default (`3` attempts, `0` base delay) is a
      development-safe default, not a production tuning
- [ ] Confirmed the vendor's own documented "safe to retry" guidance
      matches this framework's retryable/non-retryable classification
      (`docs/PROVIDER_ERROR_MODEL.md`) — override `map_error()` if not

## Failover

- [ ] At least one fallback provider (even the existing mock, temporarily)
      is registered for the same capability so a live-provider outage
      degrades gracefully rather than failing the whole capability
- [ ] Failover has been exercised deliberately in SANDBOX (force the live
      provider to fail, confirm the mock or a secondary live provider
      answers instead)

## Rate Limits

- [ ] `RateLimitTracker.configure()` matches the vendor's documented
      real limits, not a guess
- [ ] Confirmed rate-limit exhaustion triggers failover
      (`docs/CACHING_AND_FAILOVER.md`) rather than a hard failure

## Logging

- [ ] No traveller personal data appears in any provider log line —
      spot-checked against a real request shape, not just the mock
      request shapes this framework's own tests use
- [ ] No credential, raw or partial, appears in any log line
      (`docs/PROVIDER_OBSERVABILITY.md`'s tracing rules)
- [ ] Log volume at production traffic levels has been estimated and is
      acceptable for this deployment's log storage/cost

## Privacy

- [ ] Confirmed what traveller data this vendor actually receives (e.g.
      name, passport number, payment details) and that it's the minimum
      necessary for the request
- [ ] Confirmed this vendor's own data-handling terms are compatible
      with this product's privacy commitments and applicable regulation
      (GDPR Article 9 for passport/travel-document data, per
      `docs/CODING_STANDARDS.md`'s existing PII-logging rule)

## Security

- [ ] Outbound requests use TLS to the vendor's real endpoint (not
      `.invalid` or any other non-resolving placeholder — those exist
      only in this framework's tests/template)
- [ ] Credential storage in the deployment environment has been reviewed
      (secret manager, not a plain environment file, for `PRODUCTION`)
- [ ] Dependency on any new HTTP client library added for a real
      `Transport` implementation has been through the normal dependency
      review this repository already requires

## Cost Controls

- [ ] If the vendor charges per request, `record_success(..., cost_usd=...)`
      reports a real, vendor-confirmed figure — never an invented one
      (`docs/PROVIDER_OBSERVABILITY.md`)
- [ ] A request-volume ceiling or budget alert exists before enabling
      unrestricted traffic to a paid vendor

## Sandbox Validation

- [ ] Every method in the lifecycle (`build_request`, `send_request`,
      `parse_response`, `map_error`, `health_check`) has been exercised
      against the vendor's real `SANDBOX` environment, not only
      `FakeTransport`
- [ ] At least one deliberately malformed/error-triggering request has
      been sent to `SANDBOX` and confirmed to map to the correct
      standard error type

## Production Approval

- [ ] Every item above is checked for this specific provider
- [ ] A second engineer has reviewed the adapter's `build_request`/
      `parse_response` mapping against the vendor's real API docs
- [ ] Rollback plan exists (how to disable this provider — e.g. via
      `ConfigurationManager.provider_override_for()` — without a
      deploy, if it misbehaves in production)

## Incident Response

- [ ] On-call knows this provider exists and where its diagnostics live
      (`GET /internal/providers/status`)
- [ ] A runbook exists for "this provider is failing" — expected
      behaviour (failover to the mock or another live provider),
      how to confirm failover is actually happening, and how to disable
      the provider if failover isn't sufficient
- [ ] Post-incident, `ProviderMetricsTracker` counts and request traces
      are sufficient to reconstruct what happened without needing
      anything this framework doesn't already capture
