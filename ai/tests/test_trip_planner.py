import pytest

from ai.planning.trip_planner import TripPlanner


@pytest.fixture
def planner() -> TripPlanner:
    return TripPlanner()


@pytest.fixture
def base_plan_kwargs(football_profile) -> dict:
    return {
        "origin": "Manchester",
        "destination": "Tokyo",
        "duration_days": 10,
        "budget_style": "moderate",
        "cabin_class": "economy",
        "interests": ["football", "food"],
        "travellers": {"adults": 2, "children": 0},
        "goal_type": "FOOTBALL_TRAVEL",
        "profile": football_profile,
    }


class TestTripPlanner:
    def test_plan_returns_dict(self, planner, base_plan_kwargs):
        result = planner.plan(**base_plan_kwargs)
        assert isinstance(result, dict)

    def test_itinerary_has_correct_day_count(self, planner, base_plan_kwargs):
        result = planner.plan(**base_plan_kwargs)
        assert len(result["draft_itinerary"]) == 10

    def test_first_day_is_arrival(self, planner, base_plan_kwargs):
        result = planner.plan(**base_plan_kwargs)
        first_day = result["draft_itinerary"][0]
        assert "arrival" in first_day["title"].lower() or first_day["day"] == 1

    def test_last_day_is_departure(self, planner, base_plan_kwargs):
        result = planner.plan(**base_plan_kwargs)
        last_day = result["draft_itinerary"][-1]
        assert "departure" in last_day["title"].lower() or last_day["day"] == 10

    def test_budget_breakdown_has_total(self, planner, base_plan_kwargs):
        result = planner.plan(**base_plan_kwargs)
        budget = result["estimated_budget_breakdown"]
        assert "total_estimate_usd" in budget
        assert budget["total_estimate_usd"] > 0

    def test_risks_is_non_empty_list(self, planner, base_plan_kwargs):
        result = planner.plan(**base_plan_kwargs)
        assert isinstance(result["risks"], list)
        assert len(result["risks"]) > 0

    def test_confidence_is_float_in_range(self, planner, base_plan_kwargs):
        result = planner.plan(**base_plan_kwargs)
        confidence = result["confidence"]
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    def test_recommended_agents_for_goal_type(self, planner, base_plan_kwargs):
        result = planner.plan(**base_plan_kwargs)
        assert isinstance(result["recommended_agents"], list)
        assert len(result["recommended_agents"]) > 0

    def test_next_actions_is_list(self, planner, base_plan_kwargs):
        result = planner.plan(**base_plan_kwargs)
        assert isinstance(result["next_actions"], list)

    def test_missing_destination_generates_recommendations(self, planner, football_profile):
        result = planner.plan(
            origin="London",
            destination="",
            duration_days=7,
            budget_style="moderate",
            cabin_class="economy",
            interests=["football"],
            travellers={"adults": 1},
            goal_type="FOOTBALL_TRAVEL",
            profile=football_profile,
        )
        assert len(result["recommended_destinations"]) > 0

    def test_known_destination_no_recommendations(self, planner, base_plan_kwargs):
        result = planner.plan(**base_plan_kwargs)
        assert result["recommended_destinations"] == []

    def test_trip_summary_mentions_destination(self, planner, base_plan_kwargs):
        result = planner.plan(**base_plan_kwargs)
        assert "Tokyo" in result["trip_summary"]

    def test_short_trip_correct_day_count(self, planner, football_profile):
        result = planner.plan(
            origin="London",
            destination="Paris",
            duration_days=3,
            budget_style="budget",
            cabin_class="economy",
            interests=["culture"],
            travellers={"adults": 1},
            goal_type="GENERAL_TRAVEL",
            profile=football_profile,
        )
        assert len(result["draft_itinerary"]) == 3
