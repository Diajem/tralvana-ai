"""
GoalClassifier — infers GoalType from free-text or interest lists.

Sprint 1: keyword pattern matching (deterministic, no external APIs).
Sprint 3+: replace with LLM-powered zero-shot classifier.
"""
from __future__ import annotations

# Priority-ordered: first match wins
_TEXT_PATTERNS: list[tuple[str, list[str]]] = [
    ("PILGRIMAGE",      ["pilgrimage", "hajj", "umrah", "holy", "shrine", "sacred", "jerusalem", "mecca", "medina"]),
    ("FOOTBALL_TRAVEL", ["football", "soccer", "match", "stadium", "premier league", "la liga", "serie a", "bundesliga", "champions league", "world cup"]),
    ("DIASPORA_TRAVEL", ["diaspora", "heritage", "homeland", "roots", "ancestral", "ancestry", "home country", "visit family", "back home"]),
    ("ROMANTIC_TRIP",   ["honeymoon", "romantic", "anniversary", "couple", "partner", "valentine", "propose", "engagement"]),
    ("FAMILY_TRIP",     ["family", "kids", "children", "baby", "toddler", "school holiday", "half term", "parents"]),
    ("ADVENTURE",       ["adventure", "hiking", "trekking", "safari", "extreme", "bungee", "skydive", "rafting", "climbing", "kayak", "scuba", "dive"]),
    ("FOOD_TOUR",       ["food", "cuisine", "restaurant", "culinary", "wine", "gastronomy", "michelin", "street food", "eat", "tasting"]),
    ("PHOTOGRAPHY",     ["photography", "photo", "camera", "shoot", "landscape", "wildlife photography", "portrait"]),
    ("BUSINESS_TRAVEL", ["business", "conference", "meeting", "networking", "summit", "trade show", "work trip", "client visit"]),
    ("RELAXATION",      ["relax", "spa", "wellness", "beach", "rest", "chill", "unwind", "retreat", "yoga", "meditation", "resort"]),
]

_INTEREST_PATTERNS: dict[str, str] = {
    "religious": "PILGRIMAGE",
    "pilgrimage": "PILGRIMAGE",
    "spiritual": "PILGRIMAGE",
    "sport": "FOOTBALL_TRAVEL",
    "heritage": "DIASPORA_TRAVEL",
    "diaspora": "DIASPORA_TRAVEL",
    "food_drink": "FOOD_TOUR",
    "photography": "PHOTOGRAPHY",
    "wellness": "RELAXATION",
    "beach": "RELAXATION",
    "adventure": "ADVENTURE",
    "nature": "ADVENTURE",
    "business": "BUSINESS_TRAVEL",
    "family": "FAMILY_TRIP",
}


class GoalClassifier:
    """
    Classifies user intent as a GoalType.

    Two modes:
    - classify_from_text(text): for raw conversation messages
    - classify_from_interests(interests): for TIP interest lists
    """

    def classify_from_text(self, text: str) -> str:
        lower = text.lower()
        for goal_type, keywords in _TEXT_PATTERNS:
            if any(kw in lower for kw in keywords):
                return goal_type
        return "GENERAL_TRAVEL"

    def classify_from_interests(self, interests: list[str]) -> str:
        for interest in interests:
            mapped = _INTEREST_PATTERNS.get(interest.lower())
            if mapped:
                return mapped
        return "GENERAL_TRAVEL"

    def classify(self, text: str, interests: list[str] | None = None) -> str:
        result = self.classify_from_text(text)
        if result == "GENERAL_TRAVEL" and interests:
            result = self.classify_from_interests(interests)
        return result


goal_classifier = GoalClassifier()
