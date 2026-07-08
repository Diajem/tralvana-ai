"""AI test fixtures — sample profiles and goal dicts."""
import pytest


@pytest.fixture
def football_profile() -> dict:
    return {
        "id": "test-traveller-001",
        "identity": {
            "name": "Alex Okafor",
            "nationality": "NG",
            "nationality_iso": "NG",
            "home_city": "Manchester",
            "home_country": "GB",
            "passport_countries": ["NG", "GB"],
        },
        "preferences": {
            "cabin_class": "economy",
            "budget_style": "moderate",
            "travel_interests": ["sport", "food_drink", "culture"],
            "accommodation_type": "hotel",
        },
        "loyalty": {
            "airline_programs": [],
        },
    }


@pytest.fixture
def luxury_profile() -> dict:
    return {
        "id": "test-traveller-002",
        "identity": {
            "name": "Sophia Laurent",
            "nationality": "FR",
            "nationality_iso": "FR",
            "home_city": "Paris",
            "home_country": "FR",
            "passport_countries": ["FR"],
        },
        "preferences": {
            "cabin_class": "first",
            "budget_style": "luxury",
            "travel_interests": ["luxury", "food_drink", "art_culture"],
            "accommodation_type": "resort",
        },
        "loyalty": {
            "airline_programs": ["Air France Flying Blue"],
        },
    }


@pytest.fixture
def sample_goal() -> dict:
    return {
        "goal_id": "goal-001",
        "traveller_id": "test-traveller-001",
        "title": "Football & Food Tour — Japan",
        "goal_type": "FOOTBALL_TRAVEL",
        "destination": "Japan",
        "duration_days": 10,
        "budget_style": "moderate",
        "cabin_class": "economy",
        "adults": 2,
        "children": 0,
        "interests": ["football", "food", "photography"],
        "status": "DRAFT",
        "budget": {"min_usd": 2000, "max_usd": 2500, "currency": "USD"},
        "timeframe": {"duration_days": 10, "flexible": True},
        "travellers": {"adults": 2, "children": 0, "infants": 0},
        "constraints": [],
        "success_criteria": [],
        "flexibility": {"dates": True, "duration": True, "budget": False},
        "planning_readiness_score": 1.0,
        "missing_information": [],
        "suitable_agents": ["football_agent", "hotel_agent"],
        "created_at": "2026-07-08T00:00:00+00:00",
        "updated_at": "2026-07-08T00:00:00+00:00",
    }
