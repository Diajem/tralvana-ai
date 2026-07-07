from __future__ import annotations

from typing import Any

from ai.intelligence.knowledge.relationships import RelationshipType
from ai.intelligence.reasoning.base_reasoner import BaseReasoner, ReasoningResult

_MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

_CROWD_LEVEL: dict[str, str] = {
    "peak": "high", "shoulder": "moderate", "off-peak": "low",
    "festival": "high", "harmattan": "moderate", "dry": "moderate", "wet": "low",
}

_PRICE_IMPACT: dict[str, str] = {
    "peak": "premium (+30–50%)", "shoulder": "standard", "off-peak": "discounted (–20–35%)",
    "festival": "premium (+20–40%)", "harmattan": "standard", "dry": "standard", "wet": "discounted (–15–25%)",
}


class SeasonReasoner(BaseReasoner):
    """
    Reasons about the travel season at a destination for a given month.

    Sprint 1: uses TravelSeason + Weather entities from the knowledge graph.
    Sprint 3+: incorporate historical pricing data and live event calendars.
    """

    def reason(
        self,
        destination: str,
        month: int | None = None,
        traveller_profile: dict | None = None,
        **_,
    ) -> ReasoningResult:
        city, country = self._city_and_country(destination)
        if city is None:
            return self._not_found(destination, f"'{destination}' is not in the knowledge graph.")

        seasons = self._ks.get_connected_entities(city.id, "TravelSeason", RelationshipType.HAS_SEASON, "outbound")
        weather_records = self._ks.get_connected_entities(city.id, "Weather", RelationshipType.HAS_WEATHER, "outbound")

        current_season = None
        current_weather = None
        if month is not None:
            current_season = next((s for s in seasons if month in s.months), None)
            current_weather = next((w for w in weather_records if w.month == month), None)

        # Alternative season recommendation (best season for this traveller type)
        best_season = self._best_season_for(seasons, traveller_profile)

        return ReasoningResult(
            reasoner_name="SeasonReasoner",
            subject=destination,
            success=True,
            confidence=0.72,
            data={
                "destination": destination,
                "country": country.name if country else "Unknown",
                "queried_month": month,
                "queried_month_name": _MONTH_NAMES[month] if month else None,
                "current_season": self._season_dict(current_season) if current_season else None,
                "current_weather": {
                    "avg_temp_c": current_weather.avg_temp_c,
                    "condition": current_weather.condition,
                    "season_label": current_weather.season,
                } if current_weather else None,
                "crowd_level": _CROWD_LEVEL.get(current_season.season_type, "unknown") if current_season else "unknown",
                "price_impact": _PRICE_IMPACT.get(current_season.season_type, "standard") if current_season else "standard",
                "all_seasons": [self._season_dict(s) for s in seasons],
                "recommended_season": self._season_dict(best_season) if best_season else None,
                "season_recommendation": self._recommendation(best_season, traveller_profile),
            },
            assumptions=["TravelSeason definitions are static Sprint 1 data"],
            limitations=["No real-time pricing seasonality; seasons are city-level, not micro-district"],
        )

    # ------------------------------------------------------------------

    def _season_dict(self, season: Any) -> dict:
        return {
            "name": season.name,
            "type": season.season_type,
            "months": season.months,
            "month_names": [_MONTH_NAMES[m] for m in season.months],
            "characteristics": season.characteristics,
            "crowd_level": _CROWD_LEVEL.get(season.season_type, "unknown"),
            "price_impact": _PRICE_IMPACT.get(season.season_type, "standard"),
        }

    def _best_season_for(self, seasons: list, profile: dict | None) -> Any | None:
        if not seasons:
            return None
        budget_style = (profile or {}).get("preferences", {}).get("budget_style", "balanced")
        # Budget travellers → off-peak; luxury → peak; others → shoulder
        preferred_type = {"backpacker": "off-peak", "budget": "off-peak", "luxury": "peak"}.get(budget_style, "shoulder")
        return next((s for s in seasons if s.season_type == preferred_type), seasons[0])

    def _recommendation(self, season: Any, profile: dict | None) -> str:
        if season is None:
            return "No season data available."
        budget_style = (profile or {}).get("preferences", {}).get("budget_style", "balanced")
        crowd = _CROWD_LEVEL.get(season.season_type, "unknown")
        price = _PRICE_IMPACT.get(season.season_type, "standard")
        return (
            f"Based on your {budget_style} budget style, the '{season.name}' season "
            f"({', '.join(season.month_names if hasattr(season, 'month_names') else [])}) "
            f"offers {crowd} crowds and {price} pricing."
        )


season_reasoner = SeasonReasoner()
