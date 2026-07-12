"""
FlightIntelligence._source_metadata() / recommend()'s data_source
labelling (T-038) — MOCK / DUFFEL_SANDBOX / MOCK_FALLBACK, duck-typed
off the injected provider so a plain MockFlightProvider (no gateway
involved) still gets a sensible default.
"""

from __future__ import annotations

from ai.discovery.flights.flight_intelligence import FlightIntelligence, MockFlightProvider
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import Capability, ProviderStatus


class _ProviderStub:
    """Duck-types GatewayFlightProvider's public surface without any
    Intelligence Gateway involvement — isolates FlightIntelligence's own
    metadata-attachment logic from gateway/provider behaviour, already
    covered by travelos/tests/test_gateway_flight_provider_fallback.py."""

    def __init__(self, last_result, used_mock_fallback=False):
        self.last_result = last_result
        self.used_mock_fallback = used_mock_fallback

    def search(self, origin, destination, departure_date, return_date, cabin_class):
        return MockFlightProvider().search(origin, destination, departure_date, return_date, cabin_class)


def _result(provider_name: str, request_id: str = "req-123") -> ProviderResult:
    return ProviderResult(
        provider_name=provider_name, capability=Capability.FLIGHTS, status=ProviderStatus.AVAILABLE,
        data=[], confidence=1.0, retrieved_at="2026-10-01T00:00:00+00:00", request_id=request_id,
    )


class TestPlainMockProviderDefaults:
    def test_no_last_result_attribute_defaults_to_mock(self):
        engine = FlightIntelligence(provider=MockFlightProvider())
        result = engine.recommend(origin="London", destination="Paris", departure_date="2026-09-01", return_date=None)
        assert result["data_source"] == "MOCK"
        assert result["provider_status"] == "AVAILABLE"
        assert result["results_count"] == len(result["flight_options"])

    def test_mock_assumption_text_is_unchanged(self):
        engine = FlightIntelligence(provider=MockFlightProvider())
        result = engine.recommend(origin="London", destination="Paris", departure_date="2026-09-01", return_date=None)
        assert any("deterministic mock data" in a for a in result["assumptions"])


class TestGatewayMockProvider:
    def test_mock_flight_provider_via_gateway_labelled_mock(self):
        stub = _ProviderStub(last_result=_result("mock_flight_provider"))
        engine = FlightIntelligence(provider=stub)
        result = engine.recommend(origin="London", destination="Paris", departure_date="2026-09-01", return_date=None)
        assert result["data_source"] == "MOCK"
        assert result["request_id"] == "req-123"
        assert result["retrieved_at"] == "2026-10-01T00:00:00+00:00"


class TestDuffelProvider:
    def test_duffel_provider_labelled_duffel_sandbox(self):
        stub = _ProviderStub(last_result=_result("duffel_flight_provider"))
        engine = FlightIntelligence(provider=stub)
        result = engine.recommend(origin="London", destination="Paris", departure_date="2026-09-01", return_date=None)
        assert result["data_source"] == "DUFFEL_SANDBOX"

    def test_duffel_sandbox_assumption_mentions_not_for_purchase(self):
        stub = _ProviderStub(last_result=_result("duffel_flight_provider"))
        engine = FlightIntelligence(provider=stub)
        result = engine.recommend(origin="London", destination="Paris", departure_date="2026-09-01", return_date=None)
        assert any("not available for purchase" in a for a in result["assumptions"])


class TestMockFallback:
    def test_used_mock_fallback_labelled_mock_fallback_even_with_duffel_last_result(self):
        # The realistic shape: last_result is the FAILED live attempt,
        # but used_mock_fallback signals the returned data is mock.
        stub = _ProviderStub(last_result=_result("duffel_flight_provider"), used_mock_fallback=True)
        engine = FlightIntelligence(provider=stub)
        result = engine.recommend(origin="London", destination="Paris", departure_date="2026-09-01", return_date=None)
        assert result["data_source"] == "MOCK_FALLBACK"

    def test_mock_fallback_assumption_is_explicit(self):
        stub = _ProviderStub(last_result=_result("duffel_flight_provider"), used_mock_fallback=True)
        engine = FlightIntelligence(provider=stub)
        result = engine.recommend(origin="London", destination="Paris", departure_date="2026-09-01", return_date=None)
        assert any("mock fallback data" in a for a in result["assumptions"])


class TestProviderOfferIdNeverLeaksAsUnderscoreField:
    def test_public_options_never_expose_the_underscore_field(self):
        engine = FlightIntelligence(provider=MockFlightProvider())
        result = engine.recommend(origin="London", destination="Paris", departure_date="2026-09-01", return_date=None)
        for option in result["flight_options"]:
            assert "_provider_offer_id" not in option
            assert "provider_offer_id" in option  # present, just None for mock data
            assert option["provider_offer_id"] is None
