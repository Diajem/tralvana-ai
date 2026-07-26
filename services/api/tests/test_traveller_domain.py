from app.domains.traveller.models import TravellerProfile
from app.domains.traveller.repository import TravellerRepository
from app.domains.traveller.schemas import CreateProfileRequest
from app.domains.traveller.service import TravellerService


def _request() -> CreateProfileRequest:
    return CreateProfileRequest(
        identity={"name": "Test Traveller", "email": "test@example.com"},
        preferences={"travel_interests": ["culture"], "budget_style": "balanced"},
        loyalty={},
    )


def test_repository_stores_typed_profiles():
    repository = TravellerRepository()
    profile = TravellerProfile(
        id="traveller-1",
        created_at="2026-07-26T10:00:00+00:00",
        updated_at="2026-07-26T10:00:00+00:00",
        identity={"name": "Test Traveller"},
        preferences={"budget_style": "balanced"},
        loyalty={},
    )

    repository.save(profile)

    assert repository.get("traveller-1") == profile
    assert repository.get("missing") is None
    assert repository.list_all() == [profile]


def test_service_preserves_public_profile_shape():
    service = TravellerService(TravellerRepository())

    created = service.create_profile(_request())
    loaded = service.get_profile(created["id"])

    assert loaded == created
    assert created["identity"]["name"] == "Test Traveller"
    assert created["preferences"]["travel_interests"] == ["culture"]
    assert created["loyalty"] == {
        "airline_programs": [],
        "hotel_programs": [],
    }
    assert created["travel_history"] == []


def test_profile_defaults_are_not_shared_between_requests():
    first = _request()
    second = CreateProfileRequest(
        identity={"name": "Second", "email": "second@example.com"}
    )

    first.preferences.travel_interests.append("food")

    assert second.preferences.travel_interests == []
    assert second.loyalty.airline_programs == []
