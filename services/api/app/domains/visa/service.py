from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.domains.visa.models import VisaAssessment
from app.domains.visa.repository import VisaRepository
from app.domains.visa.schemas import CheckVisaRequest


class VisaIntelligenceService:
    """
    Orchestrates a visa assessment from a request, an optional Trip Plan,
    and an optional traveller profile (for a default passport country).

    Sprint 1: deterministic mock rules via ai/discovery/visa/. Sprint 4+:
    swap MockVisaProvider for a real immigration data feed.
    """

    def __init__(self, repository: VisaRepository) -> None:
        self._repo = repository

    def check(
        self,
        request: CheckVisaRequest,
        trip: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from ai.discovery.visa.visa_intelligence import visa_intelligence

        destination_country = request.destination_country
        if trip:
            destination_country = destination_country or trip.get("destination")

        output = visa_intelligence.check(
            passport_country=request.passport_country,
            destination_country=destination_country,
            nationality=request.nationality,
            transit_countries=request.transit_countries,
            travel_purpose=request.travel_purpose,
            intended_length_of_stay=request.intended_length_of_stay,
            passport_expiry_date=request.passport_expiry_date,
        )

        now = datetime.now(timezone.utc).isoformat()
        assessment = VisaAssessment(
            visa_assessment_id=str(uuid.uuid4()),
            traveller_id=request.traveller_id,
            trip_id=request.trip_id,
            nationality=output["nationality"],
            passport_country=output["passport_country"],
            destination_country=output["destination_country"],
            transit_countries=output["transit_countries"],
            travel_purpose=output["travel_purpose"],
            intended_length_of_stay=output["intended_length_of_stay"],
            passport_expiry_date=output["passport_expiry_date"],
            passport_validity_months=output["passport_validity_months"],
            visa_status=output["visa_status"],
            visa_required=output["visa_required"],
            visa_type=output["visa_type"],
            entry_requirements=output["entry_requirements"],
            supporting_documents=output["supporting_documents"],
            vaccination_requirements=output["vaccination_requirements"],
            travel_authorisation_required=output["travel_authorisation_required"],
            processing_time=output["processing_time"],
            confidence=output["confidence"],
            risks=output["risks"],
            assumptions=output["assumptions"],
            recommendation=output["recommendation"],
            explanation=output["explanation"],
            created_at=now,
        )
        self._repo.save(assessment)
        return assessment.to_dict()

    def get(self, visa_assessment_id: str) -> dict[str, Any] | None:
        assessment = self._repo.get(visa_assessment_id)
        return assessment.to_dict() if assessment else None

    def list_by_trip(self, trip_id: str) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self._repo.list_by_trip(trip_id)]

    def check_from_conversation(
        self,
        traveller_id: str | None,
        trip_id: str | None,
        entities: dict[str, str],
        profile: dict[str, Any] | None,
    ) -> dict[str, Any]:
        trip: dict[str, Any] | None = None
        if trip_id:
            try:
                from app.domains.trips.service import trip_planning_service
                trip = trip_planning_service.get(trip_id)
            except Exception:
                pass

        passport_country = entities.get("nationality") or self._profile_passport_country(profile)

        request = CheckVisaRequest(
            traveller_id=traveller_id,
            trip_id=trip_id,
            nationality=entities.get("nationality"),
            passport_country=passport_country or "",
            destination_country=entities.get("destination") or (trip or {}).get("destination") or "",
        )
        return self.check(request, trip=trip)

    def _profile_passport_country(self, profile: dict[str, Any] | None) -> str | None:
        if not profile:
            return None
        documents = profile.get("documents", {})
        if documents.get("passport_country"):
            return documents["passport_country"]
        return profile.get("identity", {}).get("nationality")


_repository = VisaRepository()
visa_intelligence_service = VisaIntelligenceService(_repository)
