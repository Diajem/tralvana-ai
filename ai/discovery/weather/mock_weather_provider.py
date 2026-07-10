from __future__ import annotations

from typing import Any

# Each destination is authored as a small number of season blocks (2-4),
# then expanded to all 12 months below — the same "formula, not 120
# hand-tuned entries" technique Destination Intelligence used for its
# objective scores (ADR-013) and Visa Intelligence used for its tier ×
# destination policy table (ADR-015), applied here to month expansion.
# All figures are illustrative mock climate archetypes, not a real
# forecast — see docs/WEATHER_INTELLIGENCE_ENGINE.md.
_CLIMATE_PROFILES: dict[str, list[dict[str, Any]]] = {
    "JAPAN": [
        {"months": [12, 1, 2], "season": "WINTER", "avg_temp_c": 6, "rainfall": "LOW",
         "humidity": "LOW", "daylight_hours": 9.8, "hazards": []},
        {"months": [3, 4, 5], "season": "SPRING", "avg_temp_c": 15, "rainfall": "MODERATE",
         "humidity": "MODERATE", "daylight_hours": 12.5, "hazards": []},
        {"months": [6, 7, 8], "season": "SUMMER", "avg_temp_c": 27, "rainfall": "HIGH",
         "humidity": "VERY_HIGH", "daylight_hours": 14.2, "hazards": ["extreme_heat", "typhoon"]},
        {"months": [9, 10, 11], "season": "AUTUMN", "avg_temp_c": 17, "rainfall": "MODERATE",
         "humidity": "MODERATE", "daylight_hours": 11.0, "hazards": ["typhoon"]},
    ],
    "SPAIN": [
        {"months": [12, 1, 2], "season": "WINTER", "avg_temp_c": 11, "rainfall": "MODERATE",
         "humidity": "MODERATE", "daylight_hours": 9.5, "hazards": []},
        {"months": [3, 4, 5], "season": "SPRING", "avg_temp_c": 17, "rainfall": "LOW",
         "humidity": "LOW", "daylight_hours": 12.8, "hazards": []},
        {"months": [6, 7, 8], "season": "SUMMER", "avg_temp_c": 30, "rainfall": "LOW",
         "humidity": "LOW", "daylight_hours": 14.5, "hazards": ["extreme_heat", "wildfire"]},
        {"months": [9, 10, 11], "season": "AUTUMN", "avg_temp_c": 19, "rainfall": "MODERATE",
         "humidity": "MODERATE", "daylight_hours": 10.8, "hazards": []},
    ],
    "FRANCE": [
        {"months": [12, 1, 2], "season": "WINTER", "avg_temp_c": 6, "rainfall": "MODERATE",
         "humidity": "HIGH", "daylight_hours": 8.8, "hazards": []},
        {"months": [3, 4, 5], "season": "SPRING", "avg_temp_c": 13, "rainfall": "MODERATE",
         "humidity": "MODERATE", "daylight_hours": 13.0, "hazards": []},
        {"months": [6, 7, 8], "season": "SUMMER", "avg_temp_c": 24, "rainfall": "LOW",
         "humidity": "MODERATE", "daylight_hours": 15.5, "hazards": ["extreme_heat"]},
        {"months": [9, 10, 11], "season": "AUTUMN", "avg_temp_c": 14, "rainfall": "HIGH",
         "humidity": "HIGH", "daylight_hours": 10.5, "hazards": []},
    ],
    "UK": [
        {"months": [12, 1, 2], "season": "WINTER", "avg_temp_c": 5, "rainfall": "HIGH",
         "humidity": "HIGH", "daylight_hours": 7.8, "hazards": ["flood"]},
        {"months": [3, 4, 5], "season": "SPRING", "avg_temp_c": 11, "rainfall": "MODERATE",
         "humidity": "MODERATE", "daylight_hours": 13.5, "hazards": []},
        {"months": [6, 7, 8], "season": "SUMMER", "avg_temp_c": 19, "rainfall": "MODERATE",
         "humidity": "MODERATE", "daylight_hours": 16.0, "hazards": []},
        {"months": [9, 10, 11], "season": "AUTUMN", "avg_temp_c": 12, "rainfall": "HIGH",
         "humidity": "HIGH", "daylight_hours": 10.0, "hazards": ["flood"]},
    ],
    "IRELAND": [
        {"months": [12, 1, 2], "season": "WINTER", "avg_temp_c": 6, "rainfall": "HIGH",
         "humidity": "HIGH", "daylight_hours": 7.5, "hazards": ["flood"]},
        {"months": [3, 4, 5], "season": "SPRING", "avg_temp_c": 10, "rainfall": "MODERATE",
         "humidity": "HIGH", "daylight_hours": 13.8, "hazards": []},
        {"months": [6, 7, 8], "season": "SUMMER", "avg_temp_c": 17, "rainfall": "MODERATE",
         "humidity": "HIGH", "daylight_hours": 16.5, "hazards": []},
        {"months": [9, 10, 11], "season": "AUTUMN", "avg_temp_c": 11, "rainfall": "HIGH",
         "humidity": "HIGH", "daylight_hours": 10.2, "hazards": ["flood"]},
    ],
    "USA": [
        {"months": [12, 1, 2], "season": "WINTER", "avg_temp_c": 2, "rainfall": "MODERATE",
         "humidity": "MODERATE", "daylight_hours": 9.5, "hazards": ["extreme_cold"]},
        {"months": [3, 4, 5], "season": "SPRING", "avg_temp_c": 14, "rainfall": "MODERATE",
         "humidity": "MODERATE", "daylight_hours": 12.8, "hazards": []},
        {"months": [6, 7, 8], "season": "SUMMER", "avg_temp_c": 27, "rainfall": "MODERATE",
         "humidity": "HIGH", "daylight_hours": 15.0, "hazards": ["extreme_heat", "hurricane"]},
        {"months": [9, 10, 11], "season": "AUTUMN", "avg_temp_c": 15, "rainfall": "MODERATE",
         "humidity": "MODERATE", "daylight_hours": 10.8, "hazards": ["hurricane"]},
    ],
    # Near-equatorial destinations: a wet/dry season pattern, not four
    # temperate seasons — genuine climate variety, same idea as Destination
    # Intelligence differentiating region-appropriate attributes per city.
    "NIGERIA": [
        {"months": [11, 12, 1, 2, 3], "season": "DRY_SEASON", "avg_temp_c": 28, "rainfall": "LOW",
         "humidity": "MODERATE", "daylight_hours": 12.0, "hazards": ["extreme_heat"]},
        {"months": [4, 5, 6, 7, 8, 9, 10], "season": "WET_SEASON", "avg_temp_c": 26, "rainfall": "VERY_HIGH",
         "humidity": "VERY_HIGH", "daylight_hours": 12.1, "hazards": ["flood"]},
    ],
    "GHANA": [
        {"months": [11, 12, 1, 2], "season": "DRY_SEASON", "avg_temp_c": 27, "rainfall": "LOW",
         "humidity": "LOW", "daylight_hours": 12.0, "hazards": []},
        {"months": [3, 4, 5, 6, 7, 8, 9, 10], "season": "WET_SEASON", "avg_temp_c": 26, "rainfall": "HIGH",
         "humidity": "HIGH", "daylight_hours": 12.1, "hazards": ["flood"]},
    ],
    "JAMAICA": [
        {"months": [12, 1, 2, 3, 4], "season": "DRY_SEASON", "avg_temp_c": 26, "rainfall": "LOW",
         "humidity": "MODERATE", "daylight_hours": 11.8, "hazards": []},
        {"months": [5, 6, 7, 8, 9, 10, 11], "season": "HURRICANE_SEASON", "avg_temp_c": 28, "rainfall": "HIGH",
         "humidity": "HIGH", "daylight_hours": 12.3, "hazards": ["hurricane", "flood"]},
    ],
    "UAE": [
        {"months": [11, 12, 1, 2, 3], "season": "MILD_SEASON", "avg_temp_c": 24, "rainfall": "LOW",
         "humidity": "LOW", "daylight_hours": 11.0, "hazards": []},
        {"months": [4, 5, 6, 7, 8, 9, 10], "season": "HOT_SEASON", "avg_temp_c": 38, "rainfall": "LOW",
         "humidity": "MODERATE", "daylight_hours": 13.0, "hazards": ["extreme_heat"]},
    ],
}

# Canonical key -> display name, for destinations where straight .title()
# would be wrong (acronyms) — same convention as
# ai/discovery/visa/mock_visa_provider.py's _DISPLAY_NAME.
_DISPLAY_NAME: dict[str, str] = {
    "UK": "United Kingdom", "USA": "United States", "UAE": "United Arab Emirates",
}

# Common long-form aliases -> canonical key, same convention as
# ai/discovery/visa/mock_visa_provider.py's _ALIASES.
_ALIASES: dict[str, str] = {
    "UNITED KINGDOM": "UK", "GREAT BRITAIN": "UK",
    "UNITED STATES": "USA", "UNITED STATES OF AMERICA": "USA",
    "UNITED ARAB EMIRATES": "UAE",
}


class MockWeatherProvider:
    """
    Deterministic mock climate profiles — no external calls, no OpenWeather,
    WeatherAPI, or AccuWeather. Same interface a real provider would
    implement: month(destination, month) -> dict. Swapping in a real
    climate data feed later means implementing this method against that
    API and passing the instance to WeatherIntelligence(provider=...) —
    nothing downstream changes.

    This is a travel decision engine, not a forecast — see
    docs/WEATHER_INTELLIGENCE_ENGINE.md.
    """

    def month(self, destination: str, month_of_travel: int) -> dict[str, Any]:
        key = self._normalize(destination)
        profile = _CLIMATE_PROFILES.get(key)

        if not profile:
            return {
                "destination": destination, "month_of_travel": month_of_travel,
                "matched": False, "season": "UNKNOWN", "avg_temp_c": None,
                "rainfall": "UNKNOWN", "humidity": "UNKNOWN", "daylight_hours": None,
                "hazards": [],
            }

        block = next(b for b in profile if month_of_travel in b["months"])
        return {
            "destination": self._display(key), "month_of_travel": month_of_travel,
            "matched": True, "season": block["season"], "avg_temp_c": block["avg_temp_c"],
            "rainfall": block["rainfall"], "humidity": block["humidity"],
            "daylight_hours": block["daylight_hours"], "hazards": list(block["hazards"]),
        }

    def year(self, destination: str) -> list[dict[str, Any]]:
        """All 12 months for a destination — used by the Orchestrator to
        find the best month and surface alternatives. Empty for an unknown
        destination."""
        if self._normalize(destination) not in _CLIMATE_PROFILES:
            return []
        return [self.month(destination, m) for m in range(1, 13)]

    def known_destinations(self) -> list[str]:
        return sorted(_CLIMATE_PROFILES.keys())

    def _normalize(self, destination: str) -> str:
        key = destination.strip().upper()
        return _ALIASES.get(key, key)

    def _display(self, key: str) -> str:
        return _DISPLAY_NAME.get(key, key.title())


mock_weather_provider = MockWeatherProvider()
