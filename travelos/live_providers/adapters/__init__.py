"""
Request/response adapter pattern (docs/LIVE_PROVIDER_ADAPTER_GUIDE.md):

    Internal request (ai.shared.agent_result-shaped ProviderRequest)
      -> provider request (TransportRequest, vendor-shaped)

    Provider response (TransportResponse, vendor-shaped)
      -> internal ProviderResult

This lives directly on `BaseLiveProvider.build_request()` and
`.parse_response()` (base_live_provider.py) rather than as a separate
class hierarchy here — each concrete provider already owns its mapping
by implementing those two methods, which *is* the adapter pattern. A
second, parallel `RequestAdapter`/`ResponseAdapter` class hierarchy
wrapping the same two methods would be an unnecessary abstraction this
task's own constraint ("keep the framework small and reusable") argues
against — see docs/ADR/ADR-021-live-provider-framework.md.

Every concrete adapter must own its vendor-specific field mapping here
(or in its own module under this package, e.g. a future
`adapters/duffel_flight_adapter.py`) — never in
`ai/shared/agent_result.py` or any other shared domain model, per this
task's explicit constraint.
"""
