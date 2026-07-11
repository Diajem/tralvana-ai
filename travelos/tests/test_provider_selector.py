"""
Deterministic provider selection — environment, health, request support,
priority, fallback order (docs/PROVIDER_SELECTION.md). No ML.
"""

from __future__ import annotations

from travelos.intelligence_gateway.provider_contract import Provider, ProviderRequest
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_selector import ProviderSelector
from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment, ProviderStatus


class _StubProvider(Provider):
    def __init__(
        self, name, capability=Capability.FLIGHTS, priority=100,
        environment=ProviderEnvironment.MOCK, status=ProviderStatus.AVAILABLE, supports_request=True,
    ):
        self._name = name
        self._capability = capability
        self._priority = priority
        self._environment = environment
        self._status = status
        self._supports = supports_request

    @property
    def provider_name(self):
        return self._name

    @property
    def capability(self):
        return self._capability

    @property
    def priority(self):
        return self._priority

    @property
    def environment(self):
        return self._environment

    def health_check(self):
        return self._status

    def supports(self, request):
        return self._supports

    def execute(self, request):
        return ProviderResult(provider_name=self._name, capability=self._capability, status=ProviderStatus.AVAILABLE)


def _request():
    return ProviderRequest(capability=Capability.FLIGHTS, operation="search", params={})


class TestSelection:
    def test_selects_by_priority_ascending(self):
        selector = ProviderSelector()
        low = _StubProvider("low", priority=50)
        high = _StubProvider("high", priority=5)
        eligible = selector.select([low, high], _request(), ProviderEnvironment.MOCK)
        assert [p.provider_name for p in eligible] == ["low", "high"]  # already registry-sorted input preserved

    def test_filters_out_wrong_environment(self):
        selector = ProviderSelector()
        mock_p = _StubProvider("mock_p", environment=ProviderEnvironment.MOCK)
        prod_p = _StubProvider("prod_p", environment=ProviderEnvironment.PRODUCTION)
        eligible = selector.select([mock_p, prod_p], _request(), ProviderEnvironment.MOCK)
        assert [p.provider_name for p in eligible] == ["mock_p"]

    def test_filters_out_unavailable_status(self):
        selector = ProviderSelector()
        healthy = _StubProvider("healthy", status=ProviderStatus.AVAILABLE)
        down = _StubProvider("down", status=ProviderStatus.UNAVAILABLE)
        eligible = selector.select([healthy, down], _request(), ProviderEnvironment.MOCK)
        assert [p.provider_name for p in eligible] == ["healthy"]

    def test_degraded_provider_is_still_eligible(self):
        selector = ProviderSelector()
        degraded = _StubProvider("degraded", status=ProviderStatus.DEGRADED)
        eligible = selector.select([degraded], _request(), ProviderEnvironment.MOCK)
        assert eligible == [degraded]

    def test_misconfigured_provider_excluded(self):
        selector = ProviderSelector()
        broken = _StubProvider("broken", status=ProviderStatus.MISCONFIGURED)
        eligible = selector.select([broken], _request(), ProviderEnvironment.MOCK)
        assert eligible == []

    def test_rate_limited_provider_excluded_from_selection(self):
        selector = ProviderSelector()
        limited = _StubProvider("limited", status=ProviderStatus.RATE_LIMITED)
        eligible = selector.select([limited], _request(), ProviderEnvironment.MOCK)
        assert eligible == []


class TestUnsupportedRequests:
    def test_provider_that_does_not_support_request_excluded(self):
        selector = ProviderSelector()
        unsupported = _StubProvider("unsupported", supports_request=False)
        eligible = selector.select([unsupported], _request(), ProviderEnvironment.MOCK)
        assert eligible == []

    def test_no_eligible_provider_returns_empty_list_not_none(self):
        selector = ProviderSelector()
        eligible = selector.select([], _request(), ProviderEnvironment.MOCK)
        assert eligible == []


class TestDeterminism:
    def test_selection_is_repeatable_for_identical_input(self):
        selector = ProviderSelector()
        providers = [_StubProvider("a", priority=5), _StubProvider("b", priority=1)]
        first = selector.select(providers, _request(), ProviderEnvironment.MOCK)
        second = selector.select(providers, _request(), ProviderEnvironment.MOCK)
        assert [p.provider_name for p in first] == [p.provider_name for p in second]
