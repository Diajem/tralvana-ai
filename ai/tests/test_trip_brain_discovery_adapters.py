"""
Discovery adapter tests. Each adapter's only external call is the same
public `*_from_conversation()` service method ConversationEngine already
calls for narrow intents — monkeypatched here at the service singleton so
these tests exercise the adapter's own wrapping/failure-isolation logic
without depending on the real mock providers' data.
"""

from ai.shared.agent_status import AgentStatus
from ai.ports import configure_planning_port
from ai.trip_brain.context import TripBrainContext
from ai.trip_brain.discovery_adapters import (
    run_accommodation_intelligence,
    run_budget_intelligence,
    run_destination_intelligence,
    run_event_intelligence,
    run_flight_intelligence,
    run_visa_intelligence,
    run_weather_intelligence,
)
from app.adapters.planning_adapter import PlanningAdapter

configure_planning_port(PlanningAdapter())


def _context() -> TripBrainContext:
    return TripBrainContext(
        traveller_id="t-1", trip_id=None, goal_id=None,
        entities={"destination": "Tokyo"},
    )


def _option(**overrides) -> dict:
    base = {
        "match_score": 0.8,
        "recommendation_type": "GOOD_MATCH",
        "risks": ["some risk"],
    }
    base.update(overrides)
    return base


class TestFlightAdapter:
    def test_success_picks_best_overall_and_average_confidence(self, monkeypatch):
        from app.domains.flights.service import flight_intelligence_service

        options = [
            _option(flight_option_id="f1", match_score=0.6, recommendation_type="GOOD_MATCH"),
            _option(flight_option_id="f2", match_score=0.9, recommendation_type="BEST_OVERALL"),
        ]
        monkeypatch.setattr(
            flight_intelligence_service,
            "recommend_from_conversation",
            lambda **kwargs: {
                "origin": "London",
                "destination": "Tokyo",
                "flight_options": options,
                "assumptions": ["a1"],
                "next_actions": ["n1"],
                "data_source": "DUFFEL_SANDBOX",
                "provider_status": "AVAILABLE",
                "retrieved_at": "2026-07-25T12:00:00+00:00",
            },
        )

        result = run_flight_intelligence(_context())
        assert result.agent_name == "flight_intelligence"
        assert result.status == AgentStatus.SUCCESS
        assert result.confidence == 0.75
        assert result.data["top_option"]["flight_option_id"] == "f2"
        assert result.data["top_option"]["data_source"] == "DUFFEL_SANDBOX"
        assert (
            result.data["top_option"]["retrieved_at"]
            == "2026-07-25T12:00:00+00:00"
        )
        assert result.assumptions == ["a1"]
        assert result.next_actions == ["n1"]

    def test_empty_options_is_needs_information_not_failed(self, monkeypatch):
        from app.domains.flights.service import flight_intelligence_service

        monkeypatch.setattr(
            flight_intelligence_service,
            "recommend_from_conversation",
            lambda **kwargs: {
                "origin": "London", "destination": "Tokyo",
                "flight_options": [], "assumptions": [], "next_actions": [],
            },
        )
        result = run_flight_intelligence(_context())
        assert result.status == AgentStatus.NEEDS_INFORMATION
        assert result.confidence == 0.0

    def test_exception_is_isolated_as_failed(self, monkeypatch):
        from app.domains.flights.service import flight_intelligence_service

        def _raise(**kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(flight_intelligence_service, "recommend_from_conversation", _raise)
        result = run_flight_intelligence(_context())
        assert result.status == AgentStatus.FAILED
        assert result.confidence == 0.0
        assert "boom" in result.risks[0]


class TestAccommodationAdapter:
    def test_success_preserves_safe_source_metadata_on_top_option(self, monkeypatch):
        from app.domains.accommodation.service import accommodation_intelligence_service

        options = [
            _option(
                accommodation_option_id="a1",
                recommendation_type="BEST_OVERALL",
                data_source="DUFFEL_STAYS_SANDBOX",
            )
        ]
        monkeypatch.setattr(
            accommodation_intelligence_service,
            "recommend_from_conversation",
            lambda **kwargs: {
                "destination": "Tokyo",
                "accommodation_options": options,
                "assumptions": [],
                "next_actions": [],
                "data_source": "DUFFEL_STAYS_SANDBOX",
                "provider_status": "AVAILABLE",
                "retrieved_at": "2026-07-25T12:00:00+00:00",
            },
        )

        result = run_accommodation_intelligence(_context())

        assert result.data["top_option"]["data_source"] == "DUFFEL_STAYS_SANDBOX"
        assert (
            result.data["top_option"]["retrieved_at"]
            == "2026-07-25T12:00:00+00:00"
        )

    def test_exception_is_isolated_as_failed(self, monkeypatch):
        from app.domains.accommodation.service import accommodation_intelligence_service

        def _raise(**kwargs):
            raise RuntimeError("no data")

        monkeypatch.setattr(
            accommodation_intelligence_service, "recommend_from_conversation", _raise
        )
        result = run_accommodation_intelligence(_context())
        assert result.status == AgentStatus.FAILED
        assert result.agent_name == "accommodation_intelligence"


class TestDestinationAdapter:
    def test_exception_is_isolated_as_failed(self, monkeypatch):
        from app.domains.destinations.service import destination_intelligence_service

        def _raise(**kwargs):
            raise RuntimeError("no data")

        monkeypatch.setattr(
            destination_intelligence_service, "recommend_from_conversation", _raise
        )
        result = run_destination_intelligence(_context())
        assert result.status == AgentStatus.FAILED
        assert result.agent_name == "destination_intelligence"


class TestBudgetAdapter:
    def test_missing_budget_requests_information_without_running_estimator(
        self, monkeypatch
    ):
        from app.domains.budget.service import budget_intelligence_service

        def _raise(**kwargs):
            raise RuntimeError("no data")

        monkeypatch.setattr(budget_intelligence_service, "recommend_from_conversation", _raise)
        result = run_budget_intelligence(_context())
        assert result.status == AgentStatus.NEEDS_INFORMATION
        assert result.agent_name == "budget_intelligence"
        assert "budget" in result.next_actions[0].lower()


class TestVisaAdapter:
    def test_success_passes_through_confidence_and_fields(self, monkeypatch):
        from app.domains.visa.service import visa_intelligence_service

        monkeypatch.setattr(
            visa_intelligence_service,
            "check_from_conversation",
            lambda **kwargs: {
                "nationality": "NG", "destination_country": "Japan",
                "visa_status": "VISA_REQUIRED", "confidence": 0.9,
                "risks": ["r1"], "assumptions": ["a1"], "recommendation": "apply early",
            },
        )
        result = run_visa_intelligence(_context())
        assert result.status == AgentStatus.SUCCESS
        assert result.confidence == 0.9
        assert result.next_actions == ["apply early"]

    def test_exception_is_isolated_as_failed(self, monkeypatch):
        from app.domains.visa.service import visa_intelligence_service

        def _raise(**kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(visa_intelligence_service, "check_from_conversation", _raise)
        result = run_visa_intelligence(_context())
        assert result.status == AgentStatus.FAILED
        assert result.agent_name == "visa_intelligence"


class TestWeatherAdapter:
    def test_success_passes_through_confidence_and_fields(self, monkeypatch):
        from app.domains.weather.service import weather_intelligence_service

        monkeypatch.setattr(
            weather_intelligence_service,
            "analyse_from_conversation",
            lambda **kwargs: {
                "destination": "Tokyo", "month_of_travel": 10, "confidence": 0.4,
                "risks": [], "assumptions": [], "recommendation": "go for it",
            },
        )
        result = run_weather_intelligence(_context())
        assert result.status == AgentStatus.SUCCESS
        assert result.confidence == 0.4

    def test_exception_is_isolated_as_failed(self, monkeypatch):
        from app.domains.weather.service import weather_intelligence_service

        def _raise(**kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(weather_intelligence_service, "analyse_from_conversation", _raise)
        result = run_weather_intelligence(_context())
        assert result.status == AgentStatus.FAILED
        assert result.agent_name == "weather_intelligence"


class TestEventAdapter:
    def test_success_preserves_curated_options_and_source(self, monkeypatch):
        from app.domains.events.service import event_intelligence_service

        option = _option(
            event_option_id="e1",
            recommendation_type="BEST_OVERALL",
            data_source="TRALVANA_CURATED_EVENT_IDEAS",
        )
        monkeypatch.setattr(
            event_intelligence_service,
            "recommend_from_conversation",
            lambda **kwargs: {
                "destination": "New York",
                "start_date": "2026-08-07",
                "end_date": "2026-08-22",
                "event_options": [option],
                "data_source": "TRALVANA_CURATED_EVENT_IDEAS",
                "provider_status": "AVAILABLE",
                "retrieved_at": "2026-07-25T20:00:00+00:00",
                "assumptions": ["curated"],
                "next_actions": ["confirm"],
            },
        )

        result = run_event_intelligence(_context())

        assert result.status == AgentStatus.SUCCESS
        assert result.data["top_option"]["event_option_id"] == "e1"
        assert result.data["options"] == [option]
        assert result.data["data_source"] == "TRALVANA_CURATED_EVENT_IDEAS"

    def test_exception_is_isolated_as_failed(self, monkeypatch):
        from app.domains.events.service import event_intelligence_service

        def _raise(**kwargs):
            raise RuntimeError("events down")

        monkeypatch.setattr(
            event_intelligence_service, "recommend_from_conversation", _raise
        )
        result = run_event_intelligence(_context())
        assert result.status == AgentStatus.FAILED
        assert result.agent_name == "event_intelligence"
