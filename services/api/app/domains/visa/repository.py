from __future__ import annotations

from app.domains.visa.models import VisaAssessment


class VisaRepository:
    """In-memory store. Replace with a PostgreSQL adapter in Sprint 3."""

    def __init__(self) -> None:
        self._store: dict[str, VisaAssessment] = {}

    def save(self, assessment: VisaAssessment) -> VisaAssessment:
        self._store[assessment.visa_assessment_id] = assessment
        return assessment

    def get(self, visa_assessment_id: str) -> VisaAssessment | None:
        return self._store.get(visa_assessment_id)

    def list_by_trip(self, trip_id: str) -> list[VisaAssessment]:
        return [a for a in self._store.values() if a.trip_id == trip_id]
