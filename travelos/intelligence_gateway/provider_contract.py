"""
The Provider contract — every provider the Intelligence Gateway can call,
mock or future-live, implements this one interface. See
docs/PROVIDER_CONTRACT.md.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import (
    Capability,
    ProviderEnvironment,
    ProviderStatus,
)


@dataclass
class ProviderRequest:
    """What the gateway asks a provider to do. `operation` distinguishes
    between a provider's several methods (e.g. Weather's `month` vs.
    `year`) — most providers only ever see one operation name."""

    capability: Capability
    operation: str
    params: dict[str, Any] = field(default_factory=dict)
    bypass_cache: bool = False


class Provider(ABC):
    """
    Common interface for every provider the Intelligence Gateway can
    select and call. A provider never talks to the Trip Brain or a
    Discovery module directly — it is only ever called by
    `IntelligenceGateway.execute()`.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def capability(self) -> Capability: ...

    @property
    def environment(self) -> ProviderEnvironment:
        return ProviderEnvironment.MOCK

    @property
    def priority(self) -> int:
        """Lower runs first. Ties broken by registration order
        (docs/PROVIDER_SELECTION.md)."""
        return 100

    @property
    def metadata(self) -> dict[str, Any]:
        return {}

    def health_check(self) -> ProviderStatus:
        """Cheap, synchronous self-check. Mock providers are always
        AVAILABLE; a future live provider would check its own circuit
        breaker / recent error rate here."""
        return ProviderStatus.AVAILABLE

    def supports(self, request: ProviderRequest) -> bool:
        """Whether this provider can serve this specific request (e.g. an
        operation it doesn't implement, or a destination outside its
        coverage). Default: supports every request for its own capability."""
        return request.capability == self.capability

    @abstractmethod
    def execute(self, request: ProviderRequest) -> ProviderResult:
        """Perform the request. Raise a travelos.intelligence_gateway.exceptions
        error on failure — the gateway's retry/failover policies decide
        what happens next, this method should not catch and swallow its
        own errors."""
        ...
