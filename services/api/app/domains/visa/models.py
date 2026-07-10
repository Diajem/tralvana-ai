from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class VisaStatus(str, Enum):
    VISA_NOT_REQUIRED = "VISA_NOT_REQUIRED"
    VISA_REQUIRED = "VISA_REQUIRED"
    ETA_REQUIRED = "ETA_REQUIRED"
    EVISA_AVAILABLE = "EVISA_AVAILABLE"
    CHECK_MANUALLY = "CHECK_MANUALLY"
    ENTRY_RESTRICTED = "ENTRY_RESTRICTED"


class TravelPurpose(str, Enum):
    TOURISM = "TOURISM"
    BUSINESS = "BUSINESS"
    TRANSIT = "TRANSIT"
    STUDY = "STUDY"
    WORK = "WORK"
    FAMILY_VISIT = "FAMILY_VISIT"
    OTHER = "OTHER"


@dataclass
class VisaAssessment:
    visa_assessment_id: str
    traveller_id: str | None
    trip_id: str | None
    nationality: str
    passport_country: str
    destination_country: str
    transit_countries: list[str]
    travel_purpose: str
    intended_length_of_stay: int
    passport_expiry_date: str | None
    passport_validity_months: float | None
    visa_status: str
    visa_required: bool
    visa_type: str
    entry_requirements: list[str]
    supporting_documents: list[str]
    vaccination_requirements: list[str]
    travel_authorisation_required: bool
    processing_time: str
    confidence: float
    risks: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    recommendation: str = ""
    explanation: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "visa_assessment_id": self.visa_assessment_id,
            "traveller_id": self.traveller_id,
            "trip_id": self.trip_id,
            "nationality": self.nationality,
            "passport_country": self.passport_country,
            "destination_country": self.destination_country,
            "transit_countries": self.transit_countries,
            "travel_purpose": self.travel_purpose,
            "intended_length_of_stay": self.intended_length_of_stay,
            "passport_expiry_date": self.passport_expiry_date,
            "passport_validity_months": self.passport_validity_months,
            "visa_status": self.visa_status,
            "visa_required": self.visa_required,
            "visa_type": self.visa_type,
            "entry_requirements": self.entry_requirements,
            "supporting_documents": self.supporting_documents,
            "vaccination_requirements": self.vaccination_requirements,
            "travel_authorisation_required": self.travel_authorisation_required,
            "processing_time": self.processing_time,
            "confidence": self.confidence,
            "risks": self.risks,
            "assumptions": self.assumptions,
            "recommendation": self.recommendation,
            "explanation": self.explanation,
            "created_at": self.created_at,
        }
