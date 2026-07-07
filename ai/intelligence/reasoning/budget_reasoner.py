from __future__ import annotations

from typing import Any

from ai.intelligence.reasoning.base_reasoner import BaseReasoner, ReasoningResult

_DAILY_USD: dict[str, dict[str, int]] = {
    "backpacker": {"Africa": 35, "Europe": 55, "Asia": 30, "Americas": 60, "default": 40},
    "budget":     {"Africa": 60, "Europe": 90, "Asia": 55, "Americas": 80, "default": 65},
    "balanced":   {"Africa":120, "Europe":180, "Asia":130, "Americas":160, "default":150},
    "comfort":    {"Africa":250, "Europe":350, "Asia":300, "Americas":380, "default":300},
    "luxury":     {"Africa":500, "Europe":700, "Asia":600, "Americas":750, "default":650},
}

_FLIGHT_USD: dict[str, dict[str, int]] = {
    "economy":  {"short": 150, "medium": 450, "long": 900},
    "business": {"short": 500, "medium":1500, "long":4000},
    "first":    {"short": 900, "medium":3000, "long":8000},
}

_HAUL: dict[str, str] = {
    "Europe": "short", "Africa": "medium", "Americas": "medium",
    "Asia": "long", "default": "long",
}


class BudgetReasoner(BaseReasoner):
    """
    Estimates total trip cost by budget style, destination continent, and duration.

    Sprint 1: static regional rate tables.
    Sprint 3+: live flight/hotel pricing via travel data feeds.
    """

    def reason(
        self,
        destination: str,
        duration_days: int = 7,
        traveller_profile: dict | None = None,
        **_,
    ) -> ReasoningResult:
        city, country = self._city_and_country(destination)
        if city is None:
            return self._not_found(destination, f"'{destination}' is not in the knowledge graph.")

        prefs = (traveller_profile or {}).get("preferences", {})
        budget_style = prefs.get("budget_style", "balanced")
        cabin = prefs.get("cabin_class", "economy")
        continent = country.continent if country else "default"

        daily_table = _DAILY_USD.get(budget_style, _DAILY_USD["balanced"])
        daily = daily_table.get(continent, daily_table["default"])
        haul = _HAUL.get(continent, _HAUL["default"])
        flight = _FLIGHT_USD.get(cabin, _FLIGHT_USD["economy"])[haul]
        total = daily * duration_days + flight

        return ReasoningResult(
            reasoner_name="BudgetReasoner",
            subject=destination,
            success=True,
            confidence=0.60,
            data={
                "destination": destination,
                "country": country.name if country else "Unknown",
                "continent": continent,
                "duration_days": duration_days,
                "budget_style": budget_style,
                "cabin_class": cabin,
                "daily_estimate_usd": daily,
                "daily_breakdown_usd": {
                    "accommodation": round(daily * 0.45),
                    "food":          round(daily * 0.25),
                    "activities":    round(daily * 0.20),
                    "miscellaneous": round(daily * 0.10),
                },
                "flight_estimate_usd": flight,
                "flight_type": f"{haul}-haul",
                "total_estimate_usd": round(total),
                "total_range_usd": {"low": round(total * 0.85), "high": round(total * 1.20)},
                "currency_note": "Estimates in USD. Convert to local currency before booking.",
            },
            assumptions=["Static regional daily rates used — no live pricing"],
            limitations=["No exchange rate conversion; haul calculation uses generic continent mapping"],
        )


budget_reasoner = BudgetReasoner()
