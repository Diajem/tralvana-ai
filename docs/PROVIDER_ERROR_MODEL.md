# Provider Error Model

The standard error types every provider — mock (T-025) or live (T-026)
— raises, and how they map into the Intelligence Gateway's retry and
failover model (`docs/CACHING_AND_FAILOVER.md`). Defined once, in
`travelos/intelligence_gateway/exceptions.py`, and re-exported from
`travelos/live_providers/errors/` — **one shared hierarchy, not two
parallel ones.**

## The Seven Standard Types

| Type | Retryable? | Meaning |
|---|---|---|
| `ProviderAuthenticationError` | No | Credentials rejected or missing (HTTP 401/403) |
| `ProviderValidationError` | No | The request itself is invalid for this provider — retrying reproduces the same failure |
| `ProviderConfigurationError` | No | The provider is not set up correctly (e.g. a missing required secret) |
| `ProviderRateLimitError` | No — failover instead | The provider reports it is rate-limited (HTTP 429); the gateway tries the next eligible provider rather than retrying the same one |
| `ProviderTimeoutError` | **Yes** | The provider took too long to respond (HTTP 408) |
| `ProviderUnavailableError` | **Yes** | The provider could not be reached, or returned a server error (HTTP 5xx) |
| `ProviderResponseError` | **Yes** | The provider responded, but the body could not be understood — often a transient vendor glitch, not a structural problem |

## Naming Reconciliation

T-025 shipped `ProviderRateLimitedError` and `ProviderMisconfiguredError`
first, with their own docs, retry-policy wiring, and tests already
committed. T-026's brief names the same two concepts
`ProviderRateLimitError` and `ProviderConfigurationError`. Rather than
rename the originals (breaking already-shipped code) or maintain two
divergent types for one concept, `travelos/intelligence_gateway/exceptions.py`
makes both names resolve to the exact same class:

```python
ProviderRateLimitError = ProviderRateLimitedError
ProviderConfigurationError = ProviderMisconfiguredError
```

Use whichever name reads better in context — they are `is`-identical,
not merely `==`-equal.

## HTTP Status → Error Mapping

`BaseLiveProvider._check_response_status()` (inherited by every live
provider) applies this mapping automatically, before `parse_response()`
is ever called:

| Status | Error |
|---|---|
| 200–299 | (success — `parse_response()` proceeds) |
| 401, 403 | `ProviderAuthenticationError` |
| 408 | `ProviderTimeoutError` |
| 429 | `ProviderRateLimitError` |
| 500–599 | `ProviderUnavailableError` |
| any other non-2xx | `ProviderResponseError` |

A concrete provider can override `map_error()` to translate a vendor's
own structured error body (e.g. `{"error": {"code": "invalid_slice"}}`)
into a more specific type after this default mapping — see
`docs/LIVE_PROVIDER_ADAPTER_GUIDE.md`'s step 5.

## Retry Behaviour

`travelos/intelligence_gateway/retry_policy.py`'s `RetryPolicy` (T-025,
extended by T-026 for `ProviderResponseError`):

```python
_DEFAULT_RETRYABLE = (
    ProviderUnavailableError, ProviderTimeoutError, ProviderResponseError,
    ConnectionError, TimeoutError,
)
_NEVER_RETRYABLE = (
    ProviderValidationError, ProviderAuthenticationError, ProviderMisconfiguredError,
)
```

`_NEVER_RETRYABLE` always wins, even if a caller widens
`retryable_exceptions` to include one of those three — retrying an
invalid request, rejected credentials, or a missing secret only
reproduces the same failure. `ProviderRateLimitError` is deliberately in
neither list: the gateway doesn't retry a rate-limited provider in place
at all, it fails over to the next eligible provider immediately
(`docs/CACHING_AND_FAILOVER.md`).

## Failover Behaviour

Any raised error — retryable or not, once retries (if applicable) are
exhausted — causes `failover_policy.run_with_failover()` to record it as
a warning and try the next eligible provider (`docs/PROVIDER_SELECTION.md`'s
fallback order). If every eligible provider fails, the gateway returns a
clear `ProviderStatus.UNAVAILABLE` `ProviderResult` naming every attempt
— it never raises out of `IntelligenceGateway.execute()` itself.

## Why `map_error()` Exists Separately From the Status Mapping

`_check_response_status()` only knows the HTTP status code — a generic,
protocol-level signal. `map_error()` is the hook for *body-level*
translation a vendor's own error format requires (e.g. distinguishing
"invalid airport code" from "invalid date" within the same 400 response)
— see `docs/LIVE_PROVIDER_ADAPTER_GUIDE.md`.
