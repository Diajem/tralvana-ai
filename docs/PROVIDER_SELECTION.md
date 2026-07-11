# Provider Selection

`travelos/intelligence_gateway/provider_selector.py`. Deterministic,
rule-based — no machine learning, no scoring model, consistent with
every other decision point in this codebase (`IntentClassifier`,
`DecisionEngine`, Trip Brain's `ModuleSelector`).

## Algorithm

`ProviderSelector.select(providers, request, environment)` filters the
capability's registered providers (already priority-sorted by
`ProviderRegistry.register()`) down to the eligible, ordered set:

```python
eligible = [
    p for p in providers
    if p.environment == environment
    and p.supports(request)
    and p.health_check() in (AVAILABLE, DEGRADED)
]
```

The filter **preserves** the registry's priority order rather than
re-sorting — so fallback order is stable and reproducible for identical
input, satisfying "deterministic" without needing a second sort pass.

## Selection Signals, In Order

1. **Environment** — a provider only participates if its `environment`
   matches the gateway's active environment
   (`ConfigurationManager.provider_environment`, default `MOCK`). A
   `SANDBOX` or `PRODUCTION` provider is silently skipped when running in
   `MOCK` mode, and vice versa.
2. **Health** — `provider.health_check()` must return `AVAILABLE` or
   `DEGRADED`. `UNAVAILABLE`, `RATE_LIMITED`, and `MISCONFIGURED`
   providers are excluded from selection entirely (rate-limit exhaustion
   specifically is checked again, per-call, by the gateway — see
   `docs/CACHING_AND_FAILOVER.md` — `health_check()` covers a provider's
   own self-reported state, not live quota).
3. **Request support** — `provider.supports(request)` — a provider that
   doesn't implement the requested `operation`, or doesn't cover the
   requested destination/route, is excluded.
4. **Priority** — lower number runs first. Registered once, by
   `ProviderRegistry.register()`, not re-evaluated per request.
5. **Fallback order** — the filtered list itself *is* the fallback
   order: the gateway's failover loop
   (`travelos/intelligence_gateway/failover_policy.py`) tries providers
   in exactly this sequence, moving to the next only if the current one
   raises.

## Configuring Priority and Overrides

- `Provider.priority` (default `100`, or
  `ConfigurationManager.default_provider_priority` for providers that
  don't override it) — set lower for a preferred provider, higher for a
  fallback.
- `ConfigurationManager.provider_override_for(capability_name)` reads
  `PROVIDER_<CAPABILITY>` (e.g. `PROVIDER_FLIGHTS=some_provider_name`) —
  reserved for forcing a specific provider for one capability. Not yet
  consumed by the selector itself (this task registers exactly one
  provider per integrated capability, so there is nothing to choose
  between today); the property exists so a future multi-provider
  capability doesn't need a new configuration surface.

## No Eligible Provider

If the filtered list is empty — no provider registered, none matches the
environment, or none supports the request — `IntelligenceGateway.execute()`
returns immediately with `status=UNAVAILABLE` and a clear error message
naming the capability. This is a normal, expected outcome for a
capability with no registered provider yet (e.g. `MAPS`), not an
exception.
