"""
Deterministic mock-provider behaviour through the gateway — the
Gateway*Provider adapters must produce byte-identical output to calling
the underlying Mock*Provider directly (docs/INTELLIGENCE_GATEWAY.md's
Discovery Integration section). This is what makes wiring the gateway
into FlightIntelligence/AccommodationIntelligence/WeatherIntelligence
behaviour-preserving.
"""

from __future__ import annotations

from travelos.intelligence_gateway.discovery_adapters import (
    GatewayAccommodationProvider,
    GatewayFlightProvider,
    GatewayWeatherProvider,
)
from travelos.intelligence_gateway.provider_registry import provider_registry
from travelos.intelligence_gateway.provider_status import Capability


class TestProvidersAccessibleThroughTheGateway:
    def test_flights_registered(self):
        names = [p.provider_name for p in provider_registry.get_providers(Capability.FLIGHTS)]
        assert "mock_flight_provider" in names

    def test_accommodation_registered(self):
        names = [p.provider_name for p in provider_registry.get_providers(Capability.ACCOMMODATION)]
        assert "mock_accommodation_provider" in names

    def test_weather_registered(self):
        names = [p.provider_name for p in provider_registry.get_providers(Capability.WEATHER)]
        assert "mock_weather_provider" in names


class TestFlightDeterminism:
    def test_gateway_backed_search_matches_direct_mock_provider(self):
        from ai.discovery.flights.flight_intelligence import MockFlightProvider

        direct = MockFlightProvider().search("LON", "Tokyo", "2026-10-01", None, "economy")
        via_gateway = GatewayFlightProvider().search("LON", "Tokyo", "2026-10-01", None, "economy")
        assert direct == via_gateway

    def test_repeated_calls_are_stable(self):
        first = GatewayFlightProvider().search("LON", "Paris", "2026-06-01", None, "economy")
        second = GatewayFlightProvider().search("LON", "Paris", "2026-06-01", None, "economy")
        assert first == second


class TestAccommodationDeterminism:
    def test_gateway_backed_search_matches_direct_mock_provider(self):
        from ai.discovery.accommodation.mock_accommodation_provider import MockAccommodationProvider

        direct = MockAccommodationProvider().search("Tokyo", "2026-10-01", 7)
        via_gateway = GatewayAccommodationProvider().search("Tokyo", "2026-10-01", 7)
        assert direct == via_gateway


class TestWeatherDeterminism:
    def test_month_matches_direct_mock_provider(self):
        from ai.discovery.weather.mock_weather_provider import MockWeatherProvider

        direct = MockWeatherProvider().month("Japan", 10)
        via_gateway = GatewayWeatherProvider().month("Japan", 10)
        assert direct == via_gateway

    def test_year_matches_direct_mock_provider(self):
        from ai.discovery.weather.mock_weather_provider import MockWeatherProvider

        direct = MockWeatherProvider().year("Japan")
        via_gateway = GatewayWeatherProvider().year("Japan")
        assert direct == via_gateway

    def test_known_destinations_matches_direct_mock_provider(self):
        from ai.discovery.weather.mock_weather_provider import MockWeatherProvider

        direct = MockWeatherProvider().known_destinations()
        via_gateway = GatewayWeatherProvider().known_destinations()
        assert direct == via_gateway

    def test_unknown_destination_month_falls_back_to_unmatched_shape(self):
        via_gateway = GatewayWeatherProvider().month("Nowhereland", 5)
        assert via_gateway["matched"] is False
        assert via_gateway["destination"] == "Nowhereland"


class TestSingletonsUseTheGatewayBackedProvider:
    def test_flight_intelligence_singleton_uses_gateway_provider(self):
        from ai.discovery.flights.flight_intelligence import flight_intelligence
        assert isinstance(flight_intelligence._provider, GatewayFlightProvider)

    def test_accommodation_intelligence_singleton_uses_gateway_provider(self):
        from ai.discovery.accommodation.accommodation_intelligence import accommodation_intelligence
        assert isinstance(accommodation_intelligence._provider, GatewayAccommodationProvider)

    def test_weather_intelligence_singleton_uses_gateway_provider(self):
        from ai.discovery.weather.weather_intelligence import weather_intelligence
        assert isinstance(weather_intelligence._provider, GatewayWeatherProvider)
