from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from ai.discovery.accommodation.accommodation_normalizer import accommodation_normalizer
from ai.discovery.accommodation.accommodation_reasoner import accommodation_reasoner
from ai.discovery.accommodation.accommodation_risk_assessor import accommodation_risk_assessor
from ai.discovery.accommodation.accommodation_scorer import accommodation_scorer
from ai.discovery.accommodation.mock_accommodation_provider import MockAccommodationProvider

_NIGHTLY_BASE_USD = 90
_BUDGET_STYLE_MULTIPLIER: dict[str, float] = {
    "backpacker": 0.5, "budget": 0.7, "balanced": 1.1, "comfort": 1.6, "luxury": 2.5,
}

# Priority order in which "winner" labels are assigned — earlier categories
# take precedence so no option receives more than one label. See
# docs/DISCOVERY_LAYER_PATTERN.md for the general algorithm.
_PERSONA_TYPES = {
    "value": "BEST_VALUE",
    "location": "BEST_LOCATION",
    "comfort": "BEST_COMFORT",
    "family": "BEST_FOR_FAMILY",
    "business": "BEST_FOR_BUSINESS",
    "budget": "BEST_BUDGET",
}
_AVOID_THRESHOLD = 0.35


class AccommodationIntelligence:
    """
    Orchestrates accommodation discovery: generate candidates -> normalize ->
    score -> explain -> assess risk -> rank -> label. Mirrors
    ai/discovery/flights/flight_intelligence.py's role as the top-level
    orchestrator for its domain. See docs/DISCOVERY_LAYER_PATTERN.md.

    Sprint 1: MockAccommodationProvider only. Sprint 4+: real
    AccommodationProvider (Booking.com, Expedia) behind the same search()
    interface; only the Normalizer needs to change.
    """

    def __init__(self, provider: MockAccommodationProvider | None = None) -> None:
        self._provider = provider or MockAccommodationProvider()

    def recommend(
        self,
        destination: str,
        check_in_date: str | None,
        nights: int = 7,
        accommodation_type_preference: str | None = None,
        budget_style: str = "balanced",
        adults: int = 1,
        children: int = 0,
        business_trip: bool = False,
        accessibility_required: bool = False,
        profile: dict[str, Any] | None = None,
        goal: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        assumptions: list[str] = []

        resolved_check_in = check_in_date
        if not resolved_check_in:
            resolved_check_in = (
                datetime.now(timezone.utc) + timedelta(days=30)
            ).strftime("%Y-%m-%d")
            assumptions.append(
                "No check-in date supplied — defaulted to 30 days from today for mock pricing."
            )

        preferences = self._build_preferences(
            accommodation_type_preference, budget_style, children,
            business_trip, accessibility_required, profile,
        )

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

        raw_candidates = self._provider.search(destination, resolved_check_in, nights)
        normalized = [accommodation_normalizer.normalize(r) for r in raw_candidates]

        price_anchor = _NIGHTLY_BASE_USD * _BUDGET_STYLE_MULTIPLIER.get(budget_style, 1.1)

        scored: list[dict[str, Any]] = []
        for a in normalized:
            a["_price_anchor"] = price_anchor
            score_result = accommodation_scorer.score(a, preferences, dna=dna, goal_type=goal_type)
            reasoning = accommodation_reasoner.explain(a, score_result, preferences)
            risks = accommodation_risk_assessor.assess(a)
            scored.append({
                **a,
                "match_score": score_result["match_score"],
                "reasoning": reasoning,
                "risks": risks,
                "assumptions": self._per_option_assumptions(dna, profile),
                "_persona_scores": score_result["persona_scores"],
            })

        ranked = sorted(scored, key=lambda a: a["match_score"], reverse=True)
        self._label_recommendation_types(ranked)

        for a in ranked:
            a.pop("_price_anchor", None)
            a.pop("_persona_scores", None)
            a.pop("_amenities", None)

        assumptions.append("Prices and availability are deterministic mock data — no live provider inventory was queried.")
        assumptions.append(f"Scoring assumes a '{budget_style}' budget style for a {nights}-night stay.")

        return {
            "accommodation_options": ranked,
            "assumptions": assumptions,
            "next_actions": self._next_actions(ranked),
            "recommended_agents": ["hotel_agent"],
            "summary": self._summary(destination, ranked),
        }

    # ------------------------------------------------------------------

    def _build_preferences(
        self,
        accommodation_type_preference: str | None,
        budget_style: str,
        children: int,
        business_trip: bool,
        accessibility_required: bool,
        profile: dict[str, Any] | None,
    ) -> dict[str, Any]:
        prefs = (profile or {}).get("preferences", {})
        max_price = _NIGHTLY_BASE_USD * _BUDGET_STYLE_MULTIPLIER.get(budget_style, 1.1)

        return {
            "accommodation_type": accommodation_type_preference,
            "max_price_usd": max_price,
            "location_preference": "central",
            "needs_breakfast": budget_style in ("comfort", "luxury"),
            "needs_flexible_cancellation": budget_style in ("comfort", "luxury"),
            "accessibility_required": accessibility_required or bool(prefs.get("accessibility_needs")),
            "has_children": children > 0,
            "is_business_trip": business_trip,
        }

    def _per_option_assumptions(
        self, dna: dict[str, Any] | None, profile: dict[str, Any] | None
    ) -> list[str]:
        a: list[str] = []
        if not profile:
            a.append("No traveller profile — default budget and location assumptions applied.")
        if not dna:
            a.append("No Traveller DNA available — persona-based scoring skipped for this option.")
        return a

    def _label_recommendation_types(self, ranked: list[dict[str, Any]]) -> None:
        if not ranked:
            return

        labeled: dict[int, str] = {}

        avoid_idx = [i for i, a in enumerate(ranked) if a["match_score"] < _AVOID_THRESHOLD]
        for i in avoid_idx:
            labeled[i] = "AVOID"

        eligible = [i for i in range(len(ranked)) if i not in labeled]
        if eligible:
            best_overall = max(eligible, key=lambda i: ranked[i]["match_score"])
            labeled[best_overall] = "BEST_OVERALL"

        for persona, rec_type in _PERSONA_TYPES.items():
            eligible = [i for i in range(len(ranked)) if i not in labeled]
            if not eligible:
                break
            best = max(eligible, key=lambda i: (ranked[i]["_persona_scores"][persona], -i))
            labeled[best] = rec_type

        # With exactly 8 mock templates and exactly 8 recommendation types
        # (1 overall + 6 personas + AVOID), a forced label collision is
        # possible if AVOID's threshold never triggers: 8 candidates would
        # then compete for only 7 positive slots. Resolve it the same way a
        # human reviewer would: if one candidate won no category at all,
        # it's the relative weakest of this set — label it AVOID rather than
        # duplicate someone else's label. Only applies once, and only if
        # AVOID wasn't already assigned by the threshold check above.
        remaining = [i for i in range(len(ranked)) if i not in labeled]
        if remaining and "AVOID" not in labeled.values():
            weakest = min(remaining, key=lambda i: ranked[i]["match_score"])
            labeled[weakest] = "AVOID"
            remaining.remove(weakest)

        # Anything still unlabeled (more options than total category count)
        # falls back to its own best-fit persona among types not already
        # used, so duplicates only occur when candidates truly outnumber
        # every available category.
        used_types = set(labeled.values())
        for i in remaining:
            scores = ranked[i]["_persona_scores"]
            for persona, _ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True):
                rec_type = _PERSONA_TYPES[persona]
                if rec_type not in used_types:
                    labeled[i] = rec_type
                    used_types.add(rec_type)
                    break
            else:
                labeled[i] = _PERSONA_TYPES[max(scores, key=scores.get)]

        for i, a in enumerate(ranked):
            a["recommendation_type"] = labeled[i]

    def _next_actions(self, ranked: list[dict[str, Any]]) -> list[str]:
        actions = [
            "Confirm exact check-in and check-out dates for accurate pricing.",
            "Compare cancellation policies before booking.",
            "Check neighbourhood safety advisories for the destination.",
        ]
        if any(a["cancellation_policy"] == "non_refundable" for a in ranked):
            actions.append("Consider travel insurance for non-refundable bookings.")
        actions.append("Live availability has not been checked — rates are indicative only.")
        return actions

    def _summary(self, destination: str, ranked: list[dict[str, Any]]) -> str:
        if not ranked:
            return f"No accommodation options could be generated for {destination}."
        best = next((a for a in ranked if a["recommendation_type"] == "BEST_OVERALL"), ranked[0])
        return (
            f"{len(ranked)} accommodation option(s) ranked for {destination}. "
            f"Best overall: {best['property_name']} at {best['currency']} {best['nightly_price']}/night "
            f"(match {best['match_score']}). No live bookings have been made."
        )


accommodation_intelligence = AccommodationIntelligence()
