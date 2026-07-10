from __future__ import annotations

from pydantic import BaseModel, Field


class CheckVisaRequest(BaseModel):
    traveller_id: str | None = None
    trip_id: str | None = None
    nationality: str | None = None          # defaults to passport_country if omitted
    passport_country: str
    destination_country: str
    transit_countries: list[str] = []
    travel_purpose: str = "TOURISM"          # TOURISM | BUSINESS | TRANSIT | STUDY | WORK | FAMILY_VISIT | OTHER
    intended_length_of_stay: int = Field(default=14, ge=1, le=365)
    passport_expiry_date: str | None = None  # ISO date, e.g. "2027-06-01"


class VisaAssessmentResponse(BaseModel):
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
    risks: list[str]
    assumptions: list[str]
    recommendation: str
    explanation: str
    created_at: str
