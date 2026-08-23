"""Traveller profile application service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.domains.traveller.models import TravellerProfile
from app.domains.traveller.repository import TravellerRepository, build_traveller_repository
from app.domains.traveller.schemas import CreateProfileRequest


class TravellerService:
    """Create and retrieve Traveller profiles."""

    def __init__(self, repository: TravellerRepository) -> None:
        self._repository = repository

    def create_profile(
        self,
        request: CreateProfileRequest,
        *,
        traveller_id: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        profile = TravellerProfile(
            id=traveller_id or str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            identity=request.identity.model_dump(),
            preferences=request.preferences.model_dump(),
            loyalty=request.loyalty.model_dump(),
        )
        return self._repository.save(profile).to_dict()

    def get_profile(self, traveller_id: str) -> dict[str, Any] | None:
        profile = self._repository.get(traveller_id)
        return profile.to_dict() if profile else None

    def list_profiles(self) -> list[dict[str, Any]]:
        return [profile.to_dict() for profile in self._repository.list_all()]


traveller_service = TravellerService(build_traveller_repository())
