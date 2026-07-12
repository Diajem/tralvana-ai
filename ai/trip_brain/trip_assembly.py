"""
Trip Assembly Engine (T-040) — synthesizes Trip Brain's already-computed
UnifiedRecommendation into one coherent, consultant-style TripItinerary.

Trip Brain (ai/trip_brain/coordinator.py) remains the sole orchestrator
of the six Discovery modules — unchanged, its own tests untouched. This
module never re-scores, re-ranks, or recalculates anything a Discovery
module, Trip Brain, or the Explainability Engine already produced; it
only reads fields already computed (AgentResult.data's `top_option`,
UnifiedRecommendation.explanation) and assembles them into the shape
docs/AI_TRAVEL_PLANNER.md's Definition of Done requires.

Two things are genuinely new here, both compositional, neither a new
scoring model:

1. **Daily outline** — built by the pre-existing
   ai/planning/itinerary_builder.py (T-008, Sprint 1's deterministic
   goal-type-templated day planner), called here, never duplicated.
2. **Executive summary** — a natural-language paragraph assembled from
   facts each module already decided (destination, flight, property,
   budget tier, visa outcome, weather fit), not a new judgement about
   which one to prefer. Every clause is conditional on the fact it
   quotes actually being present — nothing is invented when a module
   didn't run or came back empty.

Deliberately NOT called from ai/trip_brain/coordinator.py — TripBrain.plan()
is unchanged. This is a second, separate caller of Trip Brain's output,
the same relationship ai/concierge/conversation_engine.py already has
with it (see services/api/app/routers/planner.py, T-040's one new call
site).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ai.planning.itinerary_builder import itinerary_builder
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus
from ai.trip_brain.models import UnifiedRecommendation


@dataclass
class TripItinerary:
    executive_summary: str
    destination_recommendation: dict[str, Any] | None
    flight_recommendation: dict[str, Any] | None
    accommodation_recommendation: dict[str, Any] | None
    budget_summary: dict[str, Any] | None
    visa_summary: dict[str, Any] | None
    weather_expectations: dict[str, Any] | None
    risks: list[str]
    assumptions: list[str]
    daily_outline: list[dict[str, Any]]
    why_this_itinerary: list[dict[str, str]]
    confidence: float
    confidence_explanation: str
    alternative_options: list[dict[str, Any]]
    modules_used: list[str] = field(default_factory=list)
    modules_unavailable: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "executive_summary": self.executive_summary,
            "destination_recommendation": self.destination_recommendation,
            "flight_recommendation": self.flight_recommendation,
            "accommodation_recommendation": self.accommodation_recommendation,
            "budget_summary": self.budget_summary,
            "visa_summary": self.visa_summary,
            "weather_expectations": self.weather_expectations,
            "risks": self.risks,
            "assumptions": self.assumptions,
            "daily_outline": self.daily_outline,
            "why_this_itinerary": self.why_this_itinerary,
            "confidence": self.confidence,
            "confidence_explanation": self.confidence_explanation,
            "alternative_options": self.alternative_options,
            "modules_used": self.modules_used,
            "modules_unavailable": self.modules_unavailable,
        }


# AgentResult.agent_name -> the itinerary section it feeds, matching
# ai/trip_brain/discovery_adapters.py's MODULE_RUNNERS naming exactly.
_RANKED_MODULES = ("destination_intelligence", "flight_intelligence", "accommodation_intelligence", "budget_intelligence")
_ASSESSMENT_MODULES = ("visa_intelligence", "weather_intelligence")


class TripAssemblyEngine:
    def assemble(
        self,
        unified: UnifiedRecommendation,
        destination: str,
        duration_days: int,
        goal_type: str = "GENERAL_TRAVEL",
        budget_style: str = "balanced",
        interests: list[str] | None = None,
    ) -> TripItinerary:
        by_module = {r.agent_name: r for r in unified.results}

        destination_rec = self._top_option(by_module.get("destination_intelligence"))
        flight_rec = self._top_option(by_module.get("flight_intelligence"))
        accommodation_rec = self._top_option(by_module.get("accommodation_intelligence"))
        budget_rec = self._top_option(by_module.get("budget_intelligence"))
        visa_rec = self._assessment(by_module.get("visa_intelligence"))
        weather_rec = self._assessment(by_module.get("weather_intelligence"))

        daily_outline = itinerary_builder.build(
            destination=destination or "your destination",
            duration_days=max(int(duration_days or 1), 1),
            goal_type=goal_type or "GENERAL_TRAVEL",
            budget_style=budget_style or "balanced",
            interests=interests,
        )

        explanation = unified.explanation or {}

        executive_summary = self._executive_summary(
            destination=destination,
            flight=flight_rec,
            accommodation=accommodation_rec,
            budget=budget_rec,
            visa=visa_rec,
            weather=weather_rec,
            confidence=unified.overall_confidence,
            modules_succeeded=unified.modules_succeeded,
        )

        return TripItinerary(
            executive_summary=executive_summary,
            destination_recommendation=destination_rec,
            flight_recommendation=flight_rec,
            accommodation_recommendation=accommodation_rec,
            budget_summary=budget_rec,
            visa_summary=visa_rec,
            weather_expectations=weather_rec,
            risks=list(explanation.get("risks", [])),
            assumptions=list(explanation.get("assumptions", [])),
            daily_outline=daily_outline,
            why_this_itinerary=list(explanation.get("recommendation_drivers", [])),
            confidence=unified.overall_confidence,
            confidence_explanation=explanation.get("confidence_explanation", ""),
            alternative_options=list(explanation.get("alternatives_considered", [])),
            modules_used=list(unified.modules_succeeded),
            modules_unavailable=list(unified.modules_failed),
        )

    # ------------------------------------------------------------------

    def _top_option(self, result: AgentResult | None) -> dict[str, Any] | None:
        """The module's own already-labelled BEST_OVERALL pick
        (ai/trip_brain/discovery_adapters.py's `_top_option()`,
        computed once, reused here verbatim) — never recomputed."""
        if result is None or result.status == AgentStatus.FAILED:
            return None
        top = result.data.get("top_option")
        return top or None

    def _assessment(self, result: AgentResult | None) -> dict[str, Any] | None:
        """Visa/Weather Intelligence's single-assessment shape (not a
        ranked list) — the whole `data` dict, unchanged."""
        if result is None or result.status == AgentStatus.FAILED:
            return None
        return result.data or None

    def _executive_summary(
        self,
        destination: str,
        flight: dict[str, Any] | None,
        accommodation: dict[str, Any] | None,
        budget: dict[str, Any] | None,
        visa: dict[str, Any] | None,
        weather: dict[str, Any] | None,
        confidence: float,
        modules_succeeded: list[str],
    ) -> str:
        """A natural-language paragraph over facts already decided by
        each module — every clause only appears if the fact it quotes
        is actually present; nothing here is invented or re-derived."""
        if not modules_succeeded:
            return "I wasn't able to put together a recommendation yet — let's gather a bit more detail first."

        where = destination or "this trip"
        parts = [f"Here's the plan I've put together for {where}."]

        if flight:
            airline = flight.get("airline")
            price = flight.get("estimated_price")
            currency = flight.get("currency", "")
            if airline and price is not None:
                parts.append(f"You'll fly with {airline} for {currency} {price}.")

        if accommodation:
            name = accommodation.get("property_name")
            acc_type = str(accommodation.get("accommodation_type", "")).replace("_", " ").lower()
            if name:
                stay_desc = f"a {acc_type}" if acc_type else "a property"
                parts.append(f"You'll stay at {name}, {stay_desc}.")

        if budget:
            style = budget.get("budget_style")
            if style:
                parts.append(f"Overall spending sits at a {style} level.")

        if visa and visa.get("visa_status"):
            if visa.get("visa_required"):
                parts.append(f"A visa is required for this trip ({visa.get('visa_type', 'see visa summary')}).")
            else:
                parts.append("No visa is required for this trip.")

        if weather and weather.get("recommendation"):
            parts.append(str(weather["recommendation"]))

        parts.append(f"Overall confidence in this plan is {confidence:.0%}.")
        return " ".join(parts)


trip_assembly_engine = TripAssemblyEngine()
