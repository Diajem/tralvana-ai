from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from ai.discovery.flights.flight_reasoner import flight_reasoner
from ai.discovery.flights.flight_risk_assessor import flight_risk_assessor
from ai.discovery.flights.flight_scorer import flight_scorer

# Base one-way fare per cabin class in USD — mirrors ai/planning/budget_estimator.py's
# _FLIGHT_USD anchors so flight recommendations stay consistent with trip budget estimates.
_CABIN_BASE_USD: dict[str, int] = {
    "economy": 650,
    "business": 2200,
    "first": 5000,
}
_CABIN_ORDER = ["economy", "business", "first"]

# Deterministic mock carrier archetypes. No live inventory — Sprint 4+ swaps
# MockFlightProvider for a real FlightProvider (Amadeus, Skyscanner, ...)
# behind the same search() signature.
_TEMPLATES: list[dict[str, Any]] = [
    {
        "label": "premium_direct",
        "airline": "Meridian Airlines",
        "airline_code": "MA",
        "stops": 0,
        "layover_minutes": 0,
        "price_multiplier": 1.6,
        "routing_factor": 1.0,
        "baggage_included": True,
        "refundability": "refundable",
        "flexibility": "flexible",
        "departure_hour": 9,
        "departure_minute": 0,
        "cabin_upgrade": True,
    },
    {
        "label": "standard_direct",
        "airline": "AeroLondon",
        "airline_code": "AL",
        "stops": 0,
        "layover_minutes": 0,
        "price_multiplier": 1.0,
        "routing_factor": 1.0,
        "baggage_included": True,
        "refundability": "partially_refundable",
        "flexibility": "flexible",
        "departure_hour": 14,
        "departure_minute": 30,
        "cabin_upgrade": False,
    },
    {
        "label": "budget_direct",
        "airline": "ValueJet",
        "airline_code": "VJ",
        "stops": 0,
        "layover_minutes": 0,
        "price_multiplier": 0.75,
        "routing_factor": 1.0,
        "baggage_included": False,
        "refundability": "non_refundable",
        "flexibility": "fixed",
        "departure_hour": 6,
        "departure_minute": 15,
        "cabin_upgrade": False,
    },
    {
        "label": "standard_one_stop",
        "airline": "SkyBridge Airways",
        "airline_code": "SB",
        "stops": 1,
        "layover_minutes": 95,
        "price_multiplier": 0.85,
        "routing_factor": 1.15,
        "baggage_included": True,
        "refundability": "partially_refundable",
        "flexibility": "flexible",
        "departure_hour": 11,
        "departure_minute": 45,
        "cabin_upgrade": False,
    },
    {
        "label": "budget_one_stop",
        "airline": "NovaWorld Air",
        "airline_code": "NW",
        "stops": 1,
        "layover_minutes": 310,
        "price_multiplier": 0.6,
        "routing_factor": 1.15,
        "baggage_included": False,
        "refundability": "non_refundable",
        "flexibility": "fixed",
        "departure_hour": 23,
        "departure_minute": 20,
        "cabin_upgrade": False,
    },
    {
        "label": "budget_two_stop",
        "airline": "Continental Express",
        "airline_code": "CE",
        "stops": 2,
        "layover_minutes": 150,
        "price_multiplier": 0.5,
        "routing_factor": 1.30,
        "baggage_included": False,
        "refundability": "non_refundable",
        "flexibility": "fixed",
        "departure_hour": 4,
        "departure_minute": 10,
        "cabin_upgrade": False,
    },
]


class MockFlightProvider:
    """
    Deterministic mock flight inventory — no external calls.

    Same interface a real provider would implement: search(origin, destination,
    departure_date, return_date, cabin_class) -> list[dict]. Swapping in
    Amadeus or Skyscanner later means implementing this method against their
    API and passing the instance to FlightIntelligence(provider=...) —
    nothing else in the discovery layer changes.
    """

    def search(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str | None,
        cabin_class: str,
    ) -> list[dict[str, Any]]:
        seed = sum(ord(c) for c in f"{origin}{destination}".lower()) or 1
        base_flight_hours = 2.0 + (seed % 12)
        route_price_factor = 0.7 + (seed % 61) / 100

        candidates: list[dict[str, Any]] = []
        for i, tpl in enumerate(_TEMPLATES):
            option_cabin = cabin_class
            if tpl["cabin_upgrade"]:
                idx = min(_CABIN_ORDER.index(cabin_class) + 1, len(_CABIN_ORDER) - 1)
                option_cabin = _CABIN_ORDER[idx]

            flight_hours = base_flight_hours * tpl["routing_factor"]
            layover_hours = tpl["layover_minutes"] / 60
            total_minutes = round((flight_hours + layover_hours) * 60)

            departure_dt = datetime.strptime(departure_date, "%Y-%m-%d").replace(
                hour=tpl["departure_hour"], minute=tpl["departure_minute"]
            )
            arrival_dt = departure_dt + timedelta(minutes=total_minutes)

            price = _CABIN_BASE_USD[option_cabin] * tpl["price_multiplier"] * route_price_factor
            price = round(price / 5) * 5

            candidates.append({
                "airline": tpl["airline"],
                "flight_number": f"{tpl['airline_code']}{100 + (seed + i * 37) % 900}",
                "cabin_class": option_cabin,
                "stops": tpl["stops"],
                "layover_duration": self._fmt_duration(tpl["layover_minutes"]) if tpl["stops"] else "",
                "departure_time": departure_dt.strftime("%H:%M"),
                "arrival_time": arrival_dt.strftime("%H:%M"),
                "total_duration": self._fmt_duration(total_minutes),
                "estimated_price": price,
                "currency": "USD",
                "baggage_included": tpl["baggage_included"],
                "refundability": tpl["refundability"],
                "flexibility": tpl["flexibility"],
                "departure_date": departure_date,
                "return_date": return_date,
                "_total_duration_minutes": total_minutes,
                "_layover_minutes": tpl["layover_minutes"],
                "_price_anchor": _CABIN_BASE_USD[option_cabin] * route_price_factor,
            })
        return candidates

    @staticmethod
    def _fmt_duration(minutes: int) -> str:
        h, m = divmod(minutes, 60)
        return f"{h}h {m}m" if h else f"{m}m"


# Priority order in which "winner" labels are assigned — earlier categories
# take precedence so no option receives more than one label.
_WINNER_PRIORITY = ["BEST_OVERALL", "LOWEST_PRICE", "SHORTEST_DURATION"]
_PERSONA_TYPES = {
    "business": "BEST_FOR_BUSINESS",
    "family": "BEST_FOR_FAMILY",
    "comfort": "BEST_FOR_COMFORT",
    "budget": "BEST_FOR_BUDGET",
}
_AVOID_THRESHOLD = 0.35


class FlightIntelligence:
    """
    Orchestrates flight discovery: generate candidates -> score -> explain ->
    assess risk -> rank -> label. Mirrors ai/planning/trip_planner.py's role
    as the top-level orchestrator for its domain.

    Sprint 1: MockFlightProvider only. Sprint 4+: real FlightProvider behind
    the same search() interface; scoring/reasoning/risk logic is unchanged.
    """

    def __init__(self, provider: MockFlightProvider | None = None) -> None:
        self._provider = provider or MockFlightProvider()

    def recommend(
        self,
        origin: str,
        destination: str,
        departure_date: str | None,
        return_date: str | None,
        cabin_class: str = "economy",
        adults: int = 1,
        budget_style: str = "balanced",
        airline_preference: str | None = None,
        trip_duration_days: int = 7,
        profile: dict[str, Any] | None = None,
        goal: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        assumptions: list[str] = []

        resolved_departure_date = departure_date
        if not resolved_departure_date:
            resolved_departure_date = (
                datetime.now(timezone.utc) + timedelta(days=30)
            ).strftime("%Y-%m-%d")
            assumptions.append(
                "No departure date supplied — defaulted to 30 days from today for mock pricing."
            )

        preferences = self._build_preferences(cabin_class, budget_style, airline_preference, profile)

        dna: dict[str, Any] | None = None
        if profile:
            try:
                from ai.intelligence import dna_inference_service
                dna = dna_inference_service.infer(profile).to_dict()
            except Exception:
                dna = None
        else:
            assumptions.append("No traveller profile linked — scoring uses default preferences only.")

        goal_type = (goal or {}).get("goal_type")

        candidates = self._provider.search(
            origin, destination, resolved_departure_date, return_date, cabin_class
        )

        scored: list[dict[str, Any]] = []
        for flight in candidates:
            score_result = flight_scorer.score(
                flight, preferences, dna=dna, goal_type=goal_type,
                trip_duration_days=trip_duration_days,
            )
            reasoning = flight_reasoner.explain(flight, score_result, preferences)
            risks = flight_risk_assessor.assess(flight)
            scored.append({
                **flight,
                "match_score": score_result["match_score"],
                "reasoning": reasoning,
                "risks": risks,
                "assumptions": self._per_option_assumptions(flight, dna, profile),
                "_persona_scores": score_result["persona_scores"],
            })

        ranked = sorted(scored, key=lambda f: f["match_score"], reverse=True)
        self._label_recommendation_types(ranked)

        for f in ranked:
            f.pop("_total_duration_minutes", None)
            f.pop("_layover_minutes", None)
            f.pop("_price_anchor", None)
            f.pop("_persona_scores", None)

        assumptions.append("Prices and schedules are deterministic mock data — no live airline inventory was queried.")
        assumptions.append(f"Scoring assumes a {preferences['cabin_class']} cabin preference and '{budget_style}' budget style.")

        return {
            "flight_options": ranked,
            "assumptions": assumptions,
            "next_actions": self._next_actions(ranked),
            "recommended_agents": ["flight_agent"],
            "summary": self._summary(origin, destination, ranked),
        }

    # ------------------------------------------------------------------

    def _build_preferences(
        self,
        cabin_class: str,
        budget_style: str,
        airline_preference: str | None,
        profile: dict[str, Any] | None,
    ) -> dict[str, Any]:
        prefs = (profile or {}).get("preferences", {})
        max_price = _CABIN_BASE_USD.get(cabin_class, _CABIN_BASE_USD["economy"]) * {
            "backpacker": 0.7, "budget": 0.85, "balanced": 1.15, "comfort": 1.5, "luxury": 2.2,
        }.get(budget_style, 1.15)

        preferred_airlines: list[str] = []
        if airline_preference:
            preferred_airlines.append(airline_preference)
        for program in prefs.get("airline_programs", []) if isinstance(prefs.get("airline_programs"), list) else []:
            preferred_airlines.append(str(program))

        return {
            "cabin_class": cabin_class,
            "max_price_usd": max_price,
            "preferred_airlines": preferred_airlines,
            "layover_tolerance": {"backpacker": "high", "budget": "high", "balanced": "moderate",
                                   "comfort": "low", "luxury": "low"}.get(budget_style, "moderate"),
            "needs_baggage": prefs.get("accommodation_type") != "hostel",
            "preferred_departure": "any",
        }

    def _per_option_assumptions(
        self, flight: dict[str, Any], dna: dict[str, Any] | None, profile: dict[str, Any] | None
    ) -> list[str]:
        a: list[str] = []
        if not profile:
            a.append("No traveller profile — default cabin and budget assumptions applied.")
        if not dna:
            a.append("No Traveller DNA available — persona-based scoring skipped for this option.")
        return a

    def _label_recommendation_types(self, ranked: list[dict[str, Any]]) -> None:
        if not ranked:
            return

        labeled: dict[int, str] = {}

        avoid_idx = [
            i for i, f in enumerate(ranked)
            if f["match_score"] < _AVOID_THRESHOLD
        ]
        for i in avoid_idx:
            labeled[i] = "AVOID"

        eligible = [i for i in range(len(ranked)) if i not in labeled]
        if eligible:
            best_overall = max(eligible, key=lambda i: ranked[i]["match_score"])
            labeled[best_overall] = "BEST_OVERALL"

        eligible = [i for i in range(len(ranked)) if i not in labeled]
        if eligible:
            lowest_price = min(eligible, key=lambda i: ranked[i]["estimated_price"])
            labeled[lowest_price] = "LOWEST_PRICE"

        eligible = [i for i in range(len(ranked)) if i not in labeled]
        if eligible:
            shortest = min(eligible, key=lambda i: ranked[i]["_total_duration_minutes"])
            labeled[shortest] = "SHORTEST_DURATION"

        for persona, rec_type in _PERSONA_TYPES.items():
            eligible = [i for i in range(len(ranked)) if i not in labeled]
            if not eligible:
                break
            best = max(eligible, key=lambda i: (ranked[i]["_persona_scores"][persona], -i))
            labeled[best] = rec_type

        # Anything still unlabeled (more options than categories) falls back
        # to its own best-fit persona so every option gets exactly one type.
        for i in range(len(ranked)):
            if i in labeled:
                continue
            persona = max(ranked[i]["_persona_scores"], key=lambda p: ranked[i]["_persona_scores"][p])
            labeled[i] = _PERSONA_TYPES[persona]

        for i, f in enumerate(ranked):
            f["recommendation_type"] = labeled[i]

    def _next_actions(self, ranked: list[dict[str, Any]]) -> list[str]:
        actions = [
            "Confirm exact travel dates for accurate pricing.",
            "Compare baggage policies before booking.",
            "Check visa and passport requirements for the destination.",
        ]
        if any(f["refundability"] == "non_refundable" for f in ranked):
            actions.append("Consider travel insurance for non-refundable fares.")
        actions.append("Live availability has not been checked — fares are indicative only.")
        return actions

    def _summary(self, origin: str, destination: str, ranked: list[dict[str, Any]]) -> str:
        if not ranked:
            return f"No flight options could be generated for {origin} to {destination}."
        best = next((f for f in ranked if f["recommendation_type"] == "BEST_OVERALL"), ranked[0])
        return (
            f"{len(ranked)} flight option(s) ranked for {origin} to {destination}. "
            f"Best overall: {best['airline']} {best['flight_number']} "
            f"at {best['currency']} {best['estimated_price']} (match {best['match_score']}). "
            f"No live bookings have been made."
        )


# Routed through the Intelligence Gateway (T-025) — GatewayFlightProvider
# implements this same .search() interface and calls
# intelligence_gateway.execute() instead of MockFlightProvider directly,
# so caching/retry/failover/observability apply. Imported here, after
# MockFlightProvider is already defined above, to avoid a circular import
# (travelos/intelligence_gateway/discovery_adapters.py lazily imports
# MockFlightProvider from this module to build its gateway-contract
# wrapper). Deterministic mock data, byte-identical output — see
# docs/INTELLIGENCE_GATEWAY.md's Discovery Integration section.
from travelos.intelligence_gateway.discovery_adapters import GatewayFlightProvider  # noqa: E402

flight_intelligence = FlightIntelligence(provider=GatewayFlightProvider())
