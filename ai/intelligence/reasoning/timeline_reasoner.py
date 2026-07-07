from __future__ import annotations

from typing import Any

from ai.intelligence.knowledge.relationships import RelationshipType
from ai.intelligence.reasoning.base_reasoner import BaseReasoner, ReasoningResult

_MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

_APPEAL: dict[str, int] = {
    "sunny": 5, "mild": 4, "partly-cloudy": 3, "hot": 3,
    "humid": 2, "cloudy": 2, "rainy": 1, "cold": 1, "snowy": 2, "harmattan": 2,
}


class TimelineReasoner(BaseReasoner):
    """
    Advises on when to visit a destination and what to expect in a given month.

    Sprint 1: derives best months from weather scores and event presence.
    Sprint 3+: incorporate crowd data, flight price seasonality, school holiday calendars.
    """

    def reason(
        self,
        destination: str,
        travel_month: int | None = None,
        duration_days: int = 7,
        traveller_profile: dict | None = None,
        **_,
    ) -> ReasoningResult:
        city, _ = self._city_and_country(destination)
        if city is None:
            return self._not_found(destination, f"'{destination}' is not in the knowledge graph.")

        weather_records = self._ks.get_connected_entities(city.id, "Weather", RelationshipType.HAS_WEATHER, "outbound")
        events = self._ks.get_connected_entities(city.id, "Event", RelationshipType.PART_OF, "inbound")
        seasons = self._ks.get_connected_entities(city.id, "TravelSeason", RelationshipType.HAS_SEASON, "outbound")

        event_months: set[int] = {e.month for e in events if e.month}
        best_months = self._best_months(weather_records, event_months)
        avoid = self._months_to_avoid(weather_records, traveller_profile)
        snapshot = self._month_snapshot(travel_month, weather_records, events, seasons) if travel_month else None

        return ReasoningResult(
            reasoner_name="TimelineReasoner",
            subject=destination,
            success=True,
            confidence=0.70,
            data={
                "destination": destination,
                "best_months": best_months,
                "months_to_avoid": avoid,
                "travel_month_snapshot": snapshot,
                "events_calendar": sorted(
                    [{"name": e.name, "type": e.event_type, "month": e.month, "month_name": _MONTH_NAMES[e.month or 0]} for e in events],
                    key=lambda x: x["month"] or 0,
                ),
                "planning_tips": self._tips(destination, duration_days),
            },
            assumptions=["Weather data from Sprint 1 static profiles"],
            limitations=["No live crowd or pricing seasonality data"],
        )

    # ------------------------------------------------------------------

    def _best_months(self, weather_records: list, event_months: set[int]) -> list[dict]:
        scored = [
            (w.month, _APPEAL.get(w.condition, 2) + (1 if w.month in event_months else 0))
            for w in weather_records
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            {"month": m, "month_name": _MONTH_NAMES[m], "score": s, "has_events": m in event_months}
            for m, s in scored[:3]
        ]

    def _months_to_avoid(self, weather_records: list, profile: dict | None) -> list[dict]:
        interests = (profile or {}).get("preferences", {}).get("travel_interests", [])
        avoid = []
        for w in weather_records:
            if w.condition == "rainy" and "nature" in interests:
                avoid.append({"month": w.month, "month_name": _MONTH_NAMES[w.month], "reason": "Rainy season limits outdoor activities."})
            elif w.condition == "hot" and w.avg_temp_c > 38:
                avoid.append({"month": w.month, "month_name": _MONTH_NAMES[w.month], "reason": f"Extreme heat ({w.avg_temp_c}°C)."})
        return avoid

    def _month_snapshot(self, month: int, weather_records: list, events: list, seasons: list) -> dict:
        weather = next((w for w in weather_records if w.month == month), None)
        month_events = [e for e in events if e.month == month]
        season = next((s for s in seasons if month in s.months), None)
        return {
            "month": month,
            "month_name": _MONTH_NAMES[month],
            "weather": {
                "avg_temp_c": weather.avg_temp_c if weather else None,
                "condition": weather.condition if weather else "no data",
                "season": weather.season if weather else "unknown",
            },
            "travel_season": {
                "name": season.name if season else "Unknown",
                "type": season.season_type if season else "unknown",
                "characteristics": season.characteristics if season else [],
            },
            "events": [{"name": e.name, "type": e.event_type} for e in month_events],
            "advice": self._weather_advice(weather),
        }

    def _weather_advice(self, w: Any) -> str:
        if w is None:
            return "No weather data available for this month."
        if w.condition in ("hot", "humid") and w.avg_temp_c > 35:
            return "Very hot — pack light breathable clothing and stay hydrated."
        if w.condition == "rainy":
            return "Rainy season — bring waterproofs; expect some indoor days."
        if w.condition in ("cold", "snowy") and w.avg_temp_c < 5:
            return "Cold — pack warm layers and check winter closures."
        if w.condition in ("sunny", "mild"):
            return "Excellent conditions — ideal for sightseeing and outdoor activities."
        return "Comfortable conditions — standard packing applies."

    def _tips(self, destination: str, days: int) -> list[str]:
        return [
            f"Book accommodation at least 6 weeks in advance for {destination}.",
            f"A {days}-day trip allows time for 2–3 day excursions outside the city centre.",
            "Check and apply for any required visas well in advance — processing can take 4–8 weeks.",
            "Purchase comprehensive travel insurance before departure.",
        ]


timeline_reasoner = TimelineReasoner()
