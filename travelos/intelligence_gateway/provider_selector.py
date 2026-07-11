"""
Provider Selection — deterministic, rule-based, no machine learning
(docs/PROVIDER_SELECTION.md). Given every provider registered for a
capability, returns the eligible ones in the order the gateway should
try them: environment match, health, request support, then priority.
"""

from __future__ import annotations

from travelos.intelligence_gateway.provider_contract import Provider, ProviderRequest
from travelos.intelligence_gateway.provider_status import ProviderEnvironment, ProviderStatus

_ELIGIBLE_STATUSES = (ProviderStatus.AVAILABLE, ProviderStatus.DEGRADED)


class ProviderSelector:
    def select(
        self,
        providers: list[Provider],
        request: ProviderRequest,
        environment: ProviderEnvironment,
    ) -> list[Provider]:
        """Return eligible providers in fallback order (first = preferred).
        Never raises — an empty list means no provider can serve this
        request, which the gateway turns into an UNAVAILABLE result."""
        eligible = [
            p for p in providers
            if p.environment == environment
            and p.supports(request)
            and p.health_check() in _ELIGIBLE_STATUSES
        ]
        # `providers` arrives already priority-sorted from the registry —
        # this filter preserves that order rather than re-sorting, so
        # fallback order is stable across calls for identical input.
        return eligible
