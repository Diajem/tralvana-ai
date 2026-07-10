from __future__ import annotations

from typing import Any

from ai.discovery.budget.budget_normalizer import budget_normalizer
from ai.discovery.budget.budget_reasoner import budget_option_reasoner
from ai.discovery.budget.budget_risk_assessor import budget_risk_assessor
from ai.discovery.budget.budget_scorer import budget_scorer
from ai.discovery.budget.mock_budget_provider import MockBudgetProvider

# Priority order in which "winner" labels are assigned — earlier categories
# take precedence so no option receives more than one label. See
# docs/DISCOVERY_LAYER_PATTERN.md for the general algorithm.
_PERSONA_TYPES = {
    "value": "BEST_VALUE",
    "family": "BEST_FOR_FAMILY",
}
_AVOID_THRESHOLD = 0.35
_PERSONA_MIN_SCORE = 0.45


class BudgetIntelligence:
    """
    Orchestrates budget discovery: generate one candidate per budget style ->
    normalize -> score -> explain -> assess risk -> rank -> label. Mirrors
    ai/discovery/flights/flight_intelligence.py's and
    ai/discovery/destinations/destination_intelligence.py's role as the
    top-level orchestrator for its domain. See docs/DISCOVERY_LAYER_PATTERN.md.

    Unlike the other three Discovery modules, the candidate set here is
    always the five budget styles (backpacker/budget/balanced/comfort/luxury)
    for the given trip shape — the traveller compares tiers rather than
    provider inventory. Fourth Discovery Layer module (T-018), alongside
    Flight (T-015), Accommodation (T-016), and Destination (T-017) Intelligence.

    Sprint 1: MockBudgetProvider only, static regional rate tables. Sprint
    4+: real pricing feed behind the same search() interface; only the
    Normalizer changes.
    """

    def __init__(self, provider: MockBudgetProvider | None = None) -> None:
        self._provider = provider or MockBudgetProvider()

    def recommend(
        self,
        destination: str | None = None,
        duration_days: int = 7,
        adults: int = 1,
        children: int = 0,
        budget_style: str = "balanced",
        profile: dict[str, Any] | None = None,
        goal: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        assumptions: list[str] = []

        preferences = self._build_preferences(budget_style, children, profile, goal)
        if not preferences.get("budget_max_usd"):
            assumptions.append(
                "No goal budget cap supplied — cap-fit scoring uses a neutral baseline."
            )
        if not destination:
            assumptions.append(
                "No destination supplied — regional rates default to a global average band."
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

        raw_candidates = self._provider.search(destination, duration_days, adults, children)
        normalized = [budget_normalizer.normalize(r) for r in raw_candidates]

        scored: list[dict[str, Any]] = []
        for option in normalized:
            score_result = budget_scorer.score(option, preferences, dna=dna, goal_type=goal_type)
            reasoning = budget_option_reasoner.explain(option, score_result, preferences)
            risks = budget_risk_assessor.assess(option)
            scored.append({
                **option,
                "match_score": score_result["match_score"],
                "reasoning": reasoning,
                "risks": risks,
                "assumptions": self._per_option_assumptions(dna, profile),
                "_persona_scores": score_result["persona_scores"],
            })

        ranked = sorted(scored, key=lambda o: o["match_score"], reverse=True)
        self._label_recommendation_types(ranked)

        for o in ranked:
            o.pop("_persona_scores", None)

        assumptions.append(
            "Budget estimates are deterministic mock regional rates — no live pricing was queried."
        )

        return {
            "budget_options": ranked,
            "assumptions": assumptions,
            "next_actions": self._next_actions(ranked),
            "recommended_agents": ["budget_agent"],
            "summary": self._summary(destination, ranked),
        }

    # ------------------------------------------------------------------

    def _build_preferences(
        self,
        budget_style: str,
        children: int,
        profile: dict[str, Any] | None,
        goal: dict[str, Any] | None,
    ) -> dict[str, Any]:
        prefs = (profile or {}).get("preferences", {})
        budget = (goal or {}).get("budget") or {}
        return {
            "budget_style": budget_style or prefs.get("budget_style", "balanced"),
            "has_children": children > 0,
            "budget_min_usd": budget.get("min_usd"),
            "budget_max_usd": budget.get("max_usd"),
        }

    def _per_option_assumptions(
        self, dna: dict[str, Any] | None, profile: dict[str, Any] | None
    ) -> list[str]:
        a: list[str] = []
        if not profile:
            a.append("No traveller profile — default style and family assumptions applied.")
        if not dna:
            a.append("No Traveller DNA available — persona-based scoring skipped for this option.")
        return a

    def _label_recommendation_types(self, ranked: list[dict[str, Any]]) -> None:
        if not ranked:
            return

        labeled: dict[int, str] = {}

        avoid_idx = [i for i, o in enumerate(ranked) if o["match_score"] < _AVOID_THRESHOLD]
        for i in avoid_idx:
            labeled[i] = "AVOID"

        eligible = [i for i in range(len(ranked)) if i not in labeled]
        if eligible:
            best_overall = max(eligible, key=lambda i: ranked[i]["match_score"])
            labeled[best_overall] = "BEST_OVERALL"

        eligible = [i for i in range(len(ranked)) if i not in labeled]
        if eligible:
            lowest_cost = min(eligible, key=lambda i: ranked[i]["total_cost_usd"])
            labeled[lowest_cost] = "LOWEST_COST"

        eligible = [i for i in range(len(ranked)) if i not in labeled]
        if eligible:
            most_comfortable = max(eligible, key=lambda i: ranked[i]["comfort_score"])
            labeled[most_comfortable] = "MOST_COMFORTABLE"

        # A persona only claims a candidate if it's genuinely relevant —
        # same relevance floor as Destination Intelligence (ADR-013) so a
        # persona label is never forced onto a poorly-fitting option.
        for persona, rec_type in _PERSONA_TYPES.items():
            eligible = [i for i in range(len(ranked)) if i not in labeled]
            if not eligible:
                break
            best = max(eligible, key=lambda i: (ranked[i]["_persona_scores"][persona], -i))
            if ranked[best]["_persona_scores"][persona] < _PERSONA_MIN_SCORE:
                continue
            labeled[best] = rec_type

        # Guaranteed-coverage fallback, same approach as Flight/Accommodation/
        # Destination Intelligence: anything still unlabelled falls back to
        # its own best-fit persona so every option gets exactly one type.
        for i in range(len(ranked)):
            if i in labeled:
                continue
            scores = ranked[i]["_persona_scores"]
            persona = max(scores, key=lambda p: scores[p])
            labeled[i] = _PERSONA_TYPES[persona]

        for i, o in enumerate(ranked):
            o["recommendation_type"] = labeled[i]

    def _next_actions(self, ranked: list[dict[str, Any]]) -> list[str]:
        actions = [
            "Confirm your actual budget cap so cap-fit scoring is precise.",
            "Compare the top-ranked tier against live flight and accommodation pricing before booking.",
        ]
        if any(o["recommendation_type"] == "AVOID" for o in ranked):
            actions.append("Avoid-labelled tiers exceed the supplied budget cap — consider a leaner style.")
        actions.append("Budget data has not been checked live — figures are indicative only.")
        return actions

    def _summary(self, destination: str | None, ranked: list[dict[str, Any]]) -> str:
        if not ranked:
            return "No budget options could be generated."
        best = next((o for o in ranked if o["recommendation_type"] == "BEST_OVERALL"), ranked[0])
        scope = f"for {destination}" if destination else "for your trip"
        return (
            f"{len(ranked)} budget option(s) ranked {scope}. "
            f"Best overall: {best['budget_style'].title()} tier at "
            f"{best['currency']} {best['total_cost_usd']} (match {best['match_score']}). "
            f"No live pricing was queried."
        )


budget_intelligence = BudgetIntelligence()
