# Provider Observability

Health checks, request tracing, and usage/cost metrics for live
providers (`travelos/live_providers/{health,tracing,metrics}/`). No new
logging system, no distributed tracing platform, no billing
infrastructure — everything here is built on the existing `TravelLogger`
and plain in-memory Python objects.

## Health Checks

`Provider.health_check() -> ProviderStatus` (T-025) is the minimal,
already-shared contract. `BaseLiveProvider` implements it as: `AVAILABLE`
if the configured `AuthStrategy.is_configured()`, else `MISCONFIGURED`.

`BaseLiveProvider.health_check_detailed() -> ProviderHealthResult` is a
richer result, **not** added to the shared `Provider` contract in
`travelos/intelligence_gateway/` — doing so would create a dependency
from the gateway package into `travelos/live_providers/`, inverting the
direction this framework depends on the gateway (see
`travelos/live_providers/__init__.py`). Consumers that want the richer
detail (the diagnostics endpoint) duck-type:
`getattr(provider, "health_check_detailed", None)`.

```python
@dataclass
class ProviderHealthResult:
    provider_name: str
    capability: Capability
    environment: ProviderEnvironment
    status: ProviderStatus
    checked_at: str
    latency_ms: float = 0.0
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)  # safe only
```

`metadata` is safe-only — e.g. `{"auth_configured": True}` — never a
secret value. Verified by
`travelos/tests/test_base_live_provider.py::TestHealthChecks::test_detailed_health_never_includes_the_secret_value`.

## Request Tracing

`travelos/live_providers/tracing/request_trace.py`. Every field this
task's brief specifies, and nothing more:

| Field | Source |
|---|---|
| `internal_request_id` | A fresh UUID per `execute()` call |
| `provider_request_id` | From `ProviderResult.source_metadata`, if the vendor returned one — optional |
| `provider_name` / `capability` | From the provider itself |
| `started_at` / `ended_at` | ISO timestamps |
| `latency_ms` | Wall-clock time for the whole `execute()` call |
| `status` | The final `ProviderResult.status`, or `"error"` on failure |

Logged once, on `finish()`, through `TravelLogger.for_service("ProviderTracing")`
— never a new logging system. **Never logged**: traveller personal data,
credentials (raw or otherwise), or a full request/response payload —
only the fields listed above ever reach a log line.

`BaseLiveProvider.execute()` starts a trace at the top of the lifecycle
and finishes it in both the success and failure paths — a concrete
provider never has to call tracing code itself.

## Usage and Cost Metrics

`travelos/live_providers/metrics/provider_metrics.py`. **Not a billing
system** — a lightweight, in-memory counter per provider name:

```python
@dataclass
class ProviderMetricsSnapshot:
    provider_name: str
    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    rate_limited_count: int = 0
    total_latency_ms: float = 0.0
    last_latency_ms: float = 0.0
    estimated_cost_usd: float = 0.0

    @property
    def average_latency_ms(self) -> float: ...
    @property
    def success_rate(self) -> float: ...
```

`ProviderMetricsTracker.record_success(provider_name, latency_ms, cost_usd=None)`,
`.record_failure(provider_name)`, `.record_rate_limited(provider_name)` —
called automatically by `BaseLiveProvider.execute()` on every call, so a
concrete provider never has to remember to record its own metrics.

**No price is ever invented.** `estimated_cost_usd` starts at `0.0` and
only accumulates a value a concrete adapter explicitly passes via
`cost_usd=`. Nothing in this framework assumes or hardcodes a
per-request price for any vendor — see
`travelos/tests/test_provider_metrics.py::TestCostReporting`.

A shared, module-level `provider_metrics` instance
(`travelos.live_providers.metrics.provider_metrics.provider_metrics`) is
the default every `BaseLiveProvider` records into unless a caller injects
a different tracker (e.g. for test isolation).

## Diagnostics Integration

`GET /internal/providers/status` (`services/api/app/routers/internal.py`)
reads all three observability surfaces for every registered provider,
mock and live alike:

- `provider_type` (`"MOCK"` / `"LIVE"`, derived from `provider.environment`)
- `authentication_configured` (duck-typed `provider.auth_configured`;
  `True` for every mock provider, since mocks need no credential)
- `status` / `health` (from `health_check()`, unless
  `ConfigurationManager.provider_healthcheck_enabled` is `False`, in
  which case it reports `"DISABLED"` / `"unknown"` without calling
  `health_check()` at all)
- `last_check_time` (the timestamp this diagnostics call itself ran)
- `request_count` / `failure_count` (from `provider_metrics.snapshot_for()`
  — `0`/`0` for a provider that has never recorded metrics, e.g. any
  T-025 mock provider, since only `BaseLiveProvider.execute()` records
  automatically today)

No secret value, credential, or full payload ever appears in this
response — verified by
`services/api/tests/test_internal_diagnostics.py::test_no_secret_or_credential_field_present_anywhere`.
