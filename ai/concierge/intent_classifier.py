from dataclasses import dataclass, field
from enum import Enum


class Intent(str, Enum):
    PLAN_TRIP = "PLAN_TRIP"
    MODIFY_TRIP = "MODIFY_TRIP"
    VIEW_PROFILE = "VIEW_PROFILE"
    UPDATE_PREFERENCES = "UPDATE_PREFERENCES"
    DESTINATION_QUESTION = "DESTINATION_QUESTION"
    TRAVEL_ADVICE = "TRAVEL_ADVICE"
    BUDGET_ADVICE = "BUDGET_ADVICE"
    GENERAL_CONVERSATION = "GENERAL_CONVERSATION"


@dataclass
class ClassifiedIntent:
    intent: Intent
    confidence: float
    entities: dict[str, str] = field(default_factory=dict)


# Priority-ordered: first match wins.
_PATTERNS: list[tuple[Intent, list[str]]] = [
    (Intent.PLAN_TRIP, [
        "plan a trip", "book a flight", "book flights", "fly to",
        "travel to", "trip to", "visit", "going to",
        "i want to go", "i need to travel", "arrange a trip", "journey to",
    ]),
    (Intent.MODIFY_TRIP, [
        "change my trip", "modify my trip", "update my trip",
        "reschedule", "cancel my trip", "different hotel",
        "move my flight", "change my flight", "change my booking",
    ]),
    (Intent.VIEW_PROFILE, [
        "my profile", "show profile", "view profile",
        "my settings", "my account", "show my preferences",
        "what do you know about me",
    ]),
    (Intent.UPDATE_PREFERENCES, [
        "update my preferences", "change my preferences",
        "i prefer", "i now prefer", "set my preference",
        "prefer window", "prefer aisle", "change my seat",
    ]),
    (Intent.DESTINATION_QUESTION, [
        "tell me about", "what is it like", "what's it like",
        "weather in", "best places in", "what to do in",
        "what to see in", "how safe is", "visa requirements for",
        "is it safe to travel to",
    ]),
    (Intent.TRAVEL_ADVICE, [
        "travel advice", "travel tips", "tips for travelling",
        "recommend", "suggest", "should i visit",
        "is it worth", "best time to visit", "best time to go",
        "worth visiting",
    ]),
    (Intent.BUDGET_ADVICE, [
        "how much does it cost", "how much will it cost", "what does it cost",
        "travel budget", "cheap flights", "affordable hotels",
        "can i afford", "price of", "how expensive",
    ]),
]


class IntentClassifier:
    """
    Rule-based intent classifier.

    Sprint 1: keyword pattern matching with entity extraction.
    Sprint 3+: replaced by LLM-powered classification with confidence calibration.
    """

    def classify(self, message: str) -> ClassifiedIntent:
        text = message.lower().strip()

        for intent, patterns in _PATTERNS:
            for pattern in patterns:
                if pattern in text:
                    return ClassifiedIntent(
                        intent=intent,
                        confidence=0.85,
                        entities=self._extract_entities(text),
                    )

        return ClassifiedIntent(
            intent=Intent.GENERAL_CONVERSATION,
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
            "next friday", "next saturday",
            "in january", "in february", "in march", "in april",
            "in may", "in june", "in july", "in august",
            "in september", "in october", "in november", "in december",
        ):
            if token in text:
                entities["date_hint"] = token
                break

        return entities
