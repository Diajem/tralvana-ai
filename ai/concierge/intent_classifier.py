from dataclasses import dataclass, field
from enum import Enum


class Intent(str, Enum):
    PLAN_TRIP = "PLAN_TRIP"
    FLIGHT_SEARCH = "FLIGHT_SEARCH"
    ACCOMMODATION_SEARCH = "ACCOMMODATION_SEARCH"
    DESTINATION_DISCOVERY = "DESTINATION_DISCOVERY"
    BUDGET_ANALYSIS = "BUDGET_ANALYSIS"
    VISA_CHECK = "VISA_CHECK"
    WEATHER_ANALYSIS = "WEATHER_ANALYSIS"
    MODIFY_TRIP = "MODIFY_TRIP"
    VIEW_PROFILE = "VIEW_PROFILE"
    UPDATE_PREFERENCES = "UPDATE_PREFERENCES"
    DESTINATION_QUESTION = "DESTINATION_QUESTION"
    TRAVEL_ADVICE = "TRAVEL_ADVICE"
    BUDGET_ADVICE = "BUDGET_ADVICE"
    EXPLAIN_RECOMMENDATION = "EXPLAIN_RECOMMENDATION"
    GENERAL_CONVERSATION = "GENERAL_CONVERSATION"


@dataclass
class ClassifiedIntent:
    intent: Intent
    confidence: float
    entities: dict[str, str] = field(default_factory=dict)


# Priority-ordered: first match wins.
_PATTERNS: list[tuple[Intent, list[str]]] = [
    (Intent.FLIGHT_SEARCH, [
        "recommend flights", "flight recommendations", "flight options",
        "search flights", "find flights", "find me a flight", "find me flights",
        "compare flights", "which flights", "best flights", "show me flights",
        "flights from", "rank flights", "flight search",
    ]),
    (Intent.ACCOMMODATION_SEARCH, [
        "recommend hotels", "recommend accommodation", "hotel recommendations",
        "hotel options", "accommodation options", "search hotels", "search accommodation",
        "find hotels", "find accommodation", "find me a hotel", "find me a place to stay",
        "compare hotels", "which hotels", "best hotels", "show me hotels",
        "where to stay", "places to stay", "hotel search",
    ]),
    (Intent.DESTINATION_DISCOVERY, [
        "recommend a destination", "recommend destinations", "destination recommendations",
        "where should i go", "where should i travel", "suggest a destination", "suggest destinations",
        "destination ideas", "help me choose a destination", "which city should i visit",
        "which destination", "explore destinations", "discover destinations", "things to do in",
    ]),
    (Intent.BUDGET_ANALYSIS, [
        "recommend a budget", "recommend budget options", "budget recommendations",
        "compare budget options", "budget plan for", "budget breakdown for",
        "which budget style", "rank budget options", "budget options for",
        "best budget for my trip", "optimise my budget", "optimize my budget", "budget tiers",
    ]),
    (Intent.VISA_CHECK, [
        "do i need a visa", "need a visa for", "visa requirements for", "visa required for",
        "can i enter", "will my passport", "passport work", "check my visa", "check visa",
        "visa check", "am i eligible to enter", "entry requirements for",
    ]),
    (Intent.WEATHER_ANALYSIS, [
        "good time to visit", "when should i visit", "when should i go",
        "will it rain", "weather in", "climate in", "hurricane season",
        "typhoon season", "rainy season", "best time to visit", "best time to go",
        "avoid hurricane", "avoid typhoon", "weather forecast for",
    ]),
    (Intent.EXPLAIN_RECOMMENDATION, [
        # Placed before PLAN_TRIP/TRAVEL_ADVICE/BUDGET_ADVICE — those
        # patterns are broad enough ("recommend", "how much") to otherwise
        # swallow a follow-up question about a recommendation just made.
        "why did you recommend", "why did you suggest", "why was this recommended",
        "why was that recommended", "why not the cheaper", "why not a cheaper",
        "why not cheaper", "what assumptions did you make", "what assumptions",
        "how confident are you", "how confident is that", "what would change your answer",
        "what would change the recommendation", "what would change your recommendation",
        "explain your recommendation", "explain this recommendation", "explain that recommendation",
        "explain your answer", "why this option", "why that option",
        "why did you pick", "why did you choose",
    ]),
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
        "best places in", "what to do in",
        "what to see in", "how safe is",
        "is it safe to travel to",
    ]),
    (Intent.TRAVEL_ADVICE, [
        "travel advice", "travel tips", "tips for travelling",
        "recommend", "suggest", "should i visit",
        "is it worth",
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

        entities = self._extract_entities(text)
        if entities.get("nationality") and entities.get("destination"):
            # A traveller stating both their nationality and a destination
            # with no other clear keyword pattern is a strong implicit
            # visa-check signal — nationality is not otherwise relevant to
            # any other intent in this conversation layer. E.g. "I am
            # Nigerian travelling to Spain."
            return ClassifiedIntent(intent=Intent.VISA_CHECK, confidence=0.7, entities=entities)

        return ClassifiedIntent(
            intent=Intent.GENERAL_CONVERSATION,
            confidence=1.0,
            entities=entities,
        )

    def _extract_entities(self, text: str) -> dict[str, str]:
        entities: dict[str, str] = {}

        # Padded so every marker search requires a leading word boundary —
        # without this, "in " matches inside "rain " (rendering "Will it
        # rain in Jamaica" destination-less) and similar false positives.
        padded = f" {text}"
        destination_found = False
        for marker in ("to ", "in ", "visit ", "near ", "about ", "enter "):
            if marker == "to ":
                # "to " is ambiguous between a destination preposition
                # ("trip to Tokyo") and an infinitive marker inside an
                # auxiliary construction ("want to travel", "need to
                # fly", "plan to visit"). Taking the first occurrence
                # unconditionally misreads the auxiliary verb itself as
                # the destination ("I want to travel to Tokyo" -> "Travel").
                # Keep scanning subsequent " to " occurrences until one
                # yields a real candidate.
                search_from = 0
                while True:
                    idx = padded.find(" to ", search_from)
                    if idx == -1:
                        break
                    words = padded[idx + 4:].split()
                    if not words:
                        break
                    candidate = words[0].strip(".,?!")
                    if len(candidate) > 2 and candidate not in (
                        "the", "my", "a", "an", "be", "me", "do", "go", "is", "stay",
                        "visit", "travel", "plan", "fly", "book", "see", "explore",
                    ):
                        entities["destination"] = candidate.title()
                        destination_found = True
                        break
                    search_from = idx + 4
                if destination_found:
                    break
                continue

            idx = padded.find(f" {marker}")
            if idx != -1:
                words = padded[idx + len(marker) + 1:].split()
                if words:
                    candidate = words[0].strip(".,?!")
                    if len(candidate) > 2 and candidate not in (
                        "the", "my", "a", "an", "be", "me", "do", "go", "is", "stay", "visit"
                    ):
                        entities["destination"] = candidate.title()
                        destination_found = True
                        break

        for marker in ("i am ", "i'm "):
            idx = text.find(marker)
            if idx != -1:
                words = text[idx + len(marker):].split()
                if words:
                    candidate = words[0].strip(".,?!")
                    if candidate not in ("a", "an", "the", "going", "travelling", "planning", "not"):
                        entities["nationality"] = candidate.title()
                        break

        if "nationality" not in entities:
            idx = text.find(" passport")
            if idx != -1:
                before = text[:idx].split()
                if before:
                    candidate = before[-1].strip(".,?!")
                    if candidate not in ("my", "a", "the", "valid", "your", "our"):
                        entities["nationality"] = candidate.title()

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

        # A bare month name anywhere in the message (not just "in <month>")
        # — e.g. "Is July a good time to visit Japan?". Padding with spaces
        # lets a month at the very start/end of the message still match as
        # a whole word.
        padded = f" {text} "
        for i, name in enumerate((
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december",
        ), start=1):
            if f" {name} " in padded or f" {name}?" in padded or f" {name}." in padded:
                entities["month"] = str(i)
                # PLAN_TRIP completeness uses date_hint. A bare month also
                # appears inside explicit ranges such as "10 August to 17
                # August 2026", so preserve it as a usable date hint rather
                # than repeatedly asking the traveller for dates.
                entities.setdefault("date_hint", name)
                break

        return entities
