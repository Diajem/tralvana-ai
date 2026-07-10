from __future__ import annotations

from app.domains.weather.models import WeatherAssessment


class WeatherRepository:
    """In-memory store. Replace with a PostgreSQL adapter in Sprint 3."""

    def __init__(self) -> None:
        self._store: dict[str, WeatherAssessment] = {}

    def save(self, assessment: WeatherAssessment) -> WeatherAssessment:
        self._store[assessment.weather_assessment_id] = assessment
        return assessment

    def get(self, weather_assessment_id: str) -> WeatherAssessment | None:
        return self._store.get(weather_assessment_id)

    def list_by_trip(self, trip_id: str) -> list[WeatherAssessment]:
        return [a for a in self._store.values() if a.trip_id == trip_id]
