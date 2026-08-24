"""
GoalClassifier — infers GoalType from free-text or interest lists.

Sprint 1: keyword pattern matching (deterministic, no external APIs).
Sprint 3+: replace with LLM-powered zero-shot classifier.
"""
from __future__ import annotations

# Priority-ordered: first match wins
_TEXT_PATTERNS: list[tuple[str, list[str]]] = [
    ("PILGRIMAGE",      ["pilgrimage", "hajj", "umrah", "holy", "shrine", "sacred", "jerusalem", "mecca", "medina"]),
    # "family" by itself can describe people at the destination ("stay near
    # family") rather than children travelling in the party.  Use explicit
    # party language or child-related terms before selecting child-oriented
    # itinerary templates. Family composition takes priority over a football
    # or adventure interest so one adult's hobby does not reshape every day.
    ("FAMILY_TRIP",     ["family trip", "family holiday", "family vacation", "with my family", "with our family", "with my parents", "kids", "children", "baby", "toddler", "school holiday", "half term"]),
    ("FOOTBALL_TRAVEL", ["football", "soccer", "match", "stadium", "premier league", "la liga", "serie a", "bundesliga", "champions league", "world cup"]),
    ("DIASPORA_TRAVEL", ["diaspora", "heritage", "homeland", "roots", "ancestral", "ancestry", "home country", "visit family", "back home"]),
    # Travelling as a couple is party composition, not proof that the entire
    # trip should use a romance template.
    ("ROMANTIC_TRIP",   ["honeymoon", "romantic", "anniversary", "valentine", "propose", "proposal trip", "engagement trip"]),
    ("ADVENTURE",       ["adventure", "hiking", "trekking", "safari", "extreme", "bungee", "skydive", "rafting", "climbing", "kayak", "scuba", "dive"]),
    # Ordinary trips frequently mention restaurants. Select FOOD_TOUR only
    # when food is explicitly the focus of the journey.
    ("FOOD_TOUR",       ["food tour", "culinary trip", "culinary holiday", "gastronomy trip", "food-focused", "street food tour", "wine tour", "tasting tour"]),
    ("PHOTOGRAPHY",     ["photography", "photo", "camera", "shoot", "landscape", "wildlife photography", "portrait"]),
    # A social phrase such as "meeting my girlfriend" is not business travel.
    # Require a business/work/client qualifier instead of the bare word
    # "meeting".
    ("BUSINESS_TRAVEL", ["business", "conference", "business meeting", "work meeting", "client meeting", "networking", "summit", "trade show", "work trip", "client visit"]),
    # Bare "rest" appears in ordinary sequencing ("for the rest of the
    # trip") and must not turn the whole itinerary into a spa break.
    ("RELAXATION",      ["relax", "spa", "wellness", "beach", "rest and relaxation", "restful", "chill", "unwind", "retreat", "yoga", "meditation", "resort"]),
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
