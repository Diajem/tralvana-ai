"""Canonical estimated-cost inputs shared by every budget path.

The values remain deterministic regional estimates, not live prices. Keeping
them in one module prevents the legacy trip estimator, Budget Intelligence,
and portfolio optimiser from drifting apart.
"""

from __future__ import annotations

STYLES: tuple[str, ...] = (
    "backpacker",
    "budget",
    "balanced",
    "comfort",
    "luxury",
)

CITY_REGION: dict[str, str] = {
    "Tokyo": "Asia",
    "Osaka": "Asia",
    "Barcelona": "Europe",
    "Paris": "Europe",
    "London": "Europe",
    "New York": "Americas",
    "Lagos": "Africa",
    "Accra": "Africa",
    "Kingston": "Americas",
}

DAILY_USD: dict[str, dict[str, int]] = {
    "backpacker": {
        "Africa": 35,
        "Europe": 55,
        "Asia": 30,
        "Americas": 60,
        "default": 40,
    },
    "budget": {
        "Africa": 60,
        "Europe": 90,
        "Asia": 55,
        "Americas": 80,
        "default": 65,
    },
    "balanced": {
        "Africa": 120,
        "Europe": 180,
        "Asia": 130,
        "Americas": 160,
        "default": 150,
    },
    "comfort": {
        "Africa": 250,
        "Europe": 350,
        "Asia": 300,
        "Americas": 380,
        "default": 300,
    },
    "luxury": {
        "Africa": 500,
        "Europe": 700,
        "Asia": 600,
        "Americas": 750,
        "default": 650,
    },
}

STYLE_CABIN: dict[str, str] = {
    "backpacker": "economy",
    "budget": "economy",
    "balanced": "economy",
    "comfort": "business",
    "luxury": "first",
}

FLIGHT_USD: dict[str, dict[str, int]] = {
    "economy": {"short": 150, "medium": 450, "long": 900},
    "business": {"short": 500, "medium": 1500, "long": 4000},
    "first": {"short": 900, "medium": 3000, "long": 8000},
}

HAUL: dict[str, str] = {
    "Europe": "short",
    "Africa": "medium",
    "Americas": "medium",
    "Asia": "long",
    "default": "long",
}

CHILD_COST_FACTOR = 0.75


def resolve_region(destination: str | None) -> str:
    if not destination:
        return "default"
    return CITY_REGION.get(destination.strip().title(), "default")


def daily_rate_usd(style: str, region: str) -> int:
    safe_style = style if style in DAILY_USD else "balanced"
    table = DAILY_USD[safe_style]
    return table.get(region, table["default"])


def flight_rate_usd(cabin_class: str, region: str) -> int:
    safe_cabin = cabin_class if cabin_class in FLIGHT_USD else "economy"
    haul = HAUL.get(region, HAUL["default"])
    return FLIGHT_USD[safe_cabin][haul]


def raw_budget_candidate(
    *,
    destination: str | None,
    budget_style: str,
    duration_days: int,
    adults: int,
    children: int,
    cabin_class: str | None = None,
) -> dict:
    """Return the provider-shaped record consumed by BudgetNormalizer."""
    safe_style = budget_style if budget_style in STYLES else "balanced"
    region = resolve_region(destination)
    cabin = cabin_class or STYLE_CABIN[safe_style]
    return {
        "destination": destination or "",
        "region": region,
        "budget_style": safe_style,
        "duration_days": duration_days,
        "adults": adults,
        "children": children,
        "daily_pp_usd": daily_rate_usd(safe_style, region),
        "cabin_class": cabin,
        "flight_pp_usd": flight_rate_usd(cabin, region),
        "haul": HAUL.get(region, HAUL["default"]),
        "_child_cost_factor": CHILD_COST_FACTOR,
    }
