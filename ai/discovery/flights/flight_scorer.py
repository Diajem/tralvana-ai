from __future__ import annotations

from typing import Any

# Dimension weights — must sum to 1.0. Kept explicit so scoring stays explainable:
# every dimension's contribution can be read straight off SCORE_WEIGHTS.
SCORE_WEIGHTS: dict[str, float] = {
    "price_fit": 0.25,
    "cabin_match": 0.15,
    "airline_preference": 0.10,
    "layover_tolerance": 0.15,
    "baggage_fit": 0.10,
    "time_of_day_fit": 0.10,
    "duration_fit": 0.15,
}

_CABIN_ORDER = ["economy", "business", "first"]


class FlightScorer:
    """
    Deterministic 0.0-1.0 match scoring for a single mock flight option.

    Every sub-score is a simple, explainable formula over traveller
    preferences (budget, cabin, airline, layover tolerance, baggage needs,
    time of day, trip duration) plus optional Traveller DNA traits and goal
    type. No randomness, no ML model — Sprint 1 rule-based scoring so every
    number can be traced back to a reason (see FlightReasoner).
    """

    def score(
        self,
        flight: dict[str, Any],
        preferences: dict[str, Any],
        dna: dict[str, Any] | None = None,
        goal_type: str | None = None,
        trip_duration_days: int = 7,
    ) -> dict[str, Any]:
        breakdown = {
            "price_fit": self._price_fit(flight, preferences),
            "cabin_match": self._cabin_match(flight, preferences),
            "airline_preference": self._airline_preference(flight, preferences),
            "layover_tolerance": self._layover_tolerance(flight, preferences),
            "baggage_fit": self._baggage_fit(flight, preferences, trip_duration_days),
            "time_of_day_fit": self._time_of_day_fit(flight, preferences),
            "duration_fit": self._duration_fit(flight, trip_duration_days),
        }

        base_score = sum(breakdown[k] * SCORE_WEIGHTS[k] for k in SCORE_WEIGHTS)
        adjustment, dna_notes = self._dna_and_goal_adjustment(flight, dna, goal_type)
        match_score = round(min(max(base_score + adjustment, 0.0), 1.0), 2)

        persona_scores = self._persona_scores(flight, breakdown)

        return {
            "match_score": match_score,
            "breakdown": breakdown,
            "adjustment": round(adjustment, 2),
            "dna_notes": dna_notes,
            "persona_scores": persona_scores,
        }

    # ------------------------------------------------------------------

    def _price_fit(self, flight: dict[str, Any], preferences: dict[str, Any]) -> float:
        price = flight["estimated_price"]
        ceiling = preferences.get("max_price_usd")
        if not ceiling or ceiling <= 0:
            return 0.6
        ratio = price / ceiling
        if ratio <= 0.7:
            return 1.0
        if ratio <= 1.0:
            return round(1.0 - (ratio - 0.7) * 1.0, 2)
        return round(max(0.0, 0.7 - (ratio - 1.0)), 2)

    def _cabin_match(self, flight: dict[str, Any], preferences: dict[str, Any]) -> float:
        preferred = preferences.get("cabin_class", "economy")
        actual = flight["cabin_class"]
        if actual == preferred:
            return 1.0
        gap = abs(_CABIN_ORDER.index(actual) - _CABIN_ORDER.index(preferred))
        return max(0.0, 1.0 - gap * 0.4)

    def _airline_preference(self, flight: dict[str, Any], preferences: dict[str, Any]) -> float:
        preferred_airlines = {a.lower() for a in preferences.get("preferred_airlines", [])}
        if not preferred_airlines:
            return 0.6
        return 1.0 if flight["airline"].lower() in preferred_airlines else 0.4

    def _layover_tolerance(self, flight: dict[str, Any], preferences: dict[str, Any]) -> float:
        tolerance = preferences.get("layover_tolerance", "moderate")  # low | moderate | high
        stops = flight["stops"]
        if tolerance == "low":
            return {0: 1.0, 1: 0.4, 2: 0.1}.get(stops, 0.0)
        if tolerance == "high":
            return {0: 0.85, 1: 0.9, 2: 0.7}.get(stops, 0.5)
        return {0: 1.0, 1: 0.7, 2: 0.35}.get(stops, 0.2)

    def _baggage_fit(
        self, flight: dict[str, Any], preferences: dict[str, Any], trip_duration_days: int
    ) -> float:
        needs_baggage = preferences.get("needs_baggage", trip_duration_days >= 5)
        if not needs_baggage:
            return 0.8
        return 1.0 if flight["baggage_included"] else 0.3

    def _time_of_day_fit(self, flight: dict[str, Any], preferences: dict[str, Any]) -> float:
        preferred = preferences.get("preferred_departure", "any")  # morning | afternoon | evening | any
        hour = int(flight["departure_time"].split(":")[0])
        if preferred == "any":
            return 0.4 if 0 <= hour < 5 else 0.8
        band = "morning" if 5 <= hour < 12 else "afternoon" if 12 <= hour < 18 else "evening" if 18 <= hour < 24 else "red_eye"
        if band == preferred:
            return 1.0
        if band == "red_eye":
            return 0.2
        return 0.5

    def _duration_fit(self, flight: dict[str, Any], trip_duration_days: int) -> float:
        minutes = flight["_total_duration_minutes"]
        # Shorter trips are more sensitive to long total travel time.
        sensitivity = 1.4 if trip_duration_days <= 3 else 1.0
        hours = minutes / 60
        if hours <= 4:
            return 1.0
        penalty = min(1.0, (hours - 4) / 20 * sensitivity)
        return round(max(0.0, 1.0 - penalty), 2)

    def _dna_and_goal_adjustment(
        self,
        flight: dict[str, Any],
        dna: dict[str, Any] | None,
        goal_type: str | None,
    ) -> tuple[float, list[str]]:
        adjustment = 0.0
        notes: list[str] = []

        traits = (dna or {}).get("traits", {})

        if traits.get("business_orientation", 0) > 0.5 and flight["stops"] == 0 and flight["flexibility"] == "flexible":
            adjustment += 0.08
            notes.append("Business-oriented traveller — direct, flexible fare boosted.")

        if traits.get("budget_consciousness", 0) > 0.5:
            if flight["estimated_price"] <= flight.get("_price_anchor", flight["estimated_price"]):
                adjustment += 0.06
                notes.append("Budget-conscious traveller — below-average fare boosted.")

        if traits.get("luxury_orientation", 0) > 0.5 and flight["cabin_class"] in ("business", "first"):
            adjustment += 0.08
            notes.append("Luxury-oriented traveller — premium cabin boosted.")

        if traits.get("family_orientation", 0) > 0.5 and flight["baggage_included"] and flight["stops"] <= 1:
            adjustment += 0.06
            notes.append("Family-oriented traveller — included baggage and low stop count boosted.")

        if goal_type == "BUSINESS_TRAVEL" and flight["flexibility"] == "flexible":
            adjustment += 0.05
            notes.append("Business travel goal — flexible fare boosted.")

        if goal_type == "FAMILY_TRIP" and flight["baggage_included"]:
            adjustment += 0.05
            notes.append("Family trip goal — included baggage boosted.")

        return adjustment, notes

    def _persona_scores(self, flight: dict[str, Any], breakdown: dict[str, float]) -> dict[str, float]:
        """Independent, persona-weighted scores — used to label options that
        aren't the overall winner but are still the best fit for a segment."""
        family = (
            breakdown["baggage_fit"] * 0.4
            + breakdown["layover_tolerance"] * 0.35
            + breakdown["time_of_day_fit"] * 0.25
        )
        business = (
            breakdown["duration_fit"] * 0.35
            + breakdown["layover_tolerance"] * 0.35
            + (1.0 if flight["flexibility"] == "flexible" else 0.3) * 0.30
        )
        comfort = (
            breakdown["cabin_match"] * 0.5
            + (1.0 if flight["cabin_class"] in ("business", "first") else 0.3) * 0.3
            + breakdown["layover_tolerance"] * 0.2
        )
        budget = (
            breakdown["price_fit"] * 0.7
            + (1.0 - breakdown["cabin_match"] if flight["cabin_class"] != "economy" else 0.5) * 0.3
        )
        return {
            "family": round(family, 2),
            "business": round(business, 2),
            "comfort": round(comfort, 2),
            "budget": round(budget, 2),
        }


flight_scorer = FlightScorer()
