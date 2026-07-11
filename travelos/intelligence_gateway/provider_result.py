"""ProviderResult — the Intelligence Gateway's single output shape, returned
by every gateway.execute() call regardless of which provider answered it
or whether it came from cache. Never carries a raw secret — see
docs/SECRET_MANAGEMENT.md."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelos.intelligence_gateway.provider_status import Capability, ProviderStatus


@dataclass
class ProviderResult:
    provider_name: str
    capability: Capability
    status: ProviderStatus
    data: Any = None
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    cached: bool = False
    stale: bool = False
    latency_ms: float = 0.0
    request_id: str = ""
    retrieved_at: str = ""
    expires_at: str | None = None
    source_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status in (ProviderStatus.AVAILABLE, ProviderStatus.DEGRADED) and not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "capability": self.capability.value,
            "status": self.status.value,
            "data": self.data,
            "confidence": self.confidence,
            "assumptions": self.assumptions,
            "warnings": self.warnings,
            "errors": self.errors,
            "cached": self.cached,
            "stale": self.stale,
            "latency_ms": self.latency_ms,
            "request_id": self.request_id,
            "retrieved_at": self.retrieved_at,
            "expires_at": self.expires_at,
            "source_metadata": self.source_metadata,
        }
