"""Backend test fixtures."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Sample payloads
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_profile() -> dict:
    return {
        "identity": {
            "name": "Test Traveller",
            "email": "test@example.com",
            "nationality": "NG",
            "nationality_iso": "NG",
            "home_city": "London",
            "home_country": "GB",
            "passport_countries": ["NG", "GB"],
        },
        "preferences": {
            "cabin_class": "economy",
            "seat_preference": "window",
            "budget_style": "moderate",
            "travel_interests": ["culture", "food"],
            "accommodation_type": "hotel",
            "dietary_requirements": [],
            "accessibility_needs": [],
        },
        "loyalty": {
            "airline_programs": [],
            "hotel_programs": [],
            "credit_cards": [],
        },
    }


@pytest.fixture
def sample_goal(sample_profile, client) -> dict:
    """Create a traveller and goal, return the goal dict."""
    profile_res = client.post("/traveller/profile", json=sample_profile)
    traveller_id = profile_res.json()["id"]

    goal_res = client.post("/goals", json={
        "traveller_id": traveller_id,
        "title": "Football Trip to Tokyo",
        "goal_type": "FOOTBALL_TRAVEL",
        "interests": ["football", "food"],
    })
    return goal_res.json()
