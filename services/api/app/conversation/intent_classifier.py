from dataclasses import dataclass, field


@dataclass
class ClassifiedIntent:
    intent: str
    confidence: float
    entities: dict[str, str] = field(default_factory=dict)


# Priority-ordered: first match wins.
_INTENT_PATTERNS: list[tuple[str, list[str]]] = [
    ("plan_trip", [
        "plan a trip", "book a flight", "fly to", "travel to", "trip to",
        "visit", "going to", "i want to go", "i need to be in",
        "arrange a trip", "journey to",
    ]),
    ("modify_trip", [
        "change my trip", "modify my trip", "update my trip",
        "reschedule", "cancel my trip", "different hotel", "move my flight",
        "change my flight", "change my booking",
    ]),
    ("view_profile", [
        "my profile", "show profile", "view profile",
        "my settings", "my account", "show my preferences",
    ]),
    ("update_preferences", [
        "update my preferences", "change my preferences",
        "i prefer", "i now prefer", "set my preference",
        "prefer window", "prefer aisle",
    ]),
    ("ask_destination", [
        "tell me about", "what is it like", "what's it like",
        "destination info", "weather in", "best places in",
        "what to do in", "what to see in", "how safe is",
    ]),
    ("travel_advice", [
        "travel advice", "travel tips", "tips for travelling",
        "recommend", "suggest", "should i visit", "is it worth",
        "best time to visit", "best time to go", "worth visiting",
    ]),
    ("budget_advice", [
        "how much does it cost", "how much will it cost", "what does it cost",
        "travel budget", "cheap flights", "affordable hotels",
        "can i afford", "price of", "how expensive",
    ]),
]


class IntentClassifier:
    """
    Rule-based intent classifier for Sprint 1.
    Sprint 3+: replaced by LLM-powered classification via TravelConciergeAgent.
    """

    def classify(self, message: str) -> ClassifiedIntent:
        text = message.lower().strip()

        for intent_name, patterns in _INTENT_PATTERNS:
            for pattern in patterns:
                if pattern in text:
                    return ClassifiedIntent(
                        intent=intent_name,
                        confidence=0.85,
                        entities=self._extract_entities(text),
                    )

        return ClassifiedIntent(
            intent="general_conversation",
            confidence=1.0,
            entities=self._extract_entities(text),
        )

    def _extract_entities(self, text: str) -> dict[str, str]:
        entities: dict[str, str] = {}

        for marker in ("to ", "in ", "visit ", "near ", "about "):
            idx = text.find(marker)
            if idx != -1:
                words = text[idx + len(marker):].split()
                if words:
                    candidate = words[0].strip(".,?!")
                    if len(candidate) > 2 and candidate not in (
                        "the", "my", "a", "an", "be", "me", "do", "go", "is"
                    ):
                        entities["destination"] = candidate.title()
                        break

        for token in (
            "next week", "next month", "tomorrow", "this weekend",
            "next friday", "next saturday", "in january", "in february",
            "in march", "in april", "in may", "in june",
            "in july", "in august", "in september", "in october",
            "in november", "in december",
        ):
            if token in text:
                entities["date_hint"] = token
                break

        return entities
