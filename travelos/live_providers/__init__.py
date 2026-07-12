"""
Live Provider Framework — the reusable base every future live external
provider (flights, weather, maps, ...) must follow, built on top of the
Intelligence Gateway (T-025).

Foundation only (T-026) — no real external API is connected here. Every
provider this package can actually instantiate uses `FakeTransport`
(transport.py), never a real network call.

    Trip Brain
      -> Discovery Module
        -> Intelligence Gateway (travelos/intelligence_gateway/, unchanged)
          -> Live Provider Adapter (BaseLiveProvider subclass, this package)
            -> Authentication (auth/)
            -> Request Mapping (build_request)
            -> External API (Transport — FakeTransport only, today)
            -> Response Mapping (parse_response)
            -> ProviderResult (travelos.intelligence_gateway.provider_result)

Dependency direction: this package imports from
`travelos.intelligence_gateway` (Provider, ProviderResult, exceptions,
SecretReference) — never the reverse. The gateway has no idea this
package exists; a BaseLiveProvider subclass is registered into the same
ProviderRegistry a mock provider uses, and is selected/retried/failed-
over by the exact same, unmodified gateway code
(docs/LIVE_PROVIDER_FRAMEWORK.md, docs/ADR/ADR-021-live-provider-framework.md).
"""

from travelos.live_providers.base_live_provider import BaseLiveProvider

__all__ = ["BaseLiveProvider"]
