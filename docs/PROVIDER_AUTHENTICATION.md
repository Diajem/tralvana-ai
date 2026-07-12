# Provider Authentication

Authentication strategies for live provider adapters
(`travelos/live_providers/auth/`). **Interfaces only — no real token is
fetched or live authentication call made anywhere in this framework.**

## `AuthStrategy`

```python
class AuthStrategy(ABC):
    def is_configured(self) -> bool: ...  # never reads a secret's value
    def headers(self) -> dict[str, str]:  # raises if not configured
        ...
```

Every concrete strategy loads its credential through
`travelos.intelligence_gateway.secret_reference.SecretReference`
(T-025) — never a hardcoded value, never logged, never returned raw. See
`docs/SECRET_MANAGEMENT.md` for the full rules `SecretReference` itself
follows.

## API Key (`ApiKeyAuthStrategy`)

A single secret sent as a request header (default `X-API-Key`,
configurable):

```python
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.auth.api_key_auth import ApiKeyAuthStrategy

auth = ApiKeyAuthStrategy(secret=SecretReference(env_var="WEATHER_API_KEY"))
auth.is_configured()  # True/False — never raises
auth.headers()         # {"X-API-Key": "<value>"} or raises ProviderConfigurationError
```

## Bearer Token (`BearerTokenAuthStrategy`)

A single secret sent as `Authorization: Bearer <token>`:

```python
from travelos.live_providers.auth.bearer_token_auth import BearerTokenAuthStrategy

auth = BearerTokenAuthStrategy(secret=SecretReference(env_var="DUFFEL_API_TOKEN"))
auth.headers()  # {"Authorization": "Bearer <value>"}
```

## OAuth2 Client Credentials (`OAuth2ClientCredentialsAuthStrategy`)

**Interface only.** A real implementation would `POST` `client_id`/
`client_secret` to `token_url`, cache the returned bearer token, and
refresh it once it expires — that HTTP exchange is deliberately not
implemented here (T-026's explicit constraint: "no real tokens or live
authentication calls").

```python
from travelos.live_providers.auth.oauth2_client_credentials_auth import (
    OAuth2ClientCredentialsAuthStrategy,
)

auth = OAuth2ClientCredentialsAuthStrategy(
    client_id=SecretReference(env_var="AMADEUS_API_KEY"),
    client_secret=SecretReference(env_var="AMADEUS_API_SECRET"),
    token_url="https://api.amadeus.com/v1/security/oauth2/token",
)
auth.is_configured()  # True once both secrets are present — independent
                      # of whether a token has actually been fetched
auth.headers()        # raises ProviderConfigurationError — no token exchange implemented
```

`set_cached_token(token)` exists **only** so tests can simulate an
already-authenticated state and exercise `headers()`'s success path
without a live call — never populated by anything in this framework
outside a test. A real implementation would call the equivalent of this
method after a genuine token-endpoint exchange, inside its own
`fetch_token()` method it adds when building the real adapter.

## Rules (all three strategies)

1. **Secrets come from environment variables only**, via
   `SecretReference` — never hardcoded.
2. **`is_configured()` never raises and never reads the secret's
   value** — it only checks presence.
3. **`headers()` raises `ProviderConfigurationError`** (a
   `ProviderMisconfiguredError` alias — `docs/PROVIDER_ERROR_MODEL.md`)
   if not configured — never returns a partial or placeholder
   credential.
4. **No strategy's `__repr__`/`str()` ever includes a secret value** —
   verified directly by `travelos/tests/test_auth_strategies.py`'s
   `TestSecretRedactionAcrossStrategies`.
5. **`BaseLiveProvider.authenticate()`** is the only place a strategy's
   `headers()` is called during normal execution — the returned headers
   are merged into the outgoing `TransportRequest` by `execute()` and
   never separately logged or stored (`docs/PROVIDER_OBSERVABILITY.md`).

## Choosing a Strategy for a New Provider

| Vendor style | Strategy |
|---|---|
| Single static key, header-based | `ApiKeyAuthStrategy` |
| Single static token, `Authorization: Bearer` | `BearerTokenAuthStrategy` |
| Client-credentials OAuth2 (Amadeus-style) | `OAuth2ClientCredentialsAuthStrategy` — but its token exchange must be implemented by the concrete adapter first (see above) before it can actually authenticate a live call |
| Something else entirely (HMAC signing, mTLS, ...) | Implement `AuthStrategy` directly — the interface is intentionally minimal |
