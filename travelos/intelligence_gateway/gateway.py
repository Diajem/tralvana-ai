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
        """Per-capability environment resolution (T-038). FLIGHTS reads
        `config.flight_provider_mode` — a dedicated switch independent of
        the general `provider_environment` above — so enabling live
        Duffel data never changes Accommodation/Weather's provider
        selection, which still reads `provider_environment` exactly as
        before. An explicit constructor `environment=` override (used
        throughout the test suite) always wins, for both paths, unchanged."""
        if self._environment_override is not None:
            return self._environment_override
        if capability == Capability.FLIGHTS:
            try:
                from travelos.config.configuration_manager import config
                return ProviderEnvironment.SANDBOX if config.flight_provider_mode == "LIVE_SANDBOX" else ProviderEnvironment.MOCK
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
