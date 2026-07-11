"""
Intelligence Gateway — provider-access infrastructure that lets Trip
Brain and the Discovery Layer use mock, cached, and future live
knowledge sources without coupling to a specific vendor.

Infrastructure only (T-025) — no real external API is integrated here.
See docs/INTELLIGENCE_GATEWAY.md and docs/ADR/ADR-020-intelligence-gateway.md.

    Trip Brain
      -> Discovery Module
        -> Intelligence Gateway
          -> Provider Interface
            -> Mock Provider / Future Live Provider
              -> Cache / Retry / Failover / Observability
"""

from travelos.intelligence_gateway.gateway import IntelligenceGateway, intelligence_gateway
from travelos.intelligence_gateway.provider_contract import Provider, ProviderRequest
from travelos.intelligence_gateway.provider_registry import ProviderRegistry, provider_registry
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import (
    Capability,
    ProviderEnvironment,
    ProviderStatus,
)

__all__ = [
    "IntelligenceGateway",
    "intelligence_gateway",
    "Provider",
    "ProviderRequest",
    "ProviderRegistry",
    "provider_registry",
    "ProviderResult",
    "Capability",
    "ProviderEnvironment",
    "ProviderStatus",
]
