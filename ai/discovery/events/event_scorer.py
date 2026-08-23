from __future__ import annotations

from typing import Any


_INTEREST_CONCEPTS: dict[str, set[str]] = {
    # Do not let the generic "sport" tag make basketball, baseball, or
    # wrestling look like a soccer match.
    "soccer": {"soccer", "football", "mls", "major league soccer"},
    "football": {"soccer", "football", "mls", "major league soccer"},
    "sport": {"sport", "sports"},
    "sports": {"sport", "sports"},
    "match": {"match", "soccer", "football"},
    "fashion": {"fashion", "style", "designer", "design", "runway", "couture"},
    "style": {"fashion", "style", "designer", "design", "runway", "couture"},
    "design": {"fashion", "style", "designer", "design", "runway", "couture"},
    "music": {"music", "concert"},
    "concert": {"music", "concert"},
    "festival": {"festival"},
    "theatre": {"theatre", "theater"},
    "theater": {"theatre", "theater"},
    "dining": {"food", "dining", "restaurant", "restaurants", "festival"},
    "food": {"food", "dining", "restaurant", "restaurants", "festival"},
    "culture": {"culture", "music", "theatre", "theater", "art"},
    "major attractions": {"culture", "art", "theatre", "theater"},
    "event": {"event"},
    "events": {"event"},
    "live event": {
        "event", "sport", "sports", "fashion", "style", "design", "music",
        "concert", "festival", "theatre", "theater", "food", "dining",
        "culture", "art",
    },
    "live events": {
        "event", "sport", "sports", "fashion", "style", "design", "music",
        "concert", "festival", "theatre", "theater", "food", "dining",
        "culture", "art",
    },
}

_CATEGORY_CONCEPTS: dict[str, set[str]] = {
    # SPORT is deliberately broad: the provider genre/name must establish
    # soccer or football specifically.
    "SPORT": {"sport", "sports"},
    "FASHION": {"fashion", "style", "design"},
    "MUSIC": {"music", "concert"},
    "CULTURE": {"culture", "theatre", "theater", "art"},
    "FOOD": {"food", "dining"},
}


def _interest_key(value: str) -> str:
    return " ".join(value.lower().strip().split())


class EventScorer:
    """Explainable category-aware relevance score.

    A close match to any stated event interest is useful even when the
    traveller also supplied several non-event preferences. This avoids the
    old behaviour where a soccer listing matched only 1/4 of a
    ``fashion, soccer, dining, attractions`` request and tied with unrelated
    listings.
    """

    def score(self, event: dict[str, Any], interests: list[str]) -> dict[str, Any]:
        tags = {_interest_key(str(tag)) for tag in event.get("_tags", [])}
        matched: list[str] = []
        match_strengths: list[float] = []
        for interest in interests:
            key = _interest_key(interest)
            candidates = _INTEREST_CONCEPTS.get(key, {key})
            if candidates & tags:
                matched.append(interest)
                match_strengths.append(1.0)

        if interests:
            # Rank a strong match to one explicit interest highly instead of
            # diluting it by unrelated preferences in the same trip request.
            interest_fit = max(match_strengths, default=0.0)
        else:
            interest_fit = 0.5

        category = str(event.get("category", "OTHER")).upper()
        category_terms = _CATEGORY_CONCEPTS.get(category, set())
        requested_keys = {_interest_key(interest) for interest in interests}
        category_fit = 1.0 if category_terms & requested_keys else 0.5
        if interests and not matched and category_fit < 1.0:
            category_fit = 0.0

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
        match_score = round(
            (interest_fit * 0.65) + (category_fit * 0.15) + (evidence_fit * 0.20),
            2,
        )
        team_level = str(event.get("team_level", "UNSPECIFIED")).upper()
        matched_keys = {_interest_key(value) for value in matched}
        reserve_or_youth_penalty = (
            0.15
            if team_level == "RESERVE_OR_YOUTH"
            and matched_keys & {"soccer", "football", "match"}
            else 0.0
        )
        match_score = round(match_score - reserve_or_youth_penalty, 2)
        return {
            "match_score": min(max(match_score, 0.0), 1.0),
            "interest_fit": round(interest_fit, 2),
            "category_fit": round(category_fit, 2),
            "evidence_fit": evidence_fit,
            "team_level_fit": round(1.0 - reserve_or_youth_penalty, 2),
            "interests_matched": matched,
            "is_relevant": not interests or bool(matched) or category_fit == 1.0,
        }


event_scorer = EventScorer()
