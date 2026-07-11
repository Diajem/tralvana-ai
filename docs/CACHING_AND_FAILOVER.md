# Caching, Retry, Failover, and Rate Limiting

How `IntelligenceGateway.execute()` behaves when a provider is slow,
fails, or is over quota. See `docs/INTELLIGENCE_GATEWAY.md` for where
this sits in the overall request flow.

## Cache Policy (`cache_policy.py`)

**In-memory only — no Redis.** `InMemoryCachePolicy` is a plain dict,
matching every other in-memory store already in this codebase
(`ConversationSession`'s session store, the in-memory Goal/Trip
repositories).

- **Cache key** — `build_cache_key(capability, operation, params)` hashes
  the JSON-normalised (sorted-keys) params, so identical requests with
  differently-ordered kwargs still hit the same key, and different
  requests never collide.
- **TTL** — capability-specific defaults (`DEFAULT_TTL_SECONDS`):

  | Capability | TTL | Category |
  |---|---|---|
  | Flights | 5 min | short |
  | Accommodation | 5 min | short |
  | Currency | 5 min | short |
  | Weather | 30 min | medium |
  | Events | 15 min | — |
  | Budget | 15 min | — |
  | Maps | 1 hour | longer |
  | Destinations | 1 hour | longer |
  | Visa | 24 hours | longer, clearly timestamped |

  Every result carries its own `retrieved_at`/`expires_at` regardless of
  TTL length, so staleness is always visible to a caller, never silent —
  particularly important for Visa, where a 24-hour TTL is a performance
  choice, not a claim that entry requirements are only rechecked daily.

- **Stale-data indication** — `get_stale(key)` returns the last cached
  value even past its TTL, with `.stale = True` set. Used only when every
  provider has just failed (see Failover below) — never as a substitute
  for a fresh call under normal conditions.
- **Bypass** — `ProviderRequest.bypass_cache = True` skips both the read
  and the write for that one call.
- **Global disable** — `ConfigurationManager.cache_enabled` (env var
  `PROVIDER_CACHE_ENABLED`, default `true`).

## Retry Policy (`retry_policy.py`)

**Stdlib only — no external retry library** (none is present in
`services/api/requirements.txt`, and none is added here).

- **Max attempts** — `RetryPolicy.max_attempts`, default `3`.
- **Delay strategy** — `delay_for_attempt(attempt)`, exponential:
  `base_delay_seconds * backoff_multiplier ** (attempt - 2)`, `0` for the
  first attempt. `base_delay_seconds` defaults to `0.0` — real delay is
  opt-in per gateway instance, keeping tests and local dev fast and
  deterministic by default.
- **Retryable error types** — `ProviderUnavailableError`,
  `ProviderTimeoutError`, `ConnectionError`, `TimeoutError`.
- **Never retried, by design** — `ProviderValidationError`,
  `ProviderAuthenticationError`, `ProviderMisconfiguredError` always
  return `False` from `is_retryable()`, even if a caller widens
  `retryable_exceptions` to include them — retrying an invalid request or
  bad credentials only reproduces the same failure.

## Failover Policy (`failover_policy.py`)

`run_with_failover(providers, request, call)` — a small, independently
testable loop, deliberately agnostic of retry/rate-limit/cache mechanics
(the gateway supplies `call`, already wrapped with those concerns):

1. Try each eligible provider in order (the order `ProviderSelector`
   already produced — see `docs/PROVIDER_SELECTION.md`).
2. On success: return immediately. Every **prior** provider's failure
   message is preserved in the winning result's `warnings` — the
   original failure is never discarded, only superseded.
3. On failure: record the failure as a warning, try the next provider.
4. If every provider fails: `FailoverOutcome.all_failed` is `True`,
   `provider_used` is `None`, and every failure is in `warnings`.

The gateway turns a total failure into either a stale-cache result (if
one exists) or a clear `UNAVAILABLE` `ProviderResult` naming every
attempted provider — never a raised exception a Discovery module would
have to catch.

## Rate Limit Policy (`rate_limit_policy.py`)

**In-memory, per-provider — no distributed rate limiter.**
`RateLimitTracker`:

- **Unconfigured provider is unlimited** — `configure()` is opt-in; every
  mock provider registered by this task has no configured limit.
- **`check(provider_name)`** — `True` if a call is currently allowed.
- **`record_call(provider_name)`** — decrements remaining quota.
- **`status_for(provider_name)`** — `RateLimitState(limit, remaining, reset_at)`,
  or `None` if unconfigured.
- **Window reset** — quota fully replenishes once `reset_at` passes; the
  next `check()`/`record_call()` after that re-derives a fresh window.

**Rate-limited failover**: inside the gateway's per-provider call
(`IntelligenceGateway._call_provider`), a `check()` failure **raises**
`ProviderRateLimitedError` rather than returning a result — this is what
makes `run_with_failover` treat it exactly like any other provider
failure and move to the next eligible provider, rather than returning a
`RATE_LIMITED` result as if it were a successful answer.

## Observability

Every stage above logs through the existing `TravelLogger`
(`travelos/logging/travel_logger.py`, `for_service("IntelligenceGateway")`
/ `for_service("ProviderRegistry")`): provider registered, cache hit/
miss, retry attempt (with delay), rate-limited skip, failover to a
fallback provider, final provider executed (with latency and status),
and total failure. No personal data or secret value is ever included in
a log line — only provider names, capability names, statuses, and
timings.
