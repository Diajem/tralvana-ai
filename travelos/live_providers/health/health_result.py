"""
A reusable, structured health-check result
(docs/PROVIDER_OBSERVABILITY.md). Deliberately not added to the shared
`Provider` contract in `travelos/intelligence_gateway/` — that would
create a dependency from the gateway package into this one, inverting
the direction this framework depends on the gateway, not the reverse
(see this package's __init__.py). Consumers that want the richer detail
(the diagnostics endpoint) duck-type: `getattr(provider, "health_check_detailed", None)`.

`metadata` is safe-only — never a secret value, only booleans/strings
like `{"auth_configured": True}`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment, ProviderStatus


@dataclass
class ProviderHealthResult:
    provider_name: str
    capability: Capability
    environment: ProviderEnvironment
    status: ProviderStatus
    checked_at: str
    latency_ms: float = 0.0
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
