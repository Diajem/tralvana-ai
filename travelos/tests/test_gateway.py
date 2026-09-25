"""
IntelligenceGateway.execute() end-to-end — cache, retry, failover, rate
limiting, and total-failure handling working together
(docs/INTELLIGENCE_GATEWAY.md).
"""

from __future__ import annotations

from travelos.intelligence_gateway.cache_policy import InMemoryCachePolicy
from travelos.intelligence_gateway.exceptions import ProviderUnavailableError, ProviderValidationError
from travelos.intelligence_gateway.gateway import IntelligenceGateway
from travelos.intelligence_gateway.provider_contract import Provider, ProviderRequest
from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import Capability, ProviderStatus
from travelos.intelligence_gateway.rate_limit_policy import RateLimitTracker
from travelos.intelligence_gateway.retry_policy import RetryPolicy


class _Provider(Provider):
    def __init__(self, name="p", priority=10, fail_times=0, raises=ProviderUnavailableError):
        self._name = name
        self._priority = priority
        self._fail_times = fail_times
        self._raises = raises
        self.calls = 0

    @property
    def provider_name(self):
        return self._name

    @property
    def capability(self):
        return Capability.FLIGHTS

    @property
    def priority(self):
        return self._priority

    def execute(self, request):
        self.calls += 1
        if self.calls <= self._fail_times:
            raise self._raises("simulated failure")
        return ProviderResult(provider_name=self._name, capability=Capability.FLIGHTS, status=ProviderStatus.AVAILABLE, data={"calls": self.calls}, confidence=1.0)


class _MarketProvider(_Provider):
    def execute(self, request):
        self.calls += 1
        if self.calls <= self._fail_times:
            raise self._raises("simulated failure")
        return ProviderResult(
            provider_name=self._name,
            capability=Capability.FLIGHTS,
            status=ProviderStatus.AVAILABLE,
            data=[{"offer": self._name}],
            confidence=1.0,
        )


def _gateway(**kwargs) -> IntelligenceGateway:
    registry = kwargs.pop("registry", ProviderRegistry())
    return IntelligenceGateway(registry=registry, retry_policy=kwargs.pop("retry_policy", RetryPolicy(base_delay_seconds=0.0)), **kwargs)


def _req(params=None):
    return ProviderRequest(capability=Capability.FLIGHTS, operation="search", params=params or {})


class TestCacheHitAndMiss:
    def test_second_identical_call_is_a_cache_hit(self):
        registry = ProviderRegistry()
        provider = _Provider()
        registry.register(provider)
        gw = _gateway(registry=registry)

        first = gw.execute(Capability.FLIGHTS, _req({"x": 1}))
        second = gw.execute(Capability.FLIGHTS, _req({"x": 1}))
        assert first.cached is False
        assert second.cached is True
        assert provider.calls == 1  # provider only called once

    def test_different_params_are_not_a_cache_hit(self):
        registry = ProviderRegistry()
        provider = _Provider()
        registry.register(provider)
        gw = _gateway(registry=registry)

        gw.execute(Capability.FLIGHTS, _req({"x": 1}))
        gw.execute(Capability.FLIGHTS, _req({"x": 2}))
        assert provider.calls == 2

    def test_bypass_cache_forces_a_fresh_call(self):
        registry = ProviderRegistry()
        provider = _Provider()
        registry.register(provider)
        gw = _gateway(registry=registry)

        gw.execute(Capability.FLIGHTS, _req({"x": 1}))
        req = _req({"x": 1})
        req.bypass_cache = True
        gw.execute(Capability.FLIGHTS, req)
        assert provider.calls == 2

    def test_cache_disabled_never_hits(self):
        registry = ProviderRegistry()
        provider = _Provider()
        registry.register(provider)
        gw = _gateway(registry=registry, cache=InMemoryCachePolicy(enabled=False))

        gw.execute(Capability.FLIGHTS, _req({"x": 1}))
        gw.execute(Capability.FLIGHTS, _req({"x": 1}))
        assert provider.calls == 2


class TestRetryBehaviour:
    def test_transient_failure_recovers_within_max_attempts(self):
        registry = ProviderRegistry()
        provider = _Provider(fail_times=2)
        registry.register(provider)
        gw = _gateway(registry=registry)

        result = gw.execute(Capability.FLIGHTS, _req())
        assert result.status == ProviderStatus.AVAILABLE
        assert provider.calls == 3

    def test_non_retryable_error_fails_after_one_attempt(self):
        registry = ProviderRegistry()
        provider = _Provider(fail_times=99, raises=ProviderValidationError)
        registry.register(provider)
        gw = _gateway(registry=registry)

        result = gw.execute(Capability.FLIGHTS, _req())
        assert result.status == ProviderStatus.UNAVAILABLE
        assert provider.calls == 1


class TestFailover:
    def test_preferred_provider_failure_falls_over_to_next(self):
        registry = ProviderRegistry()
        primary = _Provider(name="primary", priority=1, fail_times=99)
        backup = _Provider(name="backup", priority=2)
        registry.register(primary)
        registry.register(backup)
        gw = _gateway(registry=registry)

        result = gw.execute(Capability.FLIGHTS, _req())
        assert result.provider_name == "backup"
        assert any("primary" in w for w in result.warnings)

    def test_total_provider_failure_returns_unavailable(self):
        registry = ProviderRegistry()
        registry.register(_Provider(name="only", fail_times=99))
        gw = _gateway(registry=registry)

        result = gw.execute(Capability.FLIGHTS, _req())
        assert result.status == ProviderStatus.UNAVAILABLE
        assert result.errors != []

    def test_no_registered_provider_returns_unavailable_with_clear_error(self):
        gw = _gateway(registry=ProviderRegistry())
        result = gw.execute(Capability.FLIGHTS, _req())
        assert result.status == ProviderStatus.UNAVAILABLE
        assert "No eligible provider" in result.errors[0]


class TestMarketWideSearch:
    def test_queries_and_combines_every_eligible_provider(self):
        registry = ProviderRegistry()
        first = _MarketProvider(name="first", priority=1)
        second = _MarketProvider(name="second", priority=2)
        registry.register(first)
        registry.register(second)
        gw = _gateway(registry=registry)

        result = gw.execute_market_search(Capability.FLIGHTS, _req())

        assert first.calls == 1
        assert second.calls == 1
        assert result.provider_name == "multi_provider"
        assert [item["_market_provider_name"] for item in result.data] == ["first", "second"]
        assert result.source_metadata["providers_queried"] == ["first", "second"]

    def test_empty_first_supplier_does_not_hide_second_supplier_inventory(self):
        class _EmptyProvider(_MarketProvider):
            def execute(self, request):
                self.calls += 1
                return ProviderResult(
                    provider_name=self.provider_name,
                    capability=Capability.FLIGHTS,
                    status=ProviderStatus.AVAILABLE,
                    data=[],
                    confidence=1.0,
                )

        registry = ProviderRegistry()
        empty = _EmptyProvider(name="empty", priority=1)
        inventory = _MarketProvider(name="inventory", priority=2)
        registry.register(empty)
        registry.register(inventory)
        gw = _gateway(registry=registry)

        result = gw.execute_market_search(Capability.FLIGHTS, _req())

        assert result.ok
        assert len(result.data) == 1
        assert result.data[0]["_market_provider_name"] == "inventory"
        assert len(result.source_metadata["providers_succeeded"]) == 2
        assert result.source_metadata["providers_empty"] == ["empty"]

    def test_all_reachable_but_empty_suppliers_are_not_reported_as_available_inventory(self):
        class _EmptyProvider(_MarketProvider):
            def execute(self, request):
                self.calls += 1
                return ProviderResult(
                    provider_name=self.provider_name,
                    capability=Capability.FLIGHTS,
                    status=ProviderStatus.AVAILABLE,
                    data=[],
                    confidence=1.0,
                )

        registry = ProviderRegistry()
        registry.register(_EmptyProvider(name="one", priority=1))
        registry.register(_EmptyProvider(name="two", priority=2))
        result = _gateway(registry=registry).execute_market_search(
            Capability.FLIGHTS, _req()
        )

        assert result.status == ProviderStatus.DEGRADED
        assert result.data == []
        assert result.source_metadata["mapped_result_count"] == 0
        assert result.source_metadata["providers_empty"] == ["one", "two"]

    def test_partial_failure_keeps_other_supplier_inventory(self):
        registry = ProviderRegistry()
        failed = _MarketProvider(name="failed", priority=1, fail_times=99)
        healthy = _MarketProvider(name="healthy", priority=2)
        registry.register(failed)
        registry.register(healthy)
        gw = _gateway(registry=registry)

        result = gw.execute_market_search(Capability.FLIGHTS, _req())

        assert result.ok
        assert result.status == ProviderStatus.DEGRADED
        assert result.data[0]["_market_provider_name"] == "healthy"
        assert result.source_metadata["providers_failed"] == ["failed"]

    def test_unavailable_only_after_every_supplier_fails(self):
        registry = ProviderRegistry()
        registry.register(_MarketProvider(name="one", priority=1, fail_times=99))
        registry.register(_MarketProvider(name="two", priority=2, fail_times=99))
        gw = _gateway(registry=registry)

        result = gw.execute_market_search(Capability.FLIGHTS, _req())

        assert result.status == ProviderStatus.UNAVAILABLE
        assert result.errors == ["All eligible providers failed"]


class TestRateLimitedFailover:
    def test_rate_limited_provider_is_skipped_in_favour_of_next(self):
        registry = ProviderRegistry()
        primary = _Provider(name="primary", priority=1)
        backup = _Provider(name="backup", priority=2)
        registry.register(primary)
        registry.register(backup)

        rate_limiter = RateLimitTracker()
        rate_limiter.configure("primary", limit=0, window_seconds=60)
        gw = _gateway(registry=registry, rate_limiter=rate_limiter)

        result = gw.execute(Capability.FLIGHTS, _req())
        assert result.provider_name == "backup"
        assert primary.calls == 0

    def test_all_providers_rate_limited_returns_unavailable(self):
        registry = ProviderRegistry()
        registry.register(_Provider(name="only"))
        rate_limiter = RateLimitTracker()
        rate_limiter.configure("only", limit=0, window_seconds=60)
        gw = _gateway(registry=registry, rate_limiter=rate_limiter)

        result = gw.execute(Capability.FLIGHTS, _req())
        assert result.status == ProviderStatus.UNAVAILABLE


class TestRequestIdAndLatency:
    def test_every_result_has_a_request_id(self):
        registry = ProviderRegistry()
        registry.register(_Provider())
        gw = _gateway(registry=registry)
        result = gw.execute(Capability.FLIGHTS, _req())
        assert result.request_id != ""

    def test_latency_is_recorded_and_non_negative(self):
        registry = ProviderRegistry()
        registry.register(_Provider())
        gw = _gateway(registry=registry)
        result = gw.execute(Capability.FLIGHTS, _req())
        assert result.latency_ms >= 0
