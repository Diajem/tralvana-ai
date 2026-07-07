from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from knowledge.graph.knowledge_graph import KnowledgeGraph

# Static budget estimates per budget_style and destination region.
# Sprint 2+: replace with live pricing data or ML cost models.
_DAILY_COST_USD: dict[str, dict[str, int]] = {
    "backpacker": {
        "Africa":  35,
        "Europe":  55,
        "Asia":    30,
        "Americas":60,
        "default": 40,
    },
    "budget": {
        "Africa":  60,
        "Europe":  90,
        "Asia":    55,
        "Americas":80,
        "default": 65,
    },
    "balanced": {
        "Africa":  120,
        "Europe":  180,
        "Asia":    130,
        "Americas":160,
        "default": 150,
    },
    "comfort": {
        "Africa":  250,
        "Europe":  350,
        "Asia":    300,
        "Americas":380,
        "default": 300,
    },
    "luxury": {
        "Africa":  500,
        "Europe":  700,
        "Asia":    600,
        "Americas":750,
        "default": 650,
    },
}

_FLIGHT_COST_USD: dict[str, dict[str, int]] = {
    "economy":  {"short-haul": 150, "medium-haul": 450, "long-haul": 900},
    "business": {"short-haul": 500, "medium-haul": 1500, "long-haul": 4000},
    "first":    {"short-haul": 900, "medium-haul": 3000, "long-haul": 8000},
}


class BudgetReasoner:
    """
    Estimates trip budget based on destination, duration, and traveller preferences.

    Sprint 1: static regional estimates.
    Sprint 3+: connect to live pricing APIs and learned cost models.
    """

    def __init__(self, graph: KnowledgeGraph | None = None) -> None:
        if graph is None:
            from knowledge import knowledge_graph
            self._graph = knowledge_graph
        else:
            self._graph = graph

    def reason(
        self,
        destination: str,
        duration_days: int = 7,
        traveller_profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prefs = (traveller_profile or {}).get("preferences", {})
        budget_style = prefs.get("budget_style", "balanced")
        cabin_class = prefs.get("cabin_class", "economy")

        continent = self._continent_for(destination)
        daily = _DAILY_COST_USD.get(budget_style, _DAILY_COST_USD["balanced"])
        daily_usd = daily.get(continent, daily["default"])
        accommodation_usd = daily_usd * 0.45
        food_usd = daily_usd * 0.25
        activities_usd = daily_usd * 0.20
        misc_usd = daily_usd * 0.10

        haul = self._haul_for(continent)
        flight_costs = _FLIGHT_COST_USD.get(cabin_class, _FLIGHT_COST_USD["economy"])
        flight_usd = flight_costs[haul]

        total_usd = (daily_usd * duration_days) + flight_usd

        return {
            "destination": destination,
            "duration_days": duration_days,
            "budget_style": budget_style,
            "cabin_class": cabin_class,
            "continent": continent,
            "daily_estimate_usd": daily_usd,
            "daily_breakdown_usd": {
                "accommodation": round(accommodation_usd),
                "food": round(food_usd),
                "activities": round(activities_usd),
                "miscellaneous": round(misc_usd),
            },
            "flight_estimate_usd": flight_usd,
            "flight_type": haul,
            "total_estimate_usd": round(total_usd),
            "total_estimate_range_usd": {
                "low": round(total_usd * 0.85),
                "high": round(total_usd * 1.20),
            },
            "currency_note": (
                "Estimates are in USD. Convert to local currency before booking."
            ),
            "confidence": "medium",
            "reasoning_source": "knowledge_graph_v1_static_estimates",
        }

    # ------------------------------------------------------------------

    def _continent_for(self, destination: str) -> str:
        city = self._graph.find_node_by_name("City", destination)
        if city:
            country = self._graph.get_node(city.country_id)
            if country:
                return country.continent
        return "default"

    def _haul_for(self, continent: str) -> str:
        # Rough heuristic from a "UK/Western" home base perspective.
        # Sprint 2+: use traveller's home_airport to compute actual route distance.
        if continent in ("Europe",):
            return "short-haul"
        if continent in ("Africa", "Americas"):
            return "medium-haul"
        return "long-haul"


budget_reasoner = BudgetReasoner()
