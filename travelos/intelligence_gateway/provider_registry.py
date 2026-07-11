"""
Provider Registry — the one central place providers are registered and
retrieved by capability. See docs/INTELLIGENCE_GATEWAY.md.
"""

from __future__ import annotations

from collections import defaultdict

from travelos.intelligence_gateway.provider_contract import Provider
from travelos.intelligence_gateway.provider_status import Capability
from travelos.logging.travel_logger import TravelLogger

_logger = TravelLogger.for_service("ProviderRegistry")


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[Capability, list[Provider]] = defaultdict(list)

    def register(self, provider: Provider) -> None:
        bucket = self._providers[provider.capability]
        bucket.append(provider)
        # Stable sort — ties keep registration order, making fallback
        # order deterministic (docs/PROVIDER_SELECTION.md).
        bucket.sort(key=lambda p: p.priority)
        _logger.info(
            "Provider registered",
            provider=provider.provider_name,
            capability=provider.capability.value,
            priority=provider.priority,
            environment=provider.environment.value,
        )

    def get_providers(self, capability: Capability) -> list[Provider]:
        return list(self._providers.get(capability, []))

    def capabilities(self) -> list[Capability]:
        return sorted(self._providers.keys(), key=lambda c: c.value)

    def all_providers(self) -> list[Provider]:
        return [p for providers in self._providers.values() for p in providers]

    def clear(self) -> None:
        """Used by tests to reset global registry state between cases."""
        self._providers.clear()


provider_registry = ProviderRegistry()
