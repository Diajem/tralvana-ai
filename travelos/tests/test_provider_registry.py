"""Provider registration and capability lookup — docs/INTELLIGENCE_GATEWAY.md."""

from __future__ import annotations

from travelos.intelligence_gateway.provider_contract import Provider, ProviderRequest
from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import Capability, ProviderStatus


class _StubProvider(Provider):
    def __init__(self, name: str, capability: Capability, priority: int = 100) -> None:
        self._name = name
        self._capability = capability
        self._priority = priority

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def capability(self) -> Capability:
        return self._capability

    @property
    def priority(self) -> int:
        return self._priority

    def execute(self, request: ProviderRequest) -> ProviderResult:
        return ProviderResult(provider_name=self._name, capability=self._capability, status=ProviderStatus.AVAILABLE)


class TestRegistration:
    def test_register_makes_provider_retrievable_by_capability(self):
        registry = ProviderRegistry()
        provider = _StubProvider("p1", Capability.FLIGHTS)
        registry.register(provider)
        assert registry.get_providers(Capability.FLIGHTS) == [provider]

    def test_unknown_capability_returns_empty_list(self):
        registry = ProviderRegistry()
        assert registry.get_providers(Capability.VISA) == []

    def test_multiple_providers_for_same_capability_all_returned(self):
        registry = ProviderRegistry()
        p1 = _StubProvider("p1", Capability.WEATHER)
        p2 = _StubProvider("p2", Capability.WEATHER)
        registry.register(p1)
        registry.register(p2)
        assert set(registry.get_providers(Capability.WEATHER)) == {p1, p2}

    def test_providers_sorted_by_priority_ascending(self):
        registry = ProviderRegistry()
        low = _StubProvider("low_priority", Capability.FLIGHTS, priority=50)
        high = _StubProvider("high_priority", Capability.FLIGHTS, priority=5)
        registry.register(low)
        registry.register(high)
        assert [p.provider_name for p in registry.get_providers(Capability.FLIGHTS)] == [
            "high_priority", "low_priority",
        ]

    def test_equal_priority_keeps_registration_order(self):
        registry = ProviderRegistry()
        first = _StubProvider("first", Capability.FLIGHTS, priority=10)
        second = _StubProvider("second", Capability.FLIGHTS, priority=10)
        registry.register(first)
        registry.register(second)
        assert [p.provider_name for p in registry.get_providers(Capability.FLIGHTS)] == ["first", "second"]


class TestCapabilityLookup:
    def test_capabilities_lists_every_registered_capability(self):
        registry = ProviderRegistry()
        registry.register(_StubProvider("flight_p", Capability.FLIGHTS))
        registry.register(_StubProvider("weather_p", Capability.WEATHER))
        assert set(registry.capabilities()) == {Capability.FLIGHTS, Capability.WEATHER}

    def test_all_capabilities_supported(self):
        # Every capability named in T-025's brief must at least be a
        # valid enum member, whether or not a provider is registered yet.
        for name in ("FLIGHTS", "ACCOMMODATION", "DESTINATIONS", "BUDGET", "VISA", "WEATHER", "MAPS", "CURRENCY", "EVENTS"):
            assert Capability(name).value == name

    def test_all_providers_returns_every_registered_provider(self):
        registry = ProviderRegistry()
        p1 = _StubProvider("p1", Capability.FLIGHTS)
        p2 = _StubProvider("p2", Capability.WEATHER)
        registry.register(p1)
        registry.register(p2)
        assert set(registry.all_providers()) == {p1, p2}

    def test_clear_removes_all_providers(self):
        registry = ProviderRegistry()
        registry.register(_StubProvider("p1", Capability.FLIGHTS))
        registry.clear()
        assert registry.get_providers(Capability.FLIGHTS) == []
        assert registry.capabilities() == []
