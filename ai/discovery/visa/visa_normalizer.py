from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

_VISA_REQUIRED_STATUSES = {"VISA_REQUIRED", "ENTRY_RESTRICTED"}
_TRAVEL_AUTH_STATUSES = {"ETA_REQUIRED", "EVISA_AVAILABLE"}

_BASE_ENTRY_REQUIREMENTS = [
    "Valid passport",
    "Proof of onward or return travel",
    "Proof of sufficient funds for the trip",
]
_BASE_SUPPORTING_DOCUMENTS = ["Passport", "Travel insurance"]


class VisaNormalizer:
    """
    Converts a raw MockVisaProvider record (plus the trip-shape facts that
    accompany it) into the canonical internal schema, and computes the
    objective (preference-independent) fields every downstream stage relies
    on: passport_validity_months, entry_requirements, supporting_documents,
    visa_required, travel_authorisation_required, and — unlike the other
    three Discovery modules — transit_status, a list of transit-country
    lookups the Orchestrator has already resolved via the same Provider.
    These are properties of the assessment itself, not of any traveller
    preference. See docs/DISCOVERY_LAYER_PATTERN.md.
    """

    def normalize(
        self,
        raw: dict[str, Any],
        nationality: str,
        transit_countries: list[str],
        transit_status: list[dict[str, Any]],
        travel_purpose: str,
        intended_length_of_stay: int,
        passport_expiry_date: str | None,
    ) -> dict[str, Any]:
        status = raw["status"]
        passport_validity_months = self._validity_months(passport_expiry_date)

        return {
            "nationality": nationality,
            "passport_country": raw["passport_country"],
            "destination_country": raw["destination_country"],
            "transit_countries": list(transit_countries),
            "transit_status": transit_status,
            "travel_purpose": travel_purpose.upper(),
            "intended_length_of_stay": intended_length_of_stay,
            "passport_expiry_date": passport_expiry_date,
            "passport_validity_months": passport_validity_months,
            "visa_status": status,
            "visa_required": status in _VISA_REQUIRED_STATUSES,
            "travel_authorisation_required": status in _TRAVEL_AUTH_STATUSES,
            "visa_type": raw["visa_type"],
            "max_stay_days": raw["max_stay_days"],
            "processing_time": raw["processing_time"],
            "entry_requirements": self._entry_requirements(status),
            "supporting_documents": self._supporting_documents(status),
            "vaccination_requirements": raw["vaccination_requirements"],
            "matched_type": raw["matched_type"],
        }

    # ------------------------------------------------------------------

    def _validity_months(self, passport_expiry_date: str | None) -> float | None:
        if not passport_expiry_date:
            return None
        try:
            expiry = date.fromisoformat(passport_expiry_date)
        except ValueError:
            return None
        today = datetime.now(timezone.utc).date()
        days_remaining = (expiry - today).days
        return round(max(days_remaining, 0) / 30.44, 1)

    def _entry_requirements(self, status: str) -> list[str]:
        requirements = list(_BASE_ENTRY_REQUIREMENTS)
        if status in _VISA_REQUIRED_STATUSES:
            requirements.append("A valid visa issued before travel")
        elif status in _TRAVEL_AUTH_STATUSES:
            requirements.append("An approved travel authorisation (ETA/e-Visa) before travel")
        elif status == "CHECK_MANUALLY":
            requirements.append("Requirements not determined — contact the destination's embassy or consulate")
        return requirements

    def _supporting_documents(self, status: str) -> list[str]:
        documents = list(_BASE_SUPPORTING_DOCUMENTS)
        if status in _VISA_REQUIRED_STATUSES:
            documents.append("Visa approval / visa sticker")
        elif status in _TRAVEL_AUTH_STATUSES:
            documents.append("ETA / e-Visa confirmation")
        return documents


visa_normalizer = VisaNormalizer()
