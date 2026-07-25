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
class GroundingNotice:
    """Public, provider-neutral description of how current a planner fact is.

    The planner must never make a mock estimate, sandbox response, static
    guidance rule, climate profile, or generic activity idea look like live
    availability.  These values are deliberately presentation facts rather
    than confidence scores: they describe provenance and the action the
    traveller still needs to take.
    """

    domain: str
    level: str
    title: str
    message: str
    data_source: str
    is_current: bool
    requires_confirmation: bool
    retrieved_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "level": self.level,
            "title": self.title,
            "message": self.message,
            "data_source": self.data_source,
            "is_current": self.is_current,
            "requires_confirmation": self.requires_confirmation,
            "retrieved_at": self.retrieved_at,
        }


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
    grounding_notices: list[GroundingNotice] = field(default_factory=list)
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
            "grounding_notices": [notice.to_dict() for notice in self.grounding_notices],
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
        grounding_notices = self._grounding_notices(
            destination=destination_rec,
            flight=flight_rec,
            accommodation=accommodation_rec,
            budget=budget_rec,
            visa=visa_rec,
            weather=weather_rec,
            interests=interests or [],
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
            grounding_notices=grounding_notices,
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
                source = str(flight.get("data_source", "MOCK")).upper()
                if self._is_live_source(source):
                    parts.append(
                        f"A current provider search found {airline} at {currency} {price}; "
                        "recheck availability before booking."
                    )
                elif self._is_sandbox_source(source):
                    parts.append(
                        f"Duffel sandbox test data returned {airline} at {currency} {price}; "
                        "this is not a purchasable fare."
                    )
                else:
                    parts.append(
                        f"A planning estimate uses {airline} at around {currency} {price}; "
                        "check a live provider before booking."
                    )

        if accommodation:
            name = accommodation.get("property_name")
            acc_type = str(accommodation.get("accommodation_type", "")).replace("_", " ").lower()
            if name:
                stay_desc = f"a {acc_type}" if acc_type else "a property"
                source = str(accommodation.get("data_source", "MOCK")).upper()
                if self._is_live_source(source):
                    parts.append(
                        f"A current provider search found {name}, {stay_desc}; "
                        "recheck the rate and availability before booking."
                    )
                elif self._is_sandbox_source(source):
                    parts.append(
                        f"Duffel Stays sandbox test data returned {name}, {stay_desc}; "
                        "it is not available to book from this result."
                    )
                else:
                    parts.append(
                        f"The plan uses {name}, {stay_desc}, as an indicative stay; "
                        "check live rates and availability before booking."
                    )

        if budget:
            style = budget.get("budget_style")
            if style:
                parts.append(f"Overall spending sits at a {style} level.")

        if visa and visa.get("visa_status"):
            if visa.get("travel_authorisation_required"):
                authorisation = visa.get("visa_type", "travel authorisation")
                parts.append(
                    f"Planning guidance indicates {authorisation} travel authorisation is "
                    "required before departure; verify this with the official authority."
                )
            elif visa.get("visa_required"):
                parts.append(
                    "Planning guidance indicates a visa is required for this trip "
                    f"({visa.get('visa_type', 'see visa summary')}); verify this with "
                    "the official authority."
                )
            else:
                parts.append(
                    "Planning guidance indicates no visa is required for this trip; "
                    "verify this with the official authority."
                )

        if weather and weather.get("recommendation"):
            parts.append(f"Seasonal weather profile: {weather['recommendation']}")

        parts.append(f"Overall confidence in this plan is {confidence:.0%}.")
        return " ".join(parts)

    # ------------------------------------------------------------------

    def _grounding_notices(
        self,
        destination: dict[str, Any] | None,
        flight: dict[str, Any] | None,
        accommodation: dict[str, Any] | None,
        budget: dict[str, Any] | None,
        visa: dict[str, Any] | None,
        weather: dict[str, Any] | None,
        interests: list[str],
    ) -> list[GroundingNotice]:
        notices: list[GroundingNotice] = []

        if destination:
            notices.append(
                GroundingNotice(
                    domain="destination",
                    level="CURATED",
                    title="Curated destination guidance",
                    message=(
                        "Destination suggestions come from Tralvana's curated catalogue, "
                        "not a live places or opening-hours search."
                    ),
                    data_source=str(destination.get("data_source", "TRALVANA_CURATED")),
                    is_current=False,
                    requires_confirmation=True,
                )
            )

        if flight:
            notices.append(self._provider_notice("flight", flight))

        if accommodation:
            notices.append(self._provider_notice("accommodation", accommodation))

        if budget:
            notices.append(
                GroundingNotice(
                    domain="budget",
                    level="ESTIMATE",
                    title="Indicative budget",
                    message=(
                        "Budget figures use static regional planning rates. They are not a "
                        "quote and should be recalculated from confirmed live prices."
                    ),
                    data_source=str(budget.get("data_source", "STATIC_REGIONAL_RATES")),
                    is_current=False,
                    requires_confirmation=True,
                )
            )

        if visa:
            notices.append(
                GroundingNotice(
                    domain="visa",
                    level="GUIDANCE",
                    title="Entry guidance—not legal advice",
                    message=(
                        "Entry guidance comes from Tralvana's general rule set, not a live "
                        "government, embassy, or Timatic check. Verify it officially before travel."
                    ),
                    data_source=str(visa.get("data_source", "TRALVANA_GENERAL_RULES")),
                    is_current=False,
                    requires_confirmation=True,
                )
            )

        if weather:
            notices.append(
                GroundingNotice(
                    domain="weather",
                    level="CLIMATE_PROFILE",
                    title="Seasonal profile—not a forecast",
                    message=(
                        "Weather guidance is based on a general seasonal climate profile, "
                        "not a current forecast or live safety alert."
                    ),
                    data_source=str(weather.get("data_source", "TRALVANA_CLIMATE_PROFILE")),
                    is_current=False,
                    requires_confirmation=True,
                )
            )

        if self._has_event_interest(interests):
            notices.append(
                GroundingNotice(
                    domain="events",
                    level="IDEA",
                    title="Event ideas require a live check",
                    message=(
                        "Fashion and football activities in the daily outline are planning "
                        "ideas. No live event calendar, fixture, ticket, or availability "
                        "provider was queried."
                    ),
                    data_source="NO_LIVE_EVENT_PROVIDER",
                    is_current=False,
                    requires_confirmation=True,
                )
            )

        return notices

    def _provider_notice(
        self, domain: str, recommendation: dict[str, Any]
    ) -> GroundingNotice:
        source = str(recommendation.get("data_source", "MOCK")).upper()
        retrieved_at = recommendation.get("retrieved_at")
        label = "Flight" if domain == "flight" else "Accommodation"

        if self._is_live_source(source):
            return GroundingNotice(
                domain=domain,
                level="LIVE",
                title=f"Current {label.lower()} provider result",
                message=(
                    f"{label} data came from a live provider search. Prices and "
                    "availability can still change before booking."
                ),
                data_source=source,
                is_current=True,
                requires_confirmation=True,
                retrieved_at=str(retrieved_at) if retrieved_at else None,
            )

        if self._is_sandbox_source(source):
            return GroundingNotice(
                domain=domain,
                level="SANDBOX",
                title=f"{label} sandbox test data",
                message=(
                    f"{label} results came from a provider's sandbox environment. "
                    "They demonstrate the integration but are not available to purchase."
                ),
                data_source=source,
                is_current=False,
                requires_confirmation=True,
                retrieved_at=str(retrieved_at) if retrieved_at else None,
            )

        fallback = source == "MOCK_FALLBACK"
        return GroundingNotice(
            domain=domain,
            level="ESTIMATE",
            title=f"Estimated {label.lower()} result",
            message=(
                f"{label} data is deterministic mock planning data"
                + (" used after a provider failure" if fallback else "")
                + ", not live inventory or a bookable quote."
            ),
            data_source=source,
            is_current=False,
            requires_confirmation=True,
            retrieved_at=str(retrieved_at) if retrieved_at else None,
        )

    @staticmethod
    def _is_live_source(source: str) -> bool:
        """Only explicit production-shaped labels can be called current.

        Unknown or future provider labels fail closed to ESTIMATE in
        `_provider_notice`; a provider cannot become "live" merely because
        its name contains a vendor brand.
        """
        return source in {"LIVE", "LIVE_PROVIDER", "PRODUCTION", "PRODUCTION_PROVIDER"}

    @staticmethod
    def _is_sandbox_source(source: str) -> bool:
        return "SANDBOX" in source

    @staticmethod
    def _has_event_interest(interests: list[str]) -> bool:
        return any(
            term in str(interest).lower()
            for interest in interests
            for term in ("fashion", "style", "football", "soccer", "match", "event")
        )


trip_assembly_engine = TripAssemblyEngine()
