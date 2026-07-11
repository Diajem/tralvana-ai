"""
Trade-off detection — deterministic comparisons grounded only in fields
Discovery modules already computed (docs/EXPLAINABILITY_ENGINE.md's
Trade-off Analysis section). No score is read or recomputed here.
"""

from __future__ import annotations

from ai.explainability import tradeoff_analyser
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus


def _result(agent_name: str, data: dict, status=AgentStatus.SUCCESS) -> AgentResult:
    return AgentResult(agent_name=agent_name, status=status, confidence=0.7, data=data)


class TestFlightTradeoff:
    def test_cheaper_flight_with_more_stops_detected(self):
        flight = _result("flight_intelligence", {
            "top_option": {"estimated_price": 900, "currency": "USD", "stops": 0, "total_duration": "6h 0m"},
            "alternative_option": {"estimated_price": 500, "currency": "USD", "stops": 2, "total_duration": "11h 0m"},
        })
        tradeoffs = tradeoff_analyser.analyse({"flight_intelligence": flight})
        assert len(tradeoffs) == 1
        assert "Flights" in tradeoffs[0]
        assert "500" in tradeoffs[0] and "900" in tradeoffs[0]

    def test_no_tradeoff_when_no_alternative_option(self):
        flight = _result("flight_intelligence", {"top_option": {"estimated_price": 900}})
        assert tradeoff_analyser.analyse({"flight_intelligence": flight}) == []

    def test_no_tradeoff_when_alternative_is_not_cheaper(self):
        flight = _result("flight_intelligence", {
            "top_option": {"estimated_price": 500},
            "alternative_option": {"estimated_price": 900},
        })
        assert tradeoff_analyser.analyse({"flight_intelligence": flight}) == []

    def test_no_tradeoff_for_failed_module(self):
        flight = _result("flight_intelligence", {
            "top_option": {"estimated_price": 900},
            "alternative_option": {"estimated_price": 500},
        }, status=AgentStatus.FAILED)
        assert tradeoff_analyser.analyse({"flight_intelligence": flight}) == []


class TestAccommodationTradeoff:
    def test_cheaper_lower_rated_stay_detected(self):
        accommodation = _result("accommodation_intelligence", {
            "top_option": {"nightly_price": 45, "currency": "USD", "star_rating": 3},
            "alternative_option": {"nightly_price": 25, "currency": "USD", "star_rating": 2},
        })
        tradeoffs = tradeoff_analyser.analyse({"accommodation_intelligence": accommodation})
        assert any("Accommodation" in t for t in tradeoffs)


class TestBudgetTradeoff:
    def test_cheaper_tier_detected(self):
        budget = _result("budget_intelligence", {
            "top_option": {"total_cost_usd": 1800, "budget_style": "balanced"},
            "alternative_option": {"total_cost_usd": 1100, "budget_style": "backpacker"},
        })
        tradeoffs = tradeoff_analyser.analyse({"budget_intelligence": budget})
        assert any("Budget" in t for t in tradeoffs)


class TestVisaVsDestinationTradeoff:
    def test_involved_visa_against_strong_destination_match_detected(self):
        visa = _result("visa_intelligence", {"visa_status": "CHECK_MANUALLY"})
        destination = _result("destination_intelligence", {"top_option": {"name": "Shibuya", "match_score": 0.8}})
        tradeoffs = tradeoff_analyser.analyse({
            "visa_intelligence": visa, "destination_intelligence": destination,
        })
        assert any("Visa vs destination" in t for t in tradeoffs)

    def test_visa_free_produces_no_tradeoff(self):
        visa = _result("visa_intelligence", {"visa_status": "visa_free"})
        destination = _result("destination_intelligence", {"top_option": {"name": "Paris", "match_score": 0.9}})
        tradeoffs = tradeoff_analyser.analyse({
            "visa_intelligence": visa, "destination_intelligence": destination,
        })
        assert tradeoffs == []

    def test_weak_destination_match_produces_no_tradeoff(self):
        visa = _result("visa_intelligence", {"visa_status": "CHECK_MANUALLY"})
        destination = _result("destination_intelligence", {"top_option": {"name": "X", "match_score": 0.3}})
        tradeoffs = tradeoff_analyser.analyse({
            "visa_intelligence": visa, "destination_intelligence": destination,
        })
        assert tradeoffs == []


class TestWeatherVsPriceTradeoff:
    def test_favourable_weather_with_elevated_budget_tier_detected(self):
        weather = _result("weather_intelligence", {"weather_status": "excellent"})
        budget = _result("budget_intelligence", {"top_option": {"budget_style": "comfort"}})
        tradeoffs = tradeoff_analyser.analyse({
            "weather_intelligence": weather, "budget_intelligence": budget,
        })
        assert any("Weather vs price" in t for t in tradeoffs)

    def test_challenging_weather_produces_no_price_tradeoff(self):
        weather = _result("weather_intelligence", {"weather_status": "challenging"})
        budget = _result("budget_intelligence", {"top_option": {"budget_style": "luxury"}})
        tradeoffs = tradeoff_analyser.analyse({
            "weather_intelligence": weather, "budget_intelligence": budget,
        })
        assert tradeoffs == []


class TestConflictsPassthrough:
    def test_conflicts_appended_as_tradeoffs(self):
        conflict = "Budget tier disagrees with accommodation pick."
        tradeoffs = tradeoff_analyser.analyse({}, conflicts=[conflict])
        assert tradeoffs == [conflict]

    def test_duplicate_conflict_not_added_twice(self):
        flight = _result("flight_intelligence", {
            "top_option": {"estimated_price": 900, "stops": 0, "total_duration": "6h"},
            "alternative_option": {"estimated_price": 500, "stops": 1, "total_duration": "9h"},
        })
        flights_tradeoff = tradeoff_analyser.analyse({"flight_intelligence": flight})[0]
        result = tradeoff_analyser.analyse({"flight_intelligence": flight}, conflicts=[flights_tradeoff])
        assert result.count(flights_tradeoff) == 1


class TestDeterminism:
    def test_same_input_produces_identical_tradeoffs(self):
        flight = _result("flight_intelligence", {
            "top_option": {"estimated_price": 900, "stops": 0, "total_duration": "6h"},
            "alternative_option": {"estimated_price": 500, "stops": 1, "total_duration": "9h"},
        })
        first = tradeoff_analyser.analyse({"flight_intelligence": flight})
        second = tradeoff_analyser.analyse({"flight_intelligence": flight})
        assert first == second
