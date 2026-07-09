from __future__ import annotations

from typing import Any

from ai.discovery.destinations.destination_normalizer import destination_normalizer
from ai.discovery.destinations.destination_reasoner import destination_reasoner
from ai.discovery.destinations.destination_risk_assessor import destination_risk_assessor
from ai.discovery.destinations.destination_scorer import INTEREST_SCORE_FIELD, destination_scorer
from ai.discovery.destinations.mock_destination_provider import MockDestinationProvider

# Priority order in which "winner" labels are assigned — earlier categories
# take precedence so no option receives more than one label. See
# docs/DISCOVERY_LAYER_PATTERN.md for the general algorithm.
_PERSONA_TYPES = {
    "food": "BEST_FOR_FOOD",
    "football": "BEST_FOR_FOOTBALL",
    "culture": "BEST_FOR_CULTURE",
    "family": "BEST_FOR_FAMILY",
    "budget": "BEST_FOR_BUDGET",
    "photography": "BEST_FOR_PHOTOGRAPHY",
    "hidden_gem": "BEST_HIDDEN_GEM",
}
_AVOID_THRESHOLD = 0.35
_PERSONA_MIN_SCORE = 0.45


class DestinationIntelligence:
    """
    Orchestrates destination discovery: generate candidates -> normalize ->
    score -> explain -> assess risk -> rank -> label. Mirrors
    ai/discovery/flights/flight_intelligence.py's and
    ai/discovery/accommodation/accommodation_intelligence.py's role as the
    top-level orchestrator for its domain. See docs/DISCOVERY_LAYER_PATTERN.md.

    Two modes, matching MockDestinationProvider: a specific city returns the
    places *within* it; no city returns the best-fit cities across the whole
    catalogue.

    Sprint 1: MockDestinationProvider only. Sprint 4+: real
    DestinationProvider (Google Places or similar) behind the same search()
    interface; only the Normalizer changes.
    """

    def __init__(self, provider: MockDestinationProvider | None = None) -> None:
        self._provider = provider or MockDestinationProvider()

    def recommend(
        self,
        city: str | None = None,
        interests: list[str] | None = None,
        budget_style: str = "balanced",
        travel_month: int | None = None,
        trip_duration_days: int = 7,
        has_children: bool = False,
        profile: dict[str, Any] | None = None,
        goal: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        assumptions: list[str] = []
        interests = interests or []

        if city and city not in self._provider.cities():
            assumptions.append(
                f"'{city}' is not in the mock destination catalogue "
                f"({', '.join(self._provider.cities())}) — no options could be generated."
            )

        preferences = self._build_preferences(interests, budget_style, has_children, profile)

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
        if not travel_month:
            assumptions.append("No travel month supplied — season fit uses a neutral baseline.")

        raw_candidates = self._provider.search(city)
        normalized = [destination_normalizer.normalize(r, travel_month=travel_month) for r in raw_candidates]

        scored: list[dict[str, Any]] = []
        for dest in normalized:
            score_result = destination_scorer.score(dest, preferences, dna=dna, goal_type=goal_type)
            reasoning = destination_reasoner.explain(dest, score_result, preferences)
            risks = destination_risk_assessor.assess(dest)
            scored.append({
                **dest,
                "match_score": score_result["match_score"],
                "interests_matched": self._interests_matched(dest, interests),
                "reasoning": reasoning,
                "risks": risks,
                "assumptions": self._per_option_assumptions(dna, profile),
                "_persona_scores": score_result["persona_scores"],
            })

        ranked = sorted(scored, key=lambda d: d["match_score"], reverse=True)
        self._label_recommendation_types(ranked)

        for d in ranked:
            d.pop("_tags", None)
            d.pop("_popularity", None)
            d.pop("_persona_scores", None)

        assumptions.append(
            "Destination data is a deterministic mock catalogue — no live maps or places provider was queried."
        )

        mode = "city" if city else "catalogue"
        return {
            "destination_options": ranked,
            "assumptions": assumptions,
            "next_actions": self._next_actions(ranked, mode),
            "recommended_agents": ["experience_agent"],
            "summary": self._summary(city, ranked),
        }

    # ------------------------------------------------------------------

    def _build_preferences(
        self,
        interests: list[str],
        budget_style: str,
        has_children: bool,
        profile: dict[str, Any] | None,
    ) -> dict[str, Any]:
        prefs = (profile or {}).get("preferences", {})
        return {
            "interests": interests or prefs.get("travel_interests", []),
            "budget_style": budget_style,
            "has_children": has_children,
        }

    def _interests_matched(self, d: dict[str, Any], interests: list[str]) -> list[str]:
        matched: list[str] = []
        tags = set(d.get("_tags", []))
        for interest in interests:
            key = interest.lower()
            field = INTEREST_SCORE_FIELD.get(key)
            if (field and d[field] >= 0.6) or key in tags:
                matched.append(interest)
        return matched

    def _per_option_assumptions(
        self, dna: dict[str, Any] | None, profile: dict[str, Any] | None
    ) -> list[str]:
        a: list[str] = []
        if not profile:
            a.append("No traveller profile — default interest and budget assumptions applied.")
        if not dna:
            a.append("No Traveller DNA available — persona-based scoring skipped for this option.")
        return a

    def _label_recommendation_types(self, ranked: list[dict[str, Any]]) -> None:
        if not ranked:
            return

        labeled: dict[int, str] = {}

        avoid_idx = [i for i, d in enumerate(ranked) if d["match_score"] < _AVOID_THRESHOLD]
        for i in avoid_idx:
            labeled[i] = "AVOID"

        eligible = [i for i in range(len(ranked)) if i not in labeled]
        if eligible:
            best_overall = max(eligible, key=lambda i: ranked[i]["match_score"])
            labeled[best_overall] = "BEST_OVERALL"

        # A persona only claims a candidate if that candidate is genuinely
        # relevant to it — otherwise a destination with no football content
        # at all could still end up labelled BEST_FOR_FOOTBALL just because
        # it scored highest among a small, football-irrelevant pool. Skipped
        # personas simply go unclaimed here; any candidate left over still
        # gets a label via the guaranteed-coverage fallback below.
        for persona, rec_type in _PERSONA_TYPES.items():
            eligible = [i for i in range(len(ranked)) if i not in labeled]
            if not eligible:
                break
            best = max(eligible, key=lambda i: (ranked[i]["_persona_scores"][persona], -i))
            if ranked[best]["_persona_scores"][persona] < _PERSONA_MIN_SCORE:
                continue
            labeled[best] = rec_type

        # With exactly as many categories as candidates (e.g. a full 9-entry
        # city catalogue), a forced collision is possible if AVOID's
        # threshold never triggers. Resolve it the same way Accommodation
        # Intelligence does: the option that won no category at all is the
        # relative weakest of this set — label it AVOID rather than
        # duplicate another option's label. See ADR-012.
        remaining = [i for i in range(len(ranked)) if i not in labeled]
        if remaining and "AVOID" not in labeled.values():
            weakest = min(remaining, key=lambda i: ranked[i]["match_score"])
            labeled[weakest] = "AVOID"
            remaining.remove(weakest)

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

        for i, d in enumerate(ranked):
            d["recommendation_type"] = labeled[i]

    def _next_actions(self, ranked: list[dict[str, Any]], mode: str) -> list[str]:
        actions = ["Confirm opening hours and any booking requirements before visiting."]
        if mode == "catalogue":
            actions.append("Pick a city to see specific neighbourhoods, food areas, and attractions within it.")
        else:
            actions.append("Check current safety advisories for the destination.")
        actions.append("Destination data has not been checked live — details are indicative only.")
        return actions

    def _summary(self, city: str | None, ranked: list[dict[str, Any]]) -> str:
        if not ranked:
            scope = city or "your search"
            return f"No destination options could be generated for {scope}."
        best = next((d for d in ranked if d["recommendation_type"] == "BEST_OVERALL"), ranked[0])
        scope = f"within {city}" if city else "across the catalogue"
        return (
            f"{len(ranked)} destination option(s) ranked {scope}. "
            f"Best overall: {best['name']} (match {best['match_score']}). "
            f"No live bookings have been made."
        )


destination_intelligence = DestinationIntelligence()
