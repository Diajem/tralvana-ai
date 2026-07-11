"""
GET /internal/providers/status — read-only Intelligence Gateway
diagnostics (docs/INTELLIGENCE_GATEWAY.md). Safe metadata only: no
secret value, no raw request/response payload, ever appears here.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/internal", tags=["internal"])


class RateLimitStatus(BaseModel):
    limit: int | None = None
    remaining: int | None = None
    reset_at: str | None = None


class ProviderStatusEntry(BaseModel):
    capability: str
    provider_name: str
    environment: str
    status: str
    health: str
    priority: int
    cache_ttl_seconds: int
    rate_limit: RateLimitStatus


class ProvidersStatusResponse(BaseModel):
    environment: str
    cache_enabled: bool
    retry_enabled: bool
    providers: list[ProviderStatusEntry]


@router.get("/providers/status", response_model=ProvidersStatusResponse)
async def providers_status() -> dict:
    from travelos.config.configuration_manager import config
    from travelos.intelligence_gateway.gateway import intelligence_gateway
    from travelos.intelligence_gateway.provider_status import ProviderStatus

    # discovery_adapters registers the mock providers as an import-time
    # side effect (travelos/intelligence_gateway/discovery_adapters.py) —
    # normally triggered the first time a Discovery module runs. Import
    # it here too so this endpoint reports the true provider set even if
    # called before any Discovery request has been made yet.
    import travelos.intelligence_gateway.discovery_adapters  # noqa: F401

    entries: list[dict] = []
    for provider in intelligence_gateway.registry.all_providers():
        health = provider.health_check()
        rl_state = intelligence_gateway.rate_limit_status(provider.provider_name)
        entries.append({
            "capability": provider.capability.value,
            "provider_name": provider.provider_name,
            "environment": provider.environment.value,
            "status": health.value,
            "health": "healthy" if health in (ProviderStatus.AVAILABLE, ProviderStatus.DEGRADED) else "unhealthy",
            "priority": provider.priority,
            "cache_ttl_seconds": intelligence_gateway.cache_ttl_seconds(provider.capability),
            "rate_limit": {
                "limit": rl_state.limit if rl_state else None,
                "remaining": rl_state.remaining if rl_state else None,
                "reset_at": rl_state.reset_at.isoformat() if rl_state else None,
            },
        })

    return {
        "environment": intelligence_gateway.environment.value,
        "cache_enabled": intelligence_gateway.cache_enabled_effective,
        "retry_enabled": config.retry_enabled,
        "providers": sorted(entries, key=lambda e: (e["capability"], e["priority"])),
    }
