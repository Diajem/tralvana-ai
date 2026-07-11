# Intelligence Gateway

T-025 — provider-access infrastructure that lets Tralvana AI use mock,
cached, and future live knowledge sources without coupling the Trip
Brain or Discovery modules to specific vendors. **Infrastructure only —
no real external API is integrated by this task.**

See also `docs/PROVIDER_CONTRACT.md`, `docs/PROVIDER_SELECTION.md`,
`docs/CACHING_AND_FAILOVER.md`, `docs/SECRET_MANAGEMENT.md`, and
`docs/ADR/ADR-020-intelligence-gateway.md`.

## Why This Exists

Every Discovery module today constructs its own mock provider directly
(`FlightIntelligence(provider=MockFlightProvider())`, etc.). This works
for Sprint 1–2's deterministic mock data, but has no answer for the
questions Sprint 4+ will actually face: which vendor answers a given
request, what happens when that vendor is down or rate-limited, how a
result gets cached so the same request isn't paid for twice, and how a
credential gets from an environment variable to an outbound HTTP call
without ever being logged. The Intelligence Gateway is the one place
those concerns live, so no Discovery module or Trip Brain has to solve
them itself.

## Architecture

```
Trip Brain
  -> Discovery Module
    -> Intelligence Gateway
      -> Provider Interface
        -> Mock Provider / Future Live Provider
          -> Cache / Retry / Failover / Observability
```

The Trip Brain never calls the gateway directly — only Discovery modules
(or, in this task's integration, a thin provider adapter standing in for
a Discovery module's existing provider) do. This preserves the exact
layering ADR-017 established for Trip Brain: it orchestrates Discovery
modules, it does not reach past them into their internals.

## Package Layout (`travelos/intelligence_gateway/`)

**Deviation from the task brief's suggested `platform/intelligence_gateway/`
path — see "Architecture Deviations" below and ADR-020.**

| File | Responsibility |
|---|---|
| `provider_contract.py` | `Provider` ABC, `ProviderRequest` — see `docs/PROVIDER_CONTRACT.md` |
| `provider_result.py` | `ProviderResult` — the one output shape every `execute()` call returns |
| `provider_status.py` | `ProviderEnvironment`, `ProviderStatus`, `Capability` enums |
| `provider_registry.py` | `ProviderRegistry` — register/retrieve providers by capability |
| `provider_selector.py` | Deterministic provider selection — `docs/PROVIDER_SELECTION.md` |
| `retry_policy.py` | Transient-failure retry, non-retryable error classification |
| `cache_policy.py` | In-memory cache — key generation, TTL, staleness, bypass |
| `rate_limit_policy.py` | In-memory per-provider rate-limit tracking |
| `failover_policy.py` | Try-next-provider-on-failure loop, independently testable |
| `secret_reference.py` | `SecretReference` — `docs/SECRET_MANAGEMENT.md` |
| `exceptions.py` | Provider error hierarchy (retryable vs. never-retryable) |
| `gateway.py` | `IntelligenceGateway` — ties everything above together |
| `discovery_adapters.py` | The three real mock providers wrapped and wired in — see below |

## Execution Flow

`IntelligenceGateway.execute(capability, request)`:

1. **Cache check** — a fresh cached `ProviderResult` for this exact
   `(capability, operation, params)` short-circuits everything below.
2. **Selection** — `ProviderSelector` filters registered providers for
   this capability down to the eligible, ordered set (environment match,
   healthy, supports this request), preserving registry priority order.
3. **No eligible provider** → an `UNAVAILABLE` `ProviderResult` with a
   clear error, immediately.
4. **Failover loop** (`failover_policy.run_with_failover`) — for each
   eligible provider in order:
   - Rate-limit check; if exhausted, this provider is skipped (raises,
     caught, next provider tried).
   - Retry-wrapped `execute()` — transient failures retry up to
     `RetryPolicy.max_attempts`; non-retryable failures propagate
     immediately.
   - First success wins. Every prior failure's message is preserved in
     the winning result's `warnings`.
5. **All providers failed** — a fresh entry is not available; a *stale*
   cached entry (past its TTL but not yet overwritten) is served instead
   if one exists, marked `.stale = True`. Otherwise: `UNAVAILABLE`, with
   every provider's failure listed.
6. **Cache write** — a successful, non-bypassed result is cached with its
   capability's TTL before being returned.

Every step logs through the existing `TravelLogger`
(`travelos/logging/travel_logger.py`) — provider selected, cache hit/
miss, retry attempt, failover, latency, final status. No personal data or
secret is ever logged.

## Discovery Integration

Two layers, kept deliberately separate (`discovery_adapters.py`):

1. **Gateway-contract wrapper** (`_Mock*GatewayProvider`, private) —
   implements `Provider`, registered in `provider_registry`. It
   delegates every call straight to the *existing*
   `Mock{Flight,Accommodation,Weather}Provider` class already used by
   each Discovery module — zero internal logic rewritten or duplicated.
2. **Drop-in adapter** (`Gateway{Flight,Accommodation,Weather}Provider`,
   public) — implements the *exact same method signature* each Discovery
   module's `*Intelligence` class already expects from its `provider`
   constructor argument (`.search(...)` for flight/accommodation;
   `.month()`/`.year()`/`.known_destinations()` for weather). Internally
   it calls `IntelligenceGateway.execute()` instead of the mock class
   directly.

The only change to `ai/discovery/flights/flight_intelligence.py`,
`ai/discovery/accommodation/accommodation_intelligence.py`, and
`ai/discovery/weather/weather_intelligence.py` is which provider object
their bottom-of-file singleton passes to the constructor — `MockFlightProvider()`
→ `GatewayFlightProvider()`, and so on. No method signature, scoring
logic, or public API response shape changes anywhere.

**Proven behaviour-preserving**: `travelos/tests/test_discovery_adapters.py`
asserts every `Gateway*Provider` call produces output byte-identical to
calling the underlying `Mock*Provider` directly, for flight, accommodation,
and all three weather operations. The full 833-test suite (unchanged
649 pre-existing Discovery/Trip Brain tests plus everything since) passes
with the gateway wired in.

### Deferred Integrations

Only Flights, Accommodation, and Weather are wired to the gateway in this
task — the minimum this task's own instructions ask for ("at minimum,
integrate... start with the smallest safe integration that proves the
pattern"). Destinations, Budget, Visa, Maps, Currency, and Events are
**not** integrated:

- **Destinations, Budget, Visa** each have their own `Mock*Provider`
  (`ai/discovery/{destinations,budget,visa}/mock_*_provider.py`) with a
  distinct method shape. Wiring them is the same pattern already proven
  for the three integrated modules — no new gateway capability is
  needed, only three more `Gateway*Provider` adapter classes. Deferred
  to keep this task's diff reviewable, not because of a technical
  blocker.
- **Maps, Currency, Events** have no Discovery module or mock provider
  at all yet in this codebase — there is nothing to wrap. The `Capability`
  enum includes them (per this task's explicit requirement) so the
  registry and selector are ready the moment a real module exists, but no
  provider is registered for them.

## Configuration

`travelos/config/configuration_manager.py` gained (all environment-variable-driven,
development-safe defaults — see `.env.example`):

| Property / method | Env var | Default |
|---|---|---|
| `provider_environment` | `PROVIDER_ENVIRONMENT` | `MOCK` (`PRODUCTION` only if `TRAVELOS_ENV=production`) |
| `cache_enabled` | `PROVIDER_CACHE_ENABLED` | `true` |
| `retry_enabled` | `PROVIDER_RETRY_ENABLED` | `true` |
| `default_provider_priority` | `PROVIDER_DEFAULT_PRIORITY` | `100` |
| `provider_override_for(capability)` | `PROVIDER_<CAPABILITY>` | unset |

## Diagnostics

`GET /internal/providers/status` (`services/api/app/routers/internal.py`)
returns capability, provider name, environment, health status, priority,
cache TTL, and rate-limit state for every registered provider — safe
metadata only, no secret or credential value ever appears in the
response. See `docs/API_EXPLAINABILITY.md`'s sibling pattern for how
this repo documents a diagnostic/read endpoint; full contract example in
this file's companion docs.

## Non-Goals

- No live provider is integrated — every registered provider today is a
  wrapped mock.
- No Redis, no external queue, no distributed rate limiter — every cache
  and rate-limit store is a plain in-memory dict, matching every other
  in-memory store already in this codebase (`ConversationSession`'s
  session store, the in-memory Goal/Trip repositories).
- No new agent framework — the gateway is a plain Python package using
  only the stdlib and existing platform-layer conventions
  (`TravelLogger`, `ConfigurationManager`).
- The Trip Brain is never wired to a provider directly — it continues to
  call only Discovery modules' public service methods, unchanged.
