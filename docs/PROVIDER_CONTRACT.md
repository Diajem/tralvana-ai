# Provider Contract

The one interface every provider the Intelligence Gateway can call
implements — `travelos/intelligence_gateway/provider_contract.py`. See
`docs/INTELLIGENCE_GATEWAY.md` for how it fits into the gateway as a
whole.

## `Provider`

```python
class Provider(ABC):
    provider_name: str          # property, abstract
    capability: Capability      # property, abstract
    environment: ProviderEnvironment  # property, default MOCK
    priority: int               # property, default 100 (lower runs first)
    metadata: dict[str, Any]    # property, default {}

    def health_check(self) -> ProviderStatus: ...   # default: AVAILABLE
    def supports(self, request: ProviderRequest) -> bool: ...  # default: capability match
    def execute(self, request: ProviderRequest) -> ProviderResult: ...  # abstract
```

- **`provider_name`** — a stable, unique string (e.g. `"mock_flight_provider"`).
  Used in logs, diagnostics, and `ProviderResult.provider_name` — never a
  secret or credential value.
- **`capability`** — which `Capability` this provider serves. A provider
  serves exactly one capability; a Discovery module with multiple data
  needs (e.g. Weather's month + year + known-destinations) expresses that
  as multiple `operation` values on `ProviderRequest`, not multiple
  capabilities.
- **`health_check()`** — cheap, synchronous self-check, called by the
  selector before every request. Mock providers are always `AVAILABLE`; a
  future live provider would check its own circuit-breaker state here,
  not make a network call.
- **`supports(request)`** — whether this provider can serve this specific
  request (a request for an operation it doesn't implement, or coverage
  it doesn't have). Default: any request for its own capability.
- **`execute(request)`** — perform the request and return a `ProviderResult`,
  or raise one of `travelos/intelligence_gateway/exceptions.py`'s errors
  on failure. A provider should never catch and silently swallow its own
  errors — the gateway's retry/failover policies decide what happens
  next.

## `ProviderRequest`

```python
@dataclass
class ProviderRequest:
    capability: Capability
    operation: str
    params: dict[str, Any] = field(default_factory=dict)
    bypass_cache: bool = False
```

`operation` distinguishes between a provider's several methods — most
providers only ever see one operation name (`"search"` for flight/
accommodation), but Weather's provider sees `"month"`, `"year"`, and
`"known_destinations"`.

## `ProviderResult`

The one output shape every `IntelligenceGateway.execute()` call returns,
success or failure:

| Field | Meaning |
|---|---|
| `provider_name` | Which provider answered (`"none"` if every provider failed) |
| `capability` | Echoed from the request |
| `status` | `ProviderStatus` |
| `data` | The provider's payload — shape is capability-specific, opaque to the gateway |
| `confidence` | 0.0–1.0, provider-reported |
| `assumptions` / `warnings` / `errors` | Never silently dropped — failover preserves every prior provider's failure as a warning |
| `cached` | Whether this result came from cache |
| `stale` | Whether a cached result is being served past its TTL (total-failure graceful degradation only) |
| `latency_ms` | Time the winning provider call took |
| `request_id` | One UUID per `execute()` call, for tracing |
| `retrieved_at` / `expires_at` | ISO timestamps |
| `source_metadata` | Provider-supplied extra context |

**Never a secret.** No field on `ProviderResult` is ever populated from a
`SecretReference.resolve()` call — see `docs/SECRET_MANAGEMENT.md`.

## Provider Environments

| Environment | Meaning |
|---|---|
| `MOCK` | Deterministic, no external call — every provider registered by this task |
| `SANDBOX` | A real vendor's test/sandbox endpoint — not used yet |
| `PRODUCTION` | A real vendor's live endpoint — not used yet |

The gateway only selects providers whose `environment` matches
`ConfigurationManager.provider_environment` (default `MOCK`, forced to
`PRODUCTION` only when `TRAVELOS_ENV=production` and not overridden).

## Provider Statuses

| Status | Meaning | Eligible for selection? |
|---|---|---|
| `AVAILABLE` | Healthy, ready | Yes |
| `DEGRADED` | Working but impaired | Yes |
| `UNAVAILABLE` | Not reachable / down | No |
| `RATE_LIMITED` | Currently over its quota | No (failover attempts the next provider) |
| `MISCONFIGURED` | Missing required setup (e.g. a secret) | No |

## Capabilities

`FLIGHTS`, `ACCOMMODATION`, `DESTINATIONS`, `BUDGET`, `VISA`, `WEATHER`,
`MAPS`, `CURRENCY`, `EVENTS` — one per current or future Discovery
domain. See `docs/INTELLIGENCE_GATEWAY.md`'s Deferred Integrations
section for which capabilities have a registered provider today.
