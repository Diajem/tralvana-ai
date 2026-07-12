# Live Provider Adapter Guide

How to build a real live provider on `BaseLiveProvider`
(`travelos/live_providers/base_live_provider.py`). Walks through
`travelos/live_providers/templates/example_flight_provider.py` — copy
its shape; do not import or register that class itself outside
tests/examples, it is explicitly a **non-production template**.

## 1. Choose an authentication strategy

Pick from `travelos/live_providers/auth/` (`docs/PROVIDER_AUTHENTICATION.md`)
or, for a vendor with a genuinely different scheme, implement
`AuthStrategy` directly. Every strategy is constructed with a
`SecretReference` (`travelos/intelligence_gateway/secret_reference.py`) —
never a hardcoded credential:

```python
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.auth.api_key_auth import ApiKeyAuthStrategy

auth = ApiKeyAuthStrategy(secret=SecretReference(env_var="DUFFEL_API_TOKEN"))
```

## 2. Subclass `BaseLiveProvider`

```python
from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment
from travelos.live_providers.base_live_provider import BaseLiveProvider
from travelos.live_providers.transport import Transport

class DuffelFlightProvider(BaseLiveProvider):
    def __init__(self, transport: Transport) -> None:
        super().__init__(
            provider_name="duffel_flight_provider",
            capability=Capability.FLIGHTS,
            environment=ProviderEnvironment.PRODUCTION,  # or SANDBOX
            transport=transport,
            auth=ApiKeyAuthStrategy(secret=SecretReference(env_var="DUFFEL_API_TOKEN")),
            priority=10,  # lower than the mock provider's priority so it's preferred once eligible
        )
```

`environment` must be `SANDBOX` or `PRODUCTION` — `MOCK` raises
`ValueError` (that stays reserved for T-025's mock providers).

## 3. Implement `build_request()`

Internal `ProviderRequest.params` (whatever shape the calling Discovery
adapter passes) → a vendor-shaped `TransportRequest`. This is where
every vendor-specific field name lives — **never** in a shared domain
model (`ai/shared/agent_result.py` or similar):

```python
def build_request(self, request: ProviderRequest) -> TransportRequest:
    return TransportRequest(
        method="POST",
        url="https://api.duffel.com/air/offer_requests",
        json_body={
            "data": {
                "slices": [{
                    "origin": request.params["origin"],
                    "destination": request.params["destination"],
                    "departure_date": request.params["departure_date"],
                }],
                "passengers": [{"type": "adult"}],
            }
        },
        timeout_seconds=config.provider_http_timeout_seconds,
    )
```

Never set an auth header here — `authenticate()` supplies it, merged in
by `execute()` automatically.

## 4. Implement `parse_response()`

Vendor-shaped `TransportResponse` → `ProviderResult`. Called only after
a successful HTTP status check (`_check_response_status`, inherited —
see `docs/PROVIDER_ERROR_MODEL.md`). Raise `ProviderResponseError` if the
body doesn't have the shape you expect, even on a 200:

```python
def parse_response(self, response: TransportResponse) -> ProviderResult:
    body = response.body
    if not isinstance(body, dict) or "data" not in body:
        raise ProviderResponseError("duffel_flight_provider: unexpected response shape")
    offers = body["data"].get("offers", [])
    return ProviderResult(
        provider_name=self.provider_name,
        capability=self.capability,
        status=ProviderStatus.AVAILABLE,
        data=[_map_offer(o) for o in offers],  # your own vendor -> internal mapping
        confidence=1.0,
        source_metadata={"provider_request_id": body["data"].get("id", "")},
    )
```

## 5. (Optional) Override `map_error()`

The default wraps any non-`ProviderError` as `ProviderUnavailableError`.
If your vendor returns a structured error body even on failure status
codes, inspect it here and raise the more specific standard type:

```python
def map_error(self, error: Exception) -> Exception:
    if isinstance(error, ProviderResponseError) and "invalid_slice" in str(error):
        return ProviderValidationError(str(error))
    return super().map_error(error)
```

## 6. Test against `FakeTransport`

Never test against the real vendor. Build a `FakeTransport` with a
canned or programmable responder:

```python
transport = FakeTransport.always_returning(
    status_code=200, body={"data": {"id": "orq_123", "offers": [...]}},
)
provider = DuffelFlightProvider(transport=transport)
result = provider.execute(request)
assert transport.sent_requests[0].json_body["data"]["slices"][0]["origin"] == "LON"
```

## 7. Register it

Once ready for a real environment, register alongside the existing mock
provider for the same capability — the Intelligence Gateway selects
between them by environment/priority/health automatically
(`docs/PROVIDER_SELECTION.md`), no gateway code changes needed:

```python
from travelos.intelligence_gateway.provider_registry import provider_registry
provider_registry.register(DuffelFlightProvider(transport=real_transport))
```

## Checklist

- [ ] `provider_name` is unique and descriptive
- [ ] `environment` is `SANDBOX` or `PRODUCTION`, never `MOCK`
- [ ] Auth strategy loads its secret via `SecretReference`, never hardcoded
- [ ] `build_request()` never includes an auth header
- [ ] `build_request()` maps every vendor-specific field itself — nothing vendor-shaped leaks into `ai/shared/agent_result.py` or any Discovery domain model
- [ ] `parse_response()` raises `ProviderResponseError` on an unexpected body shape, even on HTTP 200
- [ ] Tested exclusively against `FakeTransport` — no real network call anywhere in the test suite
- [ ] `docs/PRODUCTION_READINESS.md`'s checklist reviewed before ever pointing at a real `PRODUCTION` credential
