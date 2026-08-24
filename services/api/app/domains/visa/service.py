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
        output = self._apply_schengen_residency_document(
            output,
            residency_document=request.residency_document,
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

        nationalities = list(
            dict.fromkeys(
                value.strip()
                for value in (
                    entities.get("nationalities")
                    or entities.get("nationality")
                    or self._profile_passport_country(profile)
                    or ""
                ).split(",")
                if value.strip()
            )
        )
        if not nationalities:
            nationalities = [""]

        assessments: list[dict[str, Any]] = []
        residency_documents = [
            value.strip()
            for value in entities.get("residency_documents", "").split(",")
            if value.strip()
        ]
        for nationality in nationalities:
            residency_document = next(
                (
                    detail
                    for detail in residency_documents
                    if detail.split(":", 1)[0].strip().casefold()
                    == nationality.casefold()
                ),
                None,
            )
            request = CheckVisaRequest(
                traveller_id=traveller_id,
                trip_id=trip_id,
                nationality=nationality or None,
                passport_country=nationality,
                destination_country=(
                    entities.get("destination")
                    or (trip or {}).get("destination")
                    or ""
                ),
                intended_length_of_stay=int(
                    entities.get("duration_days")
                    or (trip or {}).get("duration_days")
                    or 14
                ),
                residency_document=residency_document,
            )
            assessments.append(self.check(request, trip=trip))

        primary = dict(assessments[0])
        primary["individual_assessments"] = assessments
        return primary

    @staticmethod
    def _apply_schengen_residency_document(
        output: dict[str, Any],
        *,
        residency_document: str | None,
    ) -> dict[str, Any]:
        """Apply the 90/180 Schengen mobility rule to a stated document.

        This does not assume that residence alone creates an exemption. The
        interpreter must preserve an explicit long-stay visa or residence
        permit issued by a Schengen country, and the traveller must still
        verify that it remains valid for the journey.
        """
        if not residency_document:
            return output
        document = residency_document.casefold()
        destination = str(output.get("destination_country") or "").casefold()
        is_schengen_destination = destination in {"france", "spain", "italy"}
        has_qualifying_document = (
            any(
                term in document
                for term in (
                    "long-term visa", "long term visa", "long-stay visa",
                    "long stay visa", "residence permit",
                )
            )
            and any(term in document for term in ("italy", "italian", "spain", "spanish", "france", "french", "poland", "polish", "germany", "german"))
        )
        if not is_schengen_destination or not has_qualifying_document:
            return output
        updated = dict(output)
        updated.update({
            "visa_status": "VISA_NOT_REQUIRED",
            "visa_required": False,
            "travel_authorisation_required": False,
            "visa_type": "No separate short-stay visa (valid Schengen long-stay visa/residence permit)",
            "max_stay_days": 90,
            "processing_time": "Not applicable",
            "confidence": max(float(output.get("confidence") or 0), 0.85),
            "recommendation": (
                "Carry the valid passport and original Schengen long-stay visa or residence permit; "
                "confirm document validity and compliance with the 90-days-in-180 rule before travel."
            ),
        })
        updated["entry_requirements"] = list(dict.fromkeys([
            *output.get("entry_requirements", []),
            "Valid Schengen long-stay visa or residence permit issued by another Schengen country",
            "Compliance with the 90-days-in-180 short-stay limit",
        ]))
        updated["supporting_documents"] = list(dict.fromkeys([
            *output.get("supporting_documents", []),
            "Original valid long-stay visa or residence permit",
        ]))
        updated["assumptions"] = list(dict.fromkeys([
            *output.get("assumptions", []),
            f"Traveller stated this immigration status: {residency_document}.",
        ]))
        updated["risks"] = list(dict.fromkeys([
            *output.get("risks", []),
            "The exemption depends on the stated long-stay visa or residence permit being valid for the full journey.",
        ]))
        updated["explanation"] = (
            "A valid long-stay visa or residence permit issued by a Schengen country normally permits "
            "short travel to another Schengen country for up to 90 days in any 180-day period. "
            "Document validity and prior Schengen stays still need official verification."
        )
        return updated

    def _profile_passport_country(self, profile: dict[str, Any] | None) -> str | None:
        if not profile:
            return None
        documents = profile.get("documents", {})
        if documents.get("passport_country"):
            return documents["passport_country"]
        return profile.get("identity", {}).get("nationality")


_repository = VisaRepository()
visa_intelligence_service = VisaIntelligenceService(_repository)
