import uuid
from datetime import datetime, timezone
from typing import Any

from app.models.traveller import CreateProfileRequest


class TravellerRepository:
    """In-memory store. Replaced by a DB adapter in Sprint 2."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def save(self, profile: dict[str, Any]) -> dict[str, Any]:
        self._store[profile["id"]] = profile
        return profile

    def get(self, traveller_id: str) -> dict[str, Any] | None:
        return self._store.get(traveller_id)

    def list_all(self) -> list[dict[str, Any]]:
        return list(self._store.values())


class TravellerService:
    def __init__(self, repository: TravellerRepository) -> None:
        self._repo = repository

    def create_profile(self, request: CreateProfileRequest) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        profile: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "created_at": now,
            "updated_at": now,
            "identity": request.identity.model_dump(),
            "preferences": request.preferences.model_dump(),
            "loyalty": request.loyalty.model_dump(),
            "travel_history": [],
        }
        return self._repo.save(profile)

    def get_profile(self, traveller_id: str) -> dict[str, Any] | None:
        return self._repo.get(traveller_id)

    def list_profiles(self) -> list[dict[str, Any]]:
        return self._repo.list_all()
