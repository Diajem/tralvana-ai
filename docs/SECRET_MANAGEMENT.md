# Secret Management

`travelos/intelligence_gateway/secret_reference.py`. Rules for how a
future live provider would hold a credential — no real key is added by
this task.

## `SecretReference`

```python
@dataclass(frozen=True)
class SecretReference:
    env_var: str
    required: bool = True
    description: str = ""
```

A `SecretReference` is a *pointer* to an environment variable, never the
credential value itself, until the one moment it's actually needed.

| Method | Behaviour |
|---|---|
| `is_present()` | `True`/`False` — whether the env var is set to a non-empty value. Never raises. |
| `resolve()` | Returns the actual value. Raises `MissingSecretError` if unset and `required=True`; returns `""` if unset and `required=False`. |
| `describe()` | Safe, loggable dict — `env_var`, `required`, `configured` (bool), `description`. **Never includes the value.** |
| `__repr__` | `SecretReference(env_var='...', configured=True/False)` — same guarantee. |

## Rules

1. **Secrets come from environment variables only.** No secret value is
   ever hardcoded in `travelos/intelligence_gateway/` or any Discovery
   module.
2. **Never log a raw secret.** `TravelLogger` calls throughout the
   gateway only ever pass provider names, capabilities, statuses, and
   timings — never a `SecretReference.resolve()` result.
3. **Never return a raw secret.** `ProviderResult` (`docs/PROVIDER_CONTRACT.md`)
   has no field that could carry a credential value; the diagnostics
   endpoint (`GET /internal/providers/status`) only ever reports whether
   a provider is healthy, never what backs it.
4. **`resolve()` is called at the point of use only** — immediately
   before an outbound call (e.g. building an `Authorization` header for a
   future live provider), never stored on an object, never assigned to a
   variable held for longer than that one call.
5. **Validation without exposure** — `is_present()` and `describe()` let
   a health check or diagnostic confirm a secret is configured (or flag
   that it's missing, surfacing as `ProviderStatus.MISCONFIGURED`)
   without ever reading the value itself.
6. **Never commit credentials.** `.env.example` (updated by this task)
   lists every provider-related environment variable name with an empty
   placeholder value — never a real key, sandbox or otherwise.

## Example (future live provider, illustrative — not built by this task)

```python
class LiveFlightProvider(Provider):
    def __init__(self) -> None:
        self._api_key = SecretReference(env_var="AMADEUS_API_KEY", required=True)

    def health_check(self) -> ProviderStatus:
        if not self._api_key.is_present():
            return ProviderStatus.MISCONFIGURED
        return ProviderStatus.AVAILABLE

    def execute(self, request: ProviderRequest) -> ProviderResult:
        headers = {"Authorization": f"Bearer {self._api_key.resolve()}"}
        # ... outbound call using `headers`, never stored beyond this scope ...
```

`health_check()` returning `MISCONFIGURED` is exactly what removes this
provider from `ProviderSelector`'s eligible set (`docs/PROVIDER_SELECTION.md`)
without ever needing to expose *why* beyond that one status value.
