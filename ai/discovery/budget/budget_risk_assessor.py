from __future__ import annotations

from typing import Any

_LOW_CERTAINTY_SCORE = 0.65
_HIGH_ABSOLUTE_COST_USD = 5000
_LONG_DURATION_DAYS = 21


class BudgetRiskAssessor:
    """
    Deterministic risk flags for a single normalized budget option.

    Property-intrinsic only — no preferences parameter, matching the same
    pattern as ai/discovery/flights/flight_risk_assessor.py,
    ai/discovery/accommodation/accommodation_risk_assessor.py, and
    ai/discovery/destinations/destination_risk_assessor.py. Whether an
    option exceeds the *traveller's own* budget cap is a preference-
    dependent judgement, so that lives in BudgetScorer's cap_fit (and
    ultimately the AVOID label), not here. Sprint 4+: incorporate live
    currency-volatility and seasonal-pricing data once a real provider is
    wired in.
    """

    def assess(self, option: dict[str, Any]) -> list[str]:
        risks: list[str] = []
        o = option

        if o["cost_certainty_score"] < _LOW_CERTAINTY_SCORE:
            risks.append(
                f"{o['budget_style'].title()}-tier pricing has higher variability — "
                "actual spend may differ more than usual from this estimate."
            )

        if o["total_cost_usd"] > _HIGH_ABSOLUTE_COST_USD:
            risks.append(
                "High absolute trip cost — consider price monitoring or a flexible cancellation policy."
            )

        if o["budget_style"] == "backpacker":
            risks.append(
                "Backpacker-tier estimates assume hostel-level accommodation and informal local "
                "transport — actual availability varies by destination."
            )

        if o["duration_days"] > _LONG_DURATION_DAYS:
            risks.append(
                f"{o['duration_days']}-day trip increases exposure to currency fluctuation "
                "and price drift over the course of the trip."
            )

        if o["children"] > 0 and o["budget_style"] == "backpacker":
            risks.append(
                "Backpacker-tier accommodation and transport may not suit young children — "
                "consider a higher tier."
            )

        return risks


budget_risk_assessor = BudgetRiskAssessor()
