"""
GET /internal/providers/status — read-only Intelligence Gateway
diagnostics (docs/INTELLIGENCE_GATEWAY.md, docs/PROVIDER_OBSERVABILITY.md).
Safe metadata only: no secret value, no raw request/response payload,
ever appears here — verified by
services/api/tests/test_internal_diagnostics.py.
"""

from __future__ import annotations

from datetime import datetime, timezone

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
    provider_type: str  # "MOCK" | "LIVE"
    environment: str
    status: str
    health: str
    priority: int
    cache_ttl_seconds: int
    rate_limit: RateLimitStatus
    authentication_configured: bool
    last_check_time: str
    request_count: int
    failure_count: int


class ProvidersStatusResponse(BaseModel):
    environment: str
    cache_enabled: bool
    retry_enabled: bool
    healthcheck_enabled: bool
    providers: list[ProviderStatusEntry]


@router.get("/providers/status", response_model=ProvidersStatusResponse)
async def providers_status() -> dict:
    from travelos.config.configuration_manager import config
    from travelos.intelligence_gateway.gateway import intelligence_gateway
    from travelos.intelligence_gateway.provider_status import ProviderEnvironment, ProviderStatus
    from travelos.live_providers.metrics.provider_metrics import provider_metrics

    # discovery_adapters registers the mock providers as an import-time
    # side effect (travelos/intelligence_gateway/discovery_adapters.py) —
    # normally triggered the first time a Discovery module runs. Import
    # it here too so this endpoint reports the true provider set even if
    # called before any Discovery request has been made yet.
    import travelos.intelligence_gateway.discovery_adapters  # noqa: F401

    healthcheck_enabled = config.provider_healthcheck_enabled
    checked_at = _now_iso()

    entries: list[dict] = []
    for provider in intelligence_gateway.registry.all_providers():
        if healthcheck_enabled:
            health = provider.health_check()
        else:
            health = None
        rl_state = intelligence_gateway.rate_limit_status(provider.provider_name)
        metrics = provider_metrics.snapshot_for(provider.provider_name)

        # MOCK providers (T-025) have nothing to authenticate — trivially
        # "configured". LIVE providers (BaseLiveProvider, T-026) expose
        # `.auth_configured` — duck-typed so this endpoint works for any
        # future Provider subclass without importing travelos.live_providers
        # at the intelligence_gateway layer (see that package's __init__.py).
        is_mock = provider.environment == ProviderEnvironment.MOCK
        auth_configured = True if is_mock else bool(getattr(provider, "auth_configured", False))

        entries.append({
            "capability": provider.capability.value,
            "provider_name": provider.provider_name,
            "provider_type": "MOCK" if is_mock else "LIVE",
            "environment": provider.environment.value,
            "status": health.value if health is not None else "DISABLED",
            "health": (
                "healthy" if health in (ProviderStatus.AVAILABLE, ProviderStatus.DEGRADED)
                else "unhealthy" if health is not None else "unknown"
            ),
            "priority": provider.priority,
            "cache_ttl_seconds": intelligence_gateway.cache_ttl_seconds(provider.capability),
            "rate_limit": {
                "limit": rl_state.limit if rl_state else None,
                "remaining": rl_state.remaining if rl_state else None,
                "reset_at": rl_state.reset_at.isoformat() if rl_state else None,
            },
            "authentication_configured": auth_configured,
            "last_check_time": checked_at,
            "request_count": metrics.request_count if metrics else 0,
            "failure_count": metrics.failure_count if metrics else 0,
        })

    return {
        "environment": intelligence_gateway.environment.value,
        "cache_enabled": intelligence_gateway.cache_enabled_effective,
        "retry_enabled": config.retry_enabled,
        "healthcheck_enabled": healthcheck_enabled,
        "providers": sorted(entries, key=lambda e: (e["capability"], e["priority"])),
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
