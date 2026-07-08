from __future__ import annotations

from typing import Any

from ai.planning.budget_estimator import budget_estimator
from ai.planning.itinerary_builder import itinerary_builder
from ai.planning.risk_assessor import risk_assessor

_GOAL_AGENTS: dict[str, list[str]] = {
    "FOOTBALL_TRAVEL": ["football_agent", "hotel_agent", "experience_agent"],
    "FOOD_TOUR":       ["food_agent", "experience_agent", "hotel_agent"],
    "RELAXATION":      ["hotel_agent", "experience_agent"],
    "ADVENTURE":       ["experience_agent", "hotel_agent"],
    "FAMILY_TRIP":     ["hotel_agent", "experience_agent", "visa_agent"],
    "BUSINESS_TRAVEL": ["hotel_agent", "flight_agent"],
    "PHOTOGRAPHY":     ["experience_agent", "hotel_agent"],
    "PILGRIMAGE":      ["experience_agent", "visa_agent"],
    "DIASPORA_TRAVEL": ["flight_agent", "experience_agent", "visa_agent"],
    "ROMANTIC_TRIP":   ["hotel_agent", "experience_agent"],
    "GENERAL_TRAVEL":  ["flight_agent", "hotel_agent", "experience_agent", "visa_agent"],
}

_RECOMMENDED_DESTINATIONS: dict[str, list[dict[str, str]]] = {
    "FOOTBALL_TRAVEL": [
        {"city": "London", "country": "United Kingdom", "reason": "Home to the Premier League and iconic grounds"},
        {"city": "Barcelona", "country": "Spain", "reason": "Camp Nou and La Liga football culture"},
        {"city": "Rome", "country": "Italy", "reason": "Stadio Olimpico and Derby della Capitale"},
    ],
    "FOOD_TOUR": [
        {"city": "Tokyo", "country": "Japan", "reason": "More Michelin stars than any city on Earth"},
        {"city": "Barcelona", "country": "Spain", "reason": "Tapas, La Boqueria, and avant-garde cuisine"},
        {"city": "Paris", "country": "France", "reason": "The birthplace of modern haute cuisine"},
    ],
    "RELAXATION": [
        {"city": "Dubai", "country": "UAE", "reason": "World-class resorts and spa culture"},
        {"city": "Cape Town", "country": "South Africa", "reason": "Beaches, mountains, and wine farms"},
        {"city": "Barcelona", "country": "Spain", "reason": "Beach city with a relaxed Mediterranean pace"},
    ],
    "PILGRIMAGE": [
        {"city": "Lagos", "country": "Nigeria", "reason": "Major West African spiritual destination"},
        {"city": "Dubai", "country": "UAE", "reason": "Gateway to key Islamic heritage sites"},
        {"city": "Rome", "country": "Italy", "reason": "Vatican City and centuries of Christian heritage"},
    ],
    "DIASPORA_TRAVEL": [
        {"city": "Lagos", "country": "Nigeria", "reason": "Cultural, economic, and family reconnection hub"},
        {"city": "Accra", "country": "Ghana", "reason": "Year of Return heritage tourism destination"},
        {"city": "London", "country": "United Kingdom", "reason": "Largest Nigerian and West African diaspora in Europe"},
    ],
    "GENERAL_TRAVEL": [
        {"city": "London", "country": "United Kingdom", "reason": "World-class culture, history, and food"},
        {"city": "Paris", "country": "France", "reason": "Architecture, art, and cuisine"},
        {"city": "Dubai", "country": "UAE", "reason": "Modern luxury with easy international connections"},
    ],
}


class TripPlanner:
    """
    Orchestrates all AI planning modules to produce a structured TripPlan output.

    Calls ItineraryBuilder, BudgetEstimator, and RiskAssessor — all deterministic,
    no external APIs.

    Sprint 3+: integrate live inventory, LLM-enhanced itinerary narrative.
    """

    def plan(
        self,
        origin: str,
        destination: str,
        duration_days: int,
        budget_style: str,
        cabin_class: str,
        interests: list[str],
        travellers: dict[str, Any],
        goal_type: str = "GENERAL_TRAVEL",
        goal: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        adults = travellers.get("adults", 1)
        passport_iso = (profile or {}).get("identity", {}).get("nationality_iso", "NG")

        # 1. Identify missing information
        missing = self._check_missing(destination, duration_days, goal)

        # 2. Recommended destinations (when none specified)
        rec_destinations: list[dict[str, str]] = []
        if not destination:
            rec_destinations = _RECOMMENDED_DESTINATIONS.get(goal_type, _RECOMMENDED_DESTINATIONS["GENERAL_TRAVEL"])

        # 3. Itinerary
        draft_itinerary = itinerary_builder.build(
            destination=destination or "your destination",
            duration_days=duration_days,
            goal_type=goal_type,
            budget_style=budget_style,
            interests=interests,
        )

        # 4. Budget
        budget_breakdown = budget_estimator.estimate(
            destination=destination,
            duration_days=duration_days,
            budget_style=budget_style,
            cabin_class=cabin_class,
            adults=adults,
            profile=profile,
        )

        # 5. Risks
        risks = risk_assessor.assess(
            destination=destination,
            passport_iso=passport_iso,
            profile=profile,
        )

        # 6. Confidence
        confidence = self._confidence(destination, duration_days, goal, profile)

        # 7. Assumptions
        assumptions = self._assumptions(destination, profile, budget_style)

        # 8. Next actions
        next_actions = self._next_actions(missing, confidence)

        # 9. Trip summary
        summary = self._summary(destination, duration_days, goal_type, budget_style, adults)

        return {
            "trip_summary": summary,
            "assumptions": assumptions,
            "missing_information": missing,
            "recommended_destinations": rec_destinations,
            "draft_itinerary": draft_itinerary,
            "estimated_budget_breakdown": budget_breakdown,
            "recommended_agents": _GOAL_AGENTS.get(goal_type, _GOAL_AGENTS["GENERAL_TRAVEL"]),
            "risks": risks,
            "confidence": confidence,
            "next_actions": next_actions,
        }

    # ------------------------------------------------------------------

    def _check_missing(
        self, destination: str, duration_days: int, goal: dict[str, Any] | None
    ) -> list[str]:
        missing: list[str] = []
        if not destination:
            missing.append("Destination city not specified")
        if not duration_days or duration_days < 1:
            missing.append("Trip duration not specified")
        if goal:
            b = goal.get("budget", {})
            if not b.get("max_usd"):
                missing.append("Budget range not set on goal")
            t = goal.get("timeframe", {})
            if not t.get("earliest"):
                missing.append("Travel dates not set on goal")
        return missing

    def _confidence(
        self,
        destination: str,
        duration_days: int,
        goal: dict[str, Any] | None,
        profile: dict[str, Any] | None,
    ) -> float:
        score = 0.30
        if destination:
            score += 0.20
        if duration_days and duration_days > 0:
            score += 0.10
        if profile:
            score += 0.10
        if goal:
            b = goal.get("budget", {})
            if b.get("min_usd") and b.get("max_usd"):
                score += 0.10
            t = goal.get("timeframe", {})
            if t.get("earliest") and t.get("latest"):
                score += 0.10
            if goal.get("interests"):
                score += 0.10
        return round(min(score, 1.0), 2)

    def _assumptions(
        self,
        destination: str,
        profile: dict[str, Any] | None,
        budget_style: str,
    ) -> list[str]:
        a: list[str] = []
        if not profile:
            a.append("No traveller profile linked — default planning parameters used")
        a.append(f"Budget estimated on '{budget_style}' style with global average rates")
        a.append("No live flight or hotel pricing has been checked")
        if destination:
            a.append(f"Itinerary assumes direct travel to {destination} is available from origin")
        return a

    def _next_actions(self, missing: list[str], confidence: float) -> list[str]:
        actions: list[str] = []
        if missing:
            actions.append("Complete missing information to improve planning accuracy")
        if confidence < 0.65:
            actions.append("Add traveller goal with budget and travel dates")
        actions.extend([
            "Confirm passport and visa requirements",
            "Check live flight availability",
            "Review and adjust day-by-day itinerary",
            "Get travel insurance quotes",
        ])
        return actions

    def _summary(
        self,
        destination: str,
        duration: int,
        goal_type: str,
        budget_style: str,
        adults: int,
    ) -> str:
        dest = destination or "an undecided destination"
        type_label = goal_type.replace("_", " ").title()
        return (
            f"Draft {type_label} trip to {dest} for {adults} adult(s) over {duration} days. "
            f"Planned at {budget_style} budget level. "
            f"Day-by-day itinerary, budget estimate, and risk assessment included. "
            f"No live bookings have been made."
        )
