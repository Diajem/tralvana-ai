"""
AccommodationIntelligence._source_metadata() / recommend()'s data_source
labelling (T-039) — MOCK / DUFFEL_STAYS_SANDBOX / MOCK_FALLBACK,
duck-typed off the injected provider so a plain MockAccommodationProvider
(no gateway involved) still gets a sensible default.
"""

from __future__ import annotations

from ai.discovery.accommodation.accommodation_intelligence import AccommodationIntelligence
from ai.discovery.accommodation.mock_accommodation_provider import MockAccommodationProvider
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import Capability, ProviderStatus


class _ProviderStub:
    def __init__(self, last_result, used_mock_fallback=False):
        self.last_result = last_result
        self.used_mock_fallback = used_mock_fallback

    def search(self, destination, check_in_date, nights, adults=1, children=0, rooms=1):
        return MockAccommodationProvider().search(destination, check_in_date, nights)


def _result(provider_name: str, request_id: str = "req-456", raw_count: int | None = None) -> ProviderResult:
    return ProviderResult(
        provider_name=provider_name, capability=Capability.ACCOMMODATION, status=ProviderStatus.AVAILABLE,
        data=[], confidence=1.0, retrieved_at="2026-10-01T00:00:00+00:00", request_id=request_id,
        source_metadata={"raw_result_count": raw_count} if raw_count is not None else {},
    )


class TestPlainMockProviderDefaults:
    def test_no_last_result_attribute_defaults_to_mock(self):
        engine = AccommodationIntelligence(provider=MockAccommodationProvider())
        result = engine.recommend(destination="Paris", check_in_date="2026-09-01", nights=3)
        assert result["data_source"] == "MOCK"
        assert result["provider_status"] == "AVAILABLE"
        assert result["ranked_results_count"] == len(result["accommodation_options"])

    def test_mock_assumption_text_is_unchanged(self):
        engine = AccommodationIntelligence(provider=MockAccommodationProvider())
        result = engine.recommend(destination="Paris", check_in_date="2026-09-01", nights=3)
        assert any("deterministic mock data" in a for a in result["assumptions"])


class TestGatewayMockProvider:
    def test_mock_accommodation_provider_via_gateway_labelled_mock(self):
        stub = _ProviderStub(last_result=_result("mock_accommodation_provider"))
        engine = AccommodationIntelligence(provider=stub)
        result = engine.recommend(destination="Paris", check_in_date="2026-09-01", nights=3)
        assert result["data_source"] == "MOCK"
        assert result["request_id"] == "req-456"
        assert result["retrieved_at"] == "2026-10-01T00:00:00+00:00"


class TestDuffelStaysProvider:
    def test_duffel_stays_provider_labelled_duffel_stays_sandbox(self):
        stub = _ProviderStub(last_result=_result("duffel_stays_provider"))
        engine = AccommodationIntelligence(provider=stub)
        result = engine.recommend(destination="Paris", check_in_date="2026-09-01", nights=3)
        assert result["data_source"] == "DUFFEL_STAYS_SANDBOX"

    def test_duffel_stays_assumption_mentions_not_for_purchase(self):
        stub = _ProviderStub(last_result=_result("duffel_stays_provider"))
        engine = AccommodationIntelligence(provider=stub)
        result = engine.recommend(destination="Paris", check_in_date="2026-09-01", nights=3)
        assert any("not available for purchase" in a for a in result["assumptions"])

    def test_raw_results_count_taken_from_provider_source_metadata(self):
        stub = _ProviderStub(last_result=_result("duffel_stays_provider", raw_count=15))
        engine = AccommodationIntelligence(provider=stub)
        result = engine.recommend(destination="Paris", check_in_date="2026-09-01", nights=3)
        assert result["raw_results_count"] == 15
        # normalised/ranked reflect the actual candidate count the stub
        # returned (8, from MockAccommodationProvider's templates) — a
        # real Duffel provider's own partial-mapping-failure filtering
        # is what makes raw_results_count differ from these.
        assert result["normalised_results_count"] == 8
        assert result["ranked_results_count"] == 8


class TestMockFallback:
    def test_used_mock_fallback_labelled_mock_fallback_even_with_duffel_last_result(self):
        stub = _ProviderStub(last_result=_result("duffel_stays_provider"), used_mock_fallback=True)
        engine = AccommodationIntelligence(provider=stub)
        result = engine.recommend(destination="Paris", check_in_date="2026-09-01", nights=3)
        assert result["data_source"] == "MOCK_FALLBACK"

    def test_mock_fallback_assumption_is_explicit(self):
        stub = _ProviderStub(last_result=_result("duffel_stays_provider"), used_mock_fallback=True)
        engine = AccommodationIntelligence(provider=stub)
        result = engine.recommend(destination="Paris", check_in_date="2026-09-01", nights=3)
        assert any("mock fallback data" in a for a in result["assumptions"])


class TestProviderIdsNeverLeakAsUnderscoreFields:
    def test_public_options_never_expose_underscore_fields(self):
        engine = AccommodationIntelligence(provider=MockAccommodationProvider())
        result = engine.recommend(destination="Paris", check_in_date="2026-09-01", nights=3)
        for option in result["accommodation_options"]:
            assert "_provider_property_id" not in option
            assert "_provider_rate_id" not in option
            assert "provider_property_id" in option
            assert option["provider_property_id"] is None
            assert "data_source" in option
