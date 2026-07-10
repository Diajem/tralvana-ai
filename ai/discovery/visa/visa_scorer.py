from __future__ import annotations

from typing import Any

# Dimension weights — must sum to 1.0, same explainability convention as
# every other Discovery module's SCORE_WEIGHTS. Unlike Flight/Accommodation/
# Destination/Budget Intelligence, there is no traveller "preference" to
# match against here — a visa determination is an objective compliance fact
# about one passport/destination/purpose combination, not a matter of
# taste. VisaScorer therefore computes *confidence* in the assessment
# rather than a subjective match_score: how specific was the matched rule,
# how complete was the supplied data, how well-supported is the stated
# purpose, and how much transit complexity is involved.
SCORE_WEIGHTS: dict[str, float] = {
    "rule_specificity": 0.40,
    "data_completeness": 0.25,
    "purpose_clarity": 0.15,
    "transit_simplicity": 0.20,
}

_RULE_SPECIFICITY: dict[str, float] = {
    "override": 1.0, "same_country": 1.0, "tier": 0.75, "unknown": 0.15,
}
_PURPOSE_CLARITY: dict[str, float] = {
    "TOURISM": 1.0, "BUSINESS": 1.0, "TRANSIT": 0.8, "FAMILY_VISIT": 0.75,
    "STUDY": 0.6, "WORK": 0.6, "OTHER": 0.4,
}
_TRANSIT_STEP = 0.15
_TRANSIT_FLOOR = 0.3


class VisaScorer:
    """
    Deterministic 0.0-1.0 confidence scoring for a single visa assessment.
    Mirrors the other Discovery modules' scorer shape (weighted, explainable
    dimensions summing to 1.0) but scores confidence in the determination
    rather than fit against traveller preference — see SCORE_WEIGHTS above.
    """

    def score(self, option: dict[str, Any]) -> dict[str, Any]:
        breakdown = {
            "rule_specificity": _RULE_SPECIFICITY.get(option["matched_type"], 0.15),
            "data_completeness": self._data_completeness(option),
            "purpose_clarity": _PURPOSE_CLARITY.get(option["travel_purpose"], 0.4),
            "transit_simplicity": self._transit_simplicity(option),
        }

        confidence = round(
            sum(breakdown[k] * SCORE_WEIGHTS[k] for k in SCORE_WEIGHTS), 2
        )

        return {"confidence": confidence, "breakdown": breakdown}

    # ------------------------------------------------------------------

    def _data_completeness(self, option: dict[str, Any]) -> float:
        score = 0.5
        if option.get("passport_expiry_date"):
            score += 0.3
        if option.get("travel_purpose") != "OTHER":
            score += 0.2
        return round(min(score, 1.0), 2)

    def _transit_simplicity(self, option: dict[str, Any]) -> float:
        count = len(option.get("transit_countries", []))
        if count == 0:
            return 1.0
        return round(max(1.0 - count * _TRANSIT_STEP, _TRANSIT_FLOOR), 2)


visa_scorer = VisaScorer()
