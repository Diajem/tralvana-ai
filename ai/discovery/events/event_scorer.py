from __future__ import annotations

from typing import Any


_SYNONYMS: dict[str, set[str]] = {
    "soccer": {"soccer", "football", "sport", "match"},
    "football": {"soccer", "football", "sport", "match"},
    "fashion": {"fashion", "style", "design", "shopping"},
    "dining": {"food", "dining", "restaurants", "festival"},
    "food": {"food", "dining", "restaurants", "festival"},
    "culture": {"culture", "music", "theatre", "art"},
    "major attractions": {"culture", "art", "theatre", "major attractions"},
}


class EventScorer:
    """Explainable interest-fit score; no date or availability is invented."""

    def score(self, event: dict[str, Any], interests: list[str]) -> dict[str, Any]:
        tags = set(event.get("_tags", []))
        matched: list[str] = []
        for interest in interests:
            key = interest.lower()
            candidates = _SYNONYMS.get(key, {key})
            if candidates & tags:
                matched.append(interest)

        if interests:
            interest_fit = len(matched) / len(interests)
        else:
            interest_fit = 0.5

        # Curated ideas and live listings with adverse provider statuses
        # cannot outrank a healthy dated listing merely on interest match.
        if event["date_status"] == "UNVERIFIED":
            evidence_fit = 0.35
        else:
            evidence_fit = {
                "CANCELLED": 0.0,
                "OFF_SALE": 0.2,
                "POSTPONED": 0.3,
                "RESCHEDULED": 0.6,
                "UNKNOWN": 0.75,
                "ON_SALE": 1.0,
            }.get(event.get("availability_status", "UNKNOWN"), 0.75)
        match_score = round((interest_fit * 0.75) + (evidence_fit * 0.25), 2)
        return {
            "match_score": min(max(match_score, 0.0), 1.0),
            "interest_fit": round(interest_fit, 2),
            "evidence_fit": evidence_fit,
            "interests_matched": matched,
        }


event_scorer = EventScorer()
