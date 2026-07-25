"""
Module Selection — "Determine Required Intelligence Modules", the one
genuinely new decision Trip Brain introduces
(docs/TRIP_BRAIN_ARCHITECTURE.md's Decision Lifecycle).

A static, explainable mapping, not a model — consistent with every other
decision point in this codebase (IntentClassifier, DecisionEngine, and
every Discovery module's labelling algorithm are deterministic rule-based
logic, not ML). No scoring, no ranking — that stays inside each Discovery
module.

Each selected module is given a relevance weight, reused later by
confidence aggregation (docs/TRIP_BRAIN_ARCHITECTURE.md's Confidence
Propagation section): a module central to the request's core trip shape
(destination/weather always; flight/accommodation once dates are known)
weighs more than one pulled in as supporting context because a Goal
happens to carry a budget cap or the traveller's nationality needs
checking. When the request carries a full PLAN_TRIP shape (destination +
dates + party size), the architecture doc's table calls for all six core
modules. Event Intelligence is added only for an explicit event-shaped
interest.
"""

from __future__ import annotations

from ai.trip_brain.context import TripBrainContext

CORE_WEIGHT = 1.0
SUPPORTING_WEIGHT = 0.7

BASE_MODULES = ("destination", "flight", "accommodation", "budget", "visa", "weather")
ALL_MODULES = (*BASE_MODULES, "events")


class ModuleSelector:
    def select(self, context: TripBrainContext) -> dict[str, float]:
        weights: dict[str, float] = {}
        destination = context.destination

        if destination:
            weights["destination"] = CORE_WEIGHT
            weights["weather"] = CORE_WEIGHT
            if context.has_dates:
                weights["flight"] = CORE_WEIGHT
                weights["accommodation"] = CORE_WEIGHT

        if context.goal_has_budget_cap:
            weights.setdefault("budget", SUPPORTING_WEIGHT)

        if context.nationality_check_needed:
            weights.setdefault("visa", SUPPORTING_WEIGHT)

        if destination and context.has_dates and context.party_size_known:
            # Full PLAN_TRIP shape — orchestrate all six as core signals.
            for name in BASE_MODULES:
                weights[name] = CORE_WEIGHT

        if destination and context.has_event_interest:
            # Events are selected only for an explicit event-shaped interest.
            # A full trip does not silently add event searches for everyone.
            weights["events"] = CORE_WEIGHT

        return weights
