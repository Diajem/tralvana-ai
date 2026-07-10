from __future__ import annotations

from typing import Any

# The five budget styles every Discovery module in this codebase already
# uses as a free-text field (Flight/Accommodation/Destination Intelligence
# request payloads). Budget Intelligence is the first module to treat these
# five styles as the candidates themselves rather than a scoring input.
STYLES: list[str] = ["backpacker", "budget", "balanced", "comfort", "luxury"]

# City -> region lookup for the same 10-city catalogue used by
# ai/discovery/destinations/mock_destination_provider.py, collapsed to the
# four region buckets below (Caribbean and Middle East have no dedicated
# regional rate table yet — they fall back to "default", same as any city
# outside this list). Kept local rather than imported so this Provider has
# no cross-module dependency, matching the rest of the Discovery Layer.
_CITY_REGION: dict[str, str] = {
    "Tokyo": "Asia", "Osaka": "Asia",
    "Barcelona": "Europe", "Paris": "Europe", "London": "Europe",
    "New York": "Americas",
    "Lagos": "Africa", "Accra": "Africa",
    "Kingston": "Americas",
}

# Daily per-person USD by style x region — identical values to
# ai/intelligence/reasoning/budget_reasoner.py's _DAILY_USD so a Budget
# Intelligence option and a BudgetReasoner/BudgetEstimator estimate agree
# for the same style and region.
_DAILY_USD: dict[str, dict[str, int]] = {
    "backpacker": {"Africa": 35, "Europe": 55, "Asia": 30, "Americas": 60, "default": 40},
    "budget":     {"Africa": 60, "Europe": 90, "Asia": 55, "Americas": 80, "default": 65},
    "balanced":   {"Africa": 120, "Europe": 180, "Asia": 130, "Americas": 160, "default": 150},
    "comfort":    {"Africa": 250, "Europe": 350, "Asia": 300, "Americas": 380, "default": 300},
    "luxury":     {"Africa": 500, "Europe": 700, "Asia": 600, "Americas": 750, "default": 650},
}

# Cabin class implied by each style, and per-cabin/haul flight anchors —
# identical values to ai/intelligence/reasoning/budget_reasoner.py's
# _FLIGHT_USD and _HAUL, so a Budget Intelligence flight line and a
# BudgetReasoner estimate agree for the same style and region.
_STYLE_CABIN: dict[str, str] = {
    "backpacker": "economy", "budget": "economy", "balanced": "economy",
    "comfort": "business", "luxury": "first",
}
_FLIGHT_USD: dict[str, dict[str, int]] = {
    "economy":  {"short": 150, "medium": 450, "long": 900},
    "business": {"short": 500, "medium": 1500, "long": 4000},
    "first":    {"short": 900, "medium": 3000, "long": 8000},
}
_HAUL: dict[str, str] = {
    "Europe": "short", "Africa": "medium", "Americas": "medium",
    "Asia": "long", "default": "long",
}

# Children are assumed to cost a fraction of an adult's daily and flight
# spend — a common, simple industry approximation. Sprint 4+ can replace
# this with age-banded live pricing once a real provider is wired in.
_CHILD_COST_FACTOR = 0.75


class MockBudgetProvider:
    """
    Deterministic mock budget-tier generator — no external calls.

    Same interface a real provider would implement: search(destination,
    duration_days, adults, children) -> list[dict], one raw candidate per
    budget style. Swapping in a real pricing feed later means implementing
    this method against that API and passing the instance to
    BudgetIntelligence(provider=...) — nothing downstream changes.

    Unlike Flight/Accommodation Intelligence, destination is optional: with
    no destination (or one outside the region lookup), rates fall back to
    the "default" global-average band rather than producing no candidates —
    comparing budget styles is still a useful answer without a resolved
    destination. See docs/BUDGET_INTELLIGENCE_ENGINE.md.
    """

    def search(
        self,
        destination: str | None,
        duration_days: int = 7,
        adults: int = 1,
        children: int = 0,
    ) -> list[dict[str, Any]]:
        region = self._region(destination)
        haul = _HAUL.get(region, _HAUL["default"])

        return [
            {
                "destination": destination or "",
                "region": region,
                "budget_style": style,
                "duration_days": duration_days,
                "adults": adults,
                "children": children,
                "daily_pp_usd": _DAILY_USD[style].get(region, _DAILY_USD[style]["default"]),
                "cabin_class": _STYLE_CABIN[style],
                "flight_pp_usd": _FLIGHT_USD[_STYLE_CABIN[style]][haul],
                "haul": haul,
                "_child_cost_factor": _CHILD_COST_FACTOR,
            }
            for style in STYLES
        ]

    def styles(self) -> list[str]:
        return list(STYLES)

    def regions(self) -> list[str]:
        return sorted(_CITY_REGION.values())

    def _region(self, destination: str | None) -> str:
        if not destination:
            return "default"
        return _CITY_REGION.get(destination.strip().title(), "default")


mock_budget_provider = MockBudgetProvider()
