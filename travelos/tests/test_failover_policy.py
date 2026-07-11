"""
Failover — preferred provider fails, next eligible one is tried, the
original failure is preserved, the final result names which provider
answered, and total failure is reported clearly — docs/CACHING_AND_FAILOVER.md.
"""

from __future__ import annotations

from travelos.intelligence_gateway.failover_policy import run_with_failover
from travelos.intelligence_gateway.provider_contract import Provider, ProviderRequest
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import Capability, ProviderStatus


class _StubProvider(Provider):
    def __init__(self, name):
        self._name = name

    @property
    def provider_name(self):
        return self._name

    @property
    def capability(self):
        return Capability.FLIGHTS

    def execute(self, request):
        raise NotImplementedError  # replaced by `call` in each test


def _request():
    return ProviderRequest(capability=Capability.FLIGHTS, operation="search", params={})


class TestFailover:
    def test_first_provider_success_never_tries_the_second(self):
        first, second = _StubProvider("first"), _StubProvider("second")
        calls = []

        def call(provider, req):
            calls.append(provider.provider_name)
            return ProviderResult(provider_name=provider.provider_name, capability=Capability.FLIGHTS, status=ProviderStatus.AVAILABLE)

        outcome = run_with_failover([first, second], _request(), call)
        assert calls == ["first"]
        assert outcome.provider_used == "first"

    def test_first_provider_failure_falls_through_to_second(self):
        first, second = _StubProvider("first"), _StubProvider("second")

        def call(provider, req):
            if provider.provider_name == "first":
                raise RuntimeError("boom")
            return ProviderResult(provider_name=provider.provider_name, capability=Capability.FLIGHTS, status=ProviderStatus.AVAILABLE)

        outcome = run_with_failover([first, second], _request(), call)
        assert outcome.provider_used == "second"

    def test_original_failure_preserved_in_warnings(self):
        first, second = _StubProvider("first"), _StubProvider("second")

        def call(provider, req):
            if provider.provider_name == "first":
                raise RuntimeError("original failure reason")
            return ProviderResult(provider_name=provider.provider_name, capability=Capability.FLIGHTS, status=ProviderStatus.AVAILABLE)

        outcome = run_with_failover([first, second], _request(), call)
        assert any("original failure reason" in w for w in outcome.warnings)
        assert any("original failure reason" in w for w in outcome.result.warnings)

    def test_result_indicates_which_provider_ultimately_supplied_it(self):
        first, second, third = _StubProvider("first"), _StubProvider("second"), _StubProvider("third")

        def call(provider, req):
            if provider.provider_name in ("first", "second"):
                raise RuntimeError("down")
            return ProviderResult(provider_name="third", capability=Capability.FLIGHTS, status=ProviderStatus.AVAILABLE)

        outcome = run_with_failover([first, second, third], _request(), call)
        assert outcome.provider_used == "third"
        assert outcome.result.provider_name == "third"


class TestTotalFailure:
    def test_all_providers_failing_returns_no_result(self):
        providers = [_StubProvider("a"), _StubProvider("b")]

        def call(provider, req):
            raise RuntimeError(f"{provider.provider_name} down")

        outcome = run_with_failover(providers, _request(), call)
        assert outcome.result is None
        assert outcome.provider_used is None
        assert outcome.all_failed is True
        assert len(outcome.warnings) == 2

    def test_empty_provider_list_is_a_clear_total_failure(self):
        outcome = run_with_failover([], _request(), lambda p, r: None)
        assert outcome.all_failed is True
        assert outcome.warnings == []
