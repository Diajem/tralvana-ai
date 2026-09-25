"""
Intelligence Gateway — the single entry point Discovery modules call
instead of talking to a provider directly (docs/INTELLIGENCE_GATEWAY.md).

    cache check -> select eligible providers -> for each, in order:
        rate-limit check -> retry-wrapped execute -> success: cache + return
                                                    -> failure: warn, try next
    all failed -> stale cache (if any) -> UNAVAILABLE ProviderResult

Infrastructure only (T-025) — the Trip Brain never calls this directly;
only Discovery modules (or their provider adapters) do
(docs/ADR/ADR-020-intelligence-gateway.md).
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from travelos.intelligence_gateway.cache_policy import InMemoryCachePolicy, build_cache_key
from travelos.intelligence_gateway.exceptions import ProviderRateLimitedError
from travelos.intelligence_gateway.failover_policy import run_with_failover
from travelos.intelligence_gateway.provider_contract import Provider, ProviderRequest
from travelos.intelligence_gateway.provider_registry import ProviderRegistry, provider_registry
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_selector import ProviderSelector
from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment, ProviderStatus
from travelos.intelligence_gateway.rate_limit_policy import RateLimitTracker
from travelos.intelligence_gateway.retry_policy import RetryPolicy
from travelos.logging.travel_logger import TravelLogger

_logger = TravelLogger.for_service("IntelligenceGateway")

# Capability -> the ConfigurationManager property name governing its own
# per-capability live/mock switch (T-038 introduced FLIGHTS, T-039 added
# ACCOMMODATION). A capability absent from this map falls back to the
# general `provider_environment` — unchanged since T-025.
_CAPABILITY_MODE_CONFIG_ATTR: dict[Capability, str] = {
    Capability.FLIGHTS: "flight_provider_mode",
    Capability.ACCOMMODATION: "accommodation_provider_mode",
    Capability.EVENTS: "event_provider_mode",
}


class IntelligenceGateway:
    def __init__(
        self,
        registry: ProviderRegistry | None = None,
        selector: ProviderSelector | None = None,
        cache: InMemoryCachePolicy | None = None,
        rate_limiter: RateLimitTracker | None = None,
        retry_policy: RetryPolicy | None = None,
        environment: ProviderEnvironment | None = None,
    ) -> None:
        self._registry = registry or provider_registry
        self._selector = selector or ProviderSelector()
        self._cache = cache or InMemoryCachePolicy()
        self._rate_limiter = rate_limiter or RateLimitTracker()
        self._retry_policy = retry_policy or RetryPolicy()
        self._environment_override = environment

    # ------------------------------------------------------------------
    # Diagnostics — read-only introspection for GET /internal/providers/status
    # (docs/INTELLIGENCE_GATEWAY.md). Never exposes a secret value.
    # ------------------------------------------------------------------

    def rate_limit_status(self, provider_name: str):
        return self._rate_limiter.status_for(provider_name)

    def cache_ttl_seconds(self, capability: Capability) -> int:
        return self._cache.ttl_for(capability)

    @property
    def cache_enabled_effective(self) -> bool:
        return self._cache_enabled()

    @property
    def registry(self) -> ProviderRegistry:
        return self._registry

    @property
    def environment(self) -> ProviderEnvironment:
        if self._environment_override is not None:
            return self._environment_override
        try:
            from travelos.config.configuration_manager import config
            return ProviderEnvironment(config.provider_environment)
        except Exception:
            return ProviderEnvironment.MOCK

    def _environment_for(self, capability: Capability) -> ProviderEnvironment:
        """Per-capability environment resolution (T-038, extended T-039).
        Each capability in `_CAPABILITY_MODE_CONFIG_ATTR` reads its own
        dedicated `ConfigurationManager` switch — independent of the
        general `provider_environment` above and of every other
        capability's own switch — so enabling live Duffel flight or
        accommodation data never changes any other capability's provider
        selection (e.g. Weather still reads `provider_environment`
        exactly as before T-038 ever existed). An explicit constructor
        `environment=` override (used throughout the test suite) always
        wins, for every capability, unchanged."""
        if self._environment_override is not None:
            return self._environment_override
        config_attr = _CAPABILITY_MODE_CONFIG_ATTR.get(capability)
        if config_attr is not None:
            try:
                from travelos.config.configuration_manager import config
                mode = getattr(config, config_attr)
                if mode == "LIVE_SANDBOX" or mode.endswith("_SANDBOX"):
                    return ProviderEnvironment.SANDBOX
                if mode == "LIVE":
                    return ProviderEnvironment.PRODUCTION
                return ProviderEnvironment.MOCK
            except Exception:
                return ProviderEnvironment.MOCK
        return self.environment

    def execute(self, capability: Capability, request: ProviderRequest) -> ProviderResult:
        request_id = str(uuid.uuid4())
        cache_enabled = self._cache_enabled()
        key = build_cache_key(capability, request.operation, request.params)

        if cache_enabled and not request.bypass_cache:
            cached = self._cache.get(key)
            if cached is not None:
                _logger.info(
                    "Cache hit", capability=capability.value, operation=request.operation,
                    request_id=request_id,
                )
                return self._with_request_id(cached, request_id, cached_copy=True)
            _logger.debug("Cache miss", capability=capability.value, operation=request.operation, request_id=request_id)

        providers = self._registry.get_providers(capability)
        eligible = self._selector.select(providers, request, self._environment_for(capability))

        if not eligible:
            _logger.warning(
                "No eligible provider", capability=capability.value,
                operation=request.operation, environment=self.environment.value,
            )
            return self._unavailable_result(
                capability, request_id,
                errors=[f"No eligible provider is registered for capability {capability.value}"],
            )

        def call(provider: Provider, req: ProviderRequest) -> ProviderResult:
            return self._call_provider(provider, req, capability, request_id)

        outcome = run_with_failover(eligible, request, call)

        if outcome.all_failed:
            _logger.error(
                "All providers failed", capability=capability.value,
                attempted=[p.provider_name for p in eligible], request_id=request_id,
            )
            stale = self._cache.get_stale(key) if cache_enabled else None
            if stale is not None:
                _logger.warning("Serving stale cache after total provider failure", capability=capability.value, request_id=request_id)
                stale.warnings = [*outcome.warnings, *stale.warnings]
                return self._with_request_id(stale, request_id, cached_copy=True)
            return self._unavailable_result(capability, request_id, warnings=outcome.warnings, errors=["All eligible providers failed"])

        result = outcome.result
        assert result is not None  # run_with_failover guarantees this when not all_failed
        if outcome.provider_used != eligible[0].provider_name:
            _logger.warning(
                "Failed over to a fallback provider", capability=capability.value,
                provider=outcome.provider_used, request_id=request_id,
            )

        if cache_enabled and not request.bypass_cache and result.status in (ProviderStatus.AVAILABLE, ProviderStatus.DEGRADED):
            self._cache.set(key, result, ttl_seconds=self._cache.ttl_for(capability))

        _logger.info(
            "Provider executed", provider=result.provider_name, capability=capability.value,
            status=result.status.value, latency_ms=round(result.latency_ms, 1), request_id=request_id,
        )
        return result

    def execute_market_search(self, capability: Capability, request: ProviderRequest) -> ProviderResult:
        """Query *every* eligible supplier and combine their inventory.

        ``execute`` intentionally remains the single-answer/failover path for
        operations such as weather lookups.  A travel inventory search is a
        different operation: the first supplier to answer is not necessarily
        the best supplier for the traveller.  This method therefore fans the
        same request out to all eligible providers, retains every successful
        list response, and reports individual provider failures without
        discarding inventory returned by healthy providers.

        An empty response from one provider is a valid contribution, not a
        terminal "destination unavailable" decision.  UNAVAILABLE is returned
        only when no eligible provider can be called or every eligible provider
        fails.
        """
        request_id = str(uuid.uuid4())
        cache_enabled = self._cache_enabled()
        key = build_cache_key(capability, f"{request.operation}:market", request.params)

        if cache_enabled and not request.bypass_cache:
            cached = self._cache.get(key)
            if cached is not None:
                return self._with_request_id(cached, request_id, cached_copy=True)

        providers = self._registry.get_providers(capability)
        eligible = self._selector.select(providers, request, self._environment_for(capability))
        if not eligible:
            return self._unavailable_result(
                capability,
                request_id,
                errors=[f"No eligible provider is registered for capability {capability.value}"],
            )

        combined: list[object] = []
        warnings: list[str] = []
        successful: list[dict[str, object]] = []
        successful_metadata: list[dict[str, object]] = []
        failed: list[str] = []
        assumptions: list[str] = []
        total_latency_ms = 0.0

        for provider in eligible:
            try:
                result = self._call_provider(provider, request, capability, request_id)
            except Exception as exc:
                failed.append(provider.provider_name)
                warnings.append(f"{provider.provider_name} failed: {exc}")
                continue

            if not result.ok:
                failed.append(provider.provider_name)
                warnings.extend(result.warnings)
                warnings.append(
                    f"{provider.provider_name} returned {result.status.value} and contributed no inventory"
                )
                continue

            data = result.data if result.data is not None else []
            if not isinstance(data, list):
                failed.append(provider.provider_name)
                warnings.append(
                    f"{provider.provider_name} returned an invalid non-list market-search response"
                )
                continue

            # Attach safe provenance to each candidate before normalisation so
            # ranking/explainability can identify the actual supplier selected.
            for item in data:
                if isinstance(item, dict) and len(eligible) > 1:
                    item = {**item, "_market_provider_name": provider.provider_name}
                combined.append(item)

            total_latency_ms += result.latency_ms
            warnings.extend(result.warnings)
            assumptions.extend(result.assumptions)
            successful.append(
                {
                    "provider_name": provider.provider_name,
                    "status": result.status.value,
                    "result_count": len(data),
                    "latency_ms": round(result.latency_ms, 1),
                }
            )
            successful_metadata.append(dict(result.source_metadata))

        if not successful:
            stale = self._cache.get_stale(key) if cache_enabled else None
            if stale is not None:
                stale.warnings = [*warnings, *stale.warnings]
                return self._with_request_id(stale, request_id, cached_copy=True)
            return self._unavailable_result(
                capability, request_id, warnings=warnings,
                errors=["All eligible providers failed"],
            )

        result = ProviderResult(
            provider_name="multi_provider" if len(successful) > 1 else str(successful[0]["provider_name"]),
            capability=capability,
            status=ProviderStatus.DEGRADED if failed else ProviderStatus.AVAILABLE,
            data=combined,
            confidence=min(1.0, max(0.0, len(successful) / len(eligible))),
            assumptions=list(dict.fromkeys(assumptions)),
            warnings=warnings,
            latency_ms=total_latency_ms,
            request_id=request_id,
            retrieved_at=_now_iso(),
            source_metadata={
                **(successful_metadata[0] if len(successful_metadata) == 1 else {}),
                "aggregation": "all_eligible_providers",
                "providers_queried": [p.provider_name for p in eligible],
                "providers_succeeded": successful,
                "providers_failed": failed,
                "mapped_result_count": len(combined),
                "raw_result_count": sum(int(p["result_count"]) for p in successful),
            },
        )
        if cache_enabled and not request.bypass_cache:
            self._cache.set(key, result, ttl_seconds=self._cache.ttl_for(capability))
        return result

    # ------------------------------------------------------------------

    def _call_provider(
        self, provider: Provider, request: ProviderRequest, capability: Capability, request_id: str
    ) -> ProviderResult:
        if not self._rate_limiter.check(provider.provider_name):
            _logger.warning("Provider rate-limited", provider=provider.provider_name, capability=capability.value, request_id=request_id)
            # Raise, don't return — a RATE_LIMITED provider must fail over
            # to the next eligible provider exactly like any other
            # failure (docs/CACHING_AND_FAILOVER.md). Returning a result
            # here would make run_with_failover treat it as success.
            raise ProviderRateLimitedError(f"{provider.provider_name} is rate-limited")

        attempt = 0
        last_exc: Exception | None = None
        start = time.monotonic()
        while attempt < self._retry_policy.max_attempts:
            attempt += 1
            try:
                result = provider.execute(request)
                self._rate_limiter.record_call(provider.provider_name)
                result.latency_ms = (time.monotonic() - start) * 1000
                result.request_id = request_id
                if not result.retrieved_at:
                    result.retrieved_at = _now_iso()
                return result
            except Exception as exc:
                last_exc = exc
                if not self._retry_policy.is_retryable(exc):
                    raise
                if attempt < self._retry_policy.max_attempts:
                    delay = self._retry_policy.delay_for_attempt(attempt + 1)
                    _logger.warning(
                        "Retrying provider call", provider=provider.provider_name,
                        capability=capability.value, attempt=attempt, delay_seconds=delay, request_id=request_id,
                    )
                    if delay > 0:
                        time.sleep(delay)

        assert last_exc is not None
        raise last_exc

    def _cache_enabled(self) -> bool:
        if not self._cache.enabled:
            return False
        try:
            from travelos.config.configuration_manager import config
            return config.cache_enabled
        except Exception:
            return True

    def _with_request_id(self, result: ProviderResult, request_id: str, cached_copy: bool) -> ProviderResult:
        from dataclasses import replace
        return replace(result, request_id=request_id, cached=cached_copy or result.cached)

    def _unavailable_result(
        self, capability: Capability, request_id: str, warnings: list[str] | None = None, errors: list[str] | None = None,
    ) -> ProviderResult:
        return ProviderResult(
            provider_name="none", capability=capability, status=ProviderStatus.UNAVAILABLE,
            warnings=warnings or [], errors=errors or [], request_id=request_id, retrieved_at=_now_iso(),
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


intelligence_gateway = IntelligenceGateway()
