import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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


_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}

# A bare "I am <word>" must never turn an ordinary name into a passport
# country.  This allow-list is intentionally limited to nationality words
# the current visa rules can actually understand.
_KNOWN_NATIONALITIES = {
    "american",
    "british",
    "canadian",
    "emirati",
    "french",
    "ghanaian",
    "irish",
    "jamaican",
    "japanese",
    "nigerian",
    "south african",
    "spanish",
}


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
        "will it rain", "weather in", "weather like in", "what is the weather",
        "what's the weather", "climate in", "hurricane season",
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
        "plan a trip", "plan a holiday", "holiday to", "book a flight", "book flights", "fly to",
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

        # An explicit request to plan a trip must win over specialist details
        # mentioned inside the same brief.  For example, "Plan a 7-day trip ...
        # with weather information" previously matched WEATHER_ANALYSIS first
        # because "weather in" is a prefix of "weather information".  The
        # planner then returned only a weather card instead of assembling the
        # requested itinerary.
        explicit_plan = re.search(
            r"\bplan\s+(?:me\s+)?(?:a|an|my|our|the)\s+"
            r"(?:[a-z0-9-]+\s+){0,2}(?:trip|holiday)\b",
            text,
        )
        if explicit_plan:
            return ClassifiedIntent(
                intent=Intent.PLAN_TRIP,
                confidence=0.95,
                entities=self._extract_entities(text),
            )

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

        standalone_year = re.fullmatch(
            r"(?:the\s+year\s+is\s+|use\s+)?(20\d{2})[.!]?",
            text,
        )
        if standalone_year:
            entities["travel_year"] = standalone_year.group(1)
            entities["year_explicit"] = "true"

        # Preserve a traveller's explicitly flexible departure choice before
        # looking for generic "travelling from" phrases.  A later phrase such
        # as "my girlfriend is travelling from the US" describes a companion,
        # not the main traveller's origin.
        either_origin_match = re.search(
            r"\bfrom\s+either\s+([a-z][a-z .'-]{1,40}?)\s+or\s+"
            r"([a-z][a-z .'-]{1,40}?)(?=\s+on\b|,|[.!?]|$)",
            text,
        )
        if either_origin_match:
            options = [value.strip().title() for value in either_origin_match.groups()]
            entities["departure_options"] = ",".join(options)
            entities["origin"] = options[0]

        companion_match = re.search(
            r"\b(?:my\s+)?(girlfriend|boyfriend|partner|wife|husband|friend)"
            r"(?:,?\s+who\s+is|\s+is)?\s+"
            r"(?:travelling|traveling|flying)\s+from\s+(?:the\s+)?"
            r"([a-z][a-z .'-]{1,35}?)(?=\s+to\b|,|[.!?]|$)",
            text,
        )
        if companion_match:
            relationship, companion_origin = companion_match.groups()
            entities["companion_relationship"] = relationship.title()
            companion_origin = companion_origin.strip()
            entities["companion_origin"] = (
                "United States"
                if companion_origin in {"us", "u.s.", "usa", "u.s.a."}
                else companion_origin.title()
            )

        if "origin" not in entities:
            origin_match = re.search(
                r"\b(?:travelling|traveling|flying|departing|leaving)\s+from\s+"
                r"([a-z][a-z .'-]{1,40}?)(?=,|[.!?]|\s+(?:and|but|with|on|for|from|we|i|so)\b|$)",
                text,
            )
            if origin_match:
                entities["origin"] = origin_match.group(1).strip().title()

        if "origin" not in entities:
            simple_origin_match = re.search(
                r"\bfrom\s+([a-z][a-z .'-]{1,40}?)"
                r"(?=\s+(?:in|on|for|from|to|with)\b|,|[.!?]|$)",
                text,
            )
            if simple_origin_match:
                entities["origin"] = simple_origin_match.group(1).strip().title()

        flexible_origin_match = re.search(
            r"\b(?:do not mind|don't mind|can|could|happy to|willing to|flexible about)\s+"
            r"(?:fly(?:ing)?|depart(?:ing)?|leave|leaving)\s+from\s+"
            r"(.+?)(?=[.!?]|$)",
            text,
        )
        if flexible_origin_match:
            options = [
                value.strip(" ,").title()
                for value in re.split(r",|\s+or\s+|\s+and\s+", flexible_origin_match.group(1))
                if value.strip(" ,")
            ]
            if options:
                if entities.get("origin") and entities["origin"] not in options:
                    entities["home_origin"] = entities["origin"]
                entities["departure_options"] = ",".join(options)
                # A named airport/city option is actionable for flight search;
                # the traveller's home city is retained separately above.
                entities["origin"] = options[0]

        adults_match = re.search(
            rf"\b(\d+|{'|'.join(_NUMBER_WORDS)})\s+"
            rf"(?:(?:{'|'.join(sorted(_KNOWN_NATIONALITIES, key=len, reverse=True))})\s+)?"
            r"adults?\b",
            text,
        )
        if adults_match:
            raw_adults = adults_match.group(1)
            entities["adults"] = str(
                int(raw_adults) if raw_adults.isdigit() else _NUMBER_WORDS[raw_adults]
            )
        if not adults_match:
            friends_match = re.search(
                rf"\b(?:me|i)\s+and\s+my\s+"
                rf"(\d+|{'|'.join(_NUMBER_WORDS)})\s+friends?\b",
                text,
            )
            if friends_match:
                raw_friends = friends_match.group(1)
                friend_count = (
                    int(raw_friends)
                    if raw_friends.isdigit()
                    else _NUMBER_WORDS[raw_friends]
                )
                entities["adults"] = str(friend_count + 1)
        if "adults" not in entities:
            reverse_friends_match = re.search(
                rf"\b(\d+|{'|'.join(_NUMBER_WORDS)})\s+friends?\s+and\s+(?:me|i)\b",
                text,
            )
            if reverse_friends_match:
                raw_friends = reverse_friends_match.group(1)
                friend_count = (
                    int(raw_friends)
                    if raw_friends.isdigit()
                    else _NUMBER_WORDS[raw_friends]
                )
                entities["adults"] = str(friend_count + 1)
        if "adults" not in entities and (
            "with my partner" in text
            or "with my partners" in text
            or re.search(r"\bwe (?:are|'re) both\b", text)
            or re.search(
                r"\b(?:my\s+)?(?:wife|husband|partner|girlfriend|boyfriend)\s+and\s+i\b",
                text,
            )
            or re.search(
                r"\bi\s+and\s+my\s+(?:wife|husband|partner|girlfriend|boyfriend)\b",
                text,
            )
            or re.search(r"\b(?:as|for)\s+a\s+couple\b|\bwe (?:are|'re) a couple\b", text)
        ):
            entities["adults"] = "2"
        if "adults" not in entities and re.search(
            r"\b(?:travelling|traveling|going)\s+(?:alone|solo)\b"
            r"|\bsolo\s+(?:trip|holiday)\b|\bjust\s+me\b",
            text,
        ):
            entities["adults"] = "1"

        children_match = re.search(
            rf"\b(\d+|{'|'.join(_NUMBER_WORDS)})\s+"
            r"(?:children|child|kids?|young people)\b",
            text,
        )
        if children_match:
            raw_children = children_match.group(1)
            entities["children"] = str(
                int(raw_children)
                if raw_children.isdigit()
                else _NUMBER_WORDS[raw_children]
            )

        infants_match = re.search(
            rf"\b(\d+|{'|'.join(_NUMBER_WORDS)})\s+(?:infants?|bab(?:y|ies))\b",
            text,
        )
        if infants_match:
            raw_infants = infants_match.group(1)
            entities["infants"] = str(
                int(raw_infants)
                if raw_infants.isdigit()
                else _NUMBER_WORDS[raw_infants]
            )

        minor_ages = self._extract_minor_ages(text)
        if minor_ages:
            entities["minor_ages"] = ",".join(str(age) for age in minor_ages)
            inferred_infants = sum(age < 2 for age in minor_ages)
            inferred_children = len(minor_ages) - inferred_infants
            # Explicit ages are stronger than a generic child/infant label:
            # Duffel applies airline passenger rules from age, so keep the
            # two descriptive counts consistent with the supplied ages.
            entities["children"] = str(inferred_children)
            entities["infants"] = str(inferred_infants)

        cabin_patterns = (
            ("premium_economy", r"\bpremium[- ]economy(?:\s+(?:flights?|class|cabin))?\b"),
            (
                "business",
                r"\bbusiness(?:[- ]class|\s+(?:flights?|cabin))\b"
                r"|\b(?:fly|flying)\s+business\b",
            ),
            ("first", r"\bfirst[- ]class(?:\s+(?:flights?|cabin))?\b"),
            ("economy", r"\beconomy(?:[- ]class)?(?:\s+(?:flights?|cabin))?\b"),
        )
        for cabin_class, pattern in cabin_patterns:
            if re.search(pattern, text):
                entities["cabin_class"] = cabin_class
                break

        family_size_match = re.search(
            rf"\b(?:family|group|party)\s+of\s+"
            rf"(\d+|{'|'.join(_NUMBER_WORDS)})\b",
            text,
        )
        if family_size_match:
            raw_party_size = family_size_match.group(1)
            party_size = (
                int(raw_party_size)
                if raw_party_size.isdigit()
                else _NUMBER_WORDS[raw_party_size]
            )
            entities["party_size"] = str(party_size)
            if "adults" not in entities:
                dependants = int(entities.get("children", "0")) + int(
                    entities.get("infants", "0")
                )
                if party_size > dependants:
                    entities["adults"] = str(party_size - dependants)

        interests_match = re.search(
            r"\b(?:we|i)\s+(?:like|love|enjoy|are interested in|am interested in)\s+"
            r"(.+?)(?:[.!?]|$)",
            text,
        )
        if interests_match:
            raw_interests = [
                value.strip(" ,")
                for value in re.split(r",|\s+and\s+", interests_match.group(1))
                if value.strip(" ,")
            ]
            interests: list[str] = []
            for value in raw_interests:
                normalized = value.removeprefix("to ").strip()
                if "hotel" in normalized or "accommodation" in normalized:
                    continue
                if "dine out" in normalized:
                    normalized = "dining"
                elif "places of significant interest" in normalized:
                    normalized = "major attractions"
                interests.append(normalized)
            if interests:
                entities["interests"] = ",".join(interests)

        canonical_interests = (
            ("dining", ("dine out", "dining", "restaurants", "food")),
            ("fashion", ("fashion",)),
            ("soccer", ("soccer", "football match", "football game")),
            (
                "major attractions",
                (
                    "places of significant interest", "sightseeing", "landmarks",
                    "major attractions", "tourist attractions", "attractions",
                ),
            ),
            (
                "live events",
                (
                    "live events", "live event", "concerts", "concert",
                    "theatre shows", "theater shows",
                ),
            ),
        )
        interests = [
            value for value in entities.get("interests", "").split(",") if value
        ]
        for canonical, keywords in canonical_interests:
            already_represented = any(
                keyword in existing
                for existing in interests
                for keyword in keywords
            )
            if (
                any(keyword in text for keyword in keywords)
                and canonical not in interests
                and not already_represented
            ):
                interests.append(canonical)
        if "places of interest" in text and "local attractions" not in interests:
            interests.append("local attractions")
        if "ajax stadium" in text and "Ajax stadium" not in interests:
            interests.append("Ajax stadium")
        if (
            ("stadium" in text or re.search(r"\b[a-z]+\s+vs\.?\s+[a-z]+\b", text))
            and "soccer" not in interests
        ):
            interests.append("soccer")
        if interests:
            entities["interests"] = ",".join(interests)

        if re.search(r"\b(?:the\s+)?same\s+hotel\b", text):
            entities["accommodation_type"] = "HOTEL"
            entities["shared_hotel"] = "true"
            entities["accommodation_preference"] = "Same hotel for all travellers"

        if re.search(
            r"\b(?:child|children|kid|kids|family)[- ]friendly\s+hotel\b",
            text,
        ):
            entities["accommodation_type"] = "HOTEL"
            entities["accommodation_preference"] = "Child-friendly hotel"
        if re.search(
            r"\bnot\s+(?:too\s+)?far\s+from\s+(?:the\s+)?city\s+cent(?:re|er)\b"
            r"|\bnear\s+(?:the\s+)?city\s+cent(?:re|er)\b",
            text,
        ):
            entities["accommodation_location_preference"] = "Near Dublin city centre"

        additional_accommodation_preferences: list[str] = []
        accommodation_patterns = (
            ("Quiet room", r"\bquiet\s+(?:hotel|room)\b"),
            ("Boutique hotel", r"\bboutique\s+hotel\b"),
            ("Luxury hotel", r"\bluxury\s+hotel\b"),
            ("Beachfront hotel", r"\b(?:beachfront|beach-front)\s+hotel\b"),
            (
                "Wheelchair-accessible accommodation",
                r"\b(?:wheelchair[- ]accessible|step[- ]free|accessible)\s+"
                r"(?:hotel|room|accommodation)\b",
            ),
            ("Hotel with a pool", r"\bhotel\s+with\s+(?:a\s+)?pool\b"),
            (
                "Apartment accommodation",
                r"\b(?:stay\s+in\s+|book\s+)?(?:an?\s+)?apartment\b",
            ),
            ("Breakfast included", r"\bbreakfast\s+included\b"),
            ("Connecting rooms", r"\bconnecting\s+rooms?\b"),
        )
        for preference, pattern in accommodation_patterns:
            if re.search(pattern, text):
                additional_accommodation_preferences.append(preference)
        if additional_accommodation_preferences:
            entities["additional_accommodation_preferences"] = ",".join(
                additional_accommodation_preferences
            )

        if re.search(r"\bany\s+(?:london\s+)?airport\b", text):
            entities["airport_preference"] = (
                "Any London airport; prioritise a reasonable price"
                if entities.get("origin", "").casefold() == "london"
                else "Any suitable departure airport; prioritise a reasonable price"
            )

        requested_activities: list[str] = []
        if re.search(r"\b(?:guinness|gunness)\s+(?:factory|storehouse)\b", text):
            requested_activities.append("Guinness Storehouse")
        if "wicklow mountains" in text:
            requested_activities.append("Wicklow Mountains day trip")
        if "temple bar" in text and re.search(r"\b(?:meal|meals|restaurant|restaurants|dining)\b", text):
            requested_activities.append("Family meal near Temple Bar")
        if re.search(r"\bhop[- ]on\s+hop[- ]off\b", text):
            requested_activities.append("Dublin hop-on hop-off sightseeing tour")
        if (
            re.search(r"\b(?:various|other)\s+(?:tourist\s+)?attractions\b", text)
            or "list other attractions" in text
        ):
            requested_activities.append("Additional family-friendly Dublin attractions")

        generic_activity_pattern = re.compile(
            r"\b(?:visit|see|tour|explore)\s+(?:the\s+)?"
            r"([a-z0-9][a-z0-9 &'().-]{2,70}?)"
            r"(?=\s+(?:and\s+(?:also\s+)?(?:visit|see|tour|explore)\b|"
            r"for\s+(?:a|one)\s+day\b)|[,;.!?]|$)"
        )
        activity_aliases = {
            "gunness factory": "Guinness Storehouse",
            "guinness factory": "Guinness Storehouse",
            "ajax stadium": "Ajax stadium",
            "wicklow mountains": "Wicklow Mountains day trip",
        }
        for activity_match in generic_activity_pattern.finditer(text):
            candidate = activity_match.group(1).strip(" ,")
            if any(
                generic in candidate
                for generic in (
                    "tourist attraction", "various attraction", "other attraction",
                    "places of interest", "local area", "city centre", "city center",
                )
            ):
                continue
            canonical_activity = activity_aliases.get(candidate, candidate.title())
            if canonical_activity not in requested_activities:
                requested_activities.append(canonical_activity)
        if requested_activities:
            entities["requested_activities"] = ",".join(requested_activities)

        ticket_match = re.search(
            r"\b(?:a\s+)?tickets?\s+(?:to|for)\s+"
            r"([a-z][a-z .'-]{1,30}?)\s+vs\.?\s+"
            r"([a-z][a-z .'-]{1,30}?)(?=\s+(?:game|match)\b|[.,;!?]|$)",
            text,
        )
        match_request = ticket_match or re.search(
            r"\b([a-z][a-z.'-]*(?:\s+[a-z][a-z.'-]*){0,2})\s+vs\.?\s+"
            r"([a-z][a-z.'-]*(?:\s+[a-z][a-z.'-]*){0,2})"
            r"(?=\s+(?:game|match)\b|[.,;!?]|$)",
            text,
        )
        if match_request:
            home_team, away_team = (
                value.strip().title() for value in match_request.groups()
            )
            team_aliases = {
                "Feynold": "Feyenoord",
                "Feynoord": "Feyenoord",
                "Feyernoord": "Feyenoord",
            }
            away_team = team_aliases.get(away_team, away_team)
            entities["requested_event"] = f"{home_team} vs {away_team}"
            entities["requested_event_type"] = "Football match"
            entities["requested_event_status"] = "REQUESTED_NOT_CONFIRMED"
            if ticket_match:
                entities["ticket_requested"] = "true"

        traveller_nationality = re.search(
            r"\b(?:both\s+)?(?:travellers?|travelers?|passengers?)\s+"
            r"(?:are|'re)\s+([a-z]+)\s+(?:citizens?|nationals?|passport holders?)\b",
            text,
        )
        nationality_with_label = re.search(
            r"\b(?:we (?:are|'re)\s+)?(?:both\s+)?([a-z]+)\s+"
            r"(?:citizens?|nationals?|passport holders?)\b",
            text,
        )
        if traveller_nationality:
            nationality = traveller_nationality.group(1).title()
            entities["nationality"] = nationality
            entities["nationalities"] = nationality
        elif nationality_with_label:
            nationality = nationality_with_label.group(1).title()
            entities["nationality"] = nationality
            entities["nationalities"] = nationality
        else:
            group_nationality_match = re.search(
                r"\bwe are\s+([a-z]+)(?:\s+and\s+([a-z]+))?"
                r"(?=,|[.!?]|\s+citizens?\b)",
                text,
            )
            if group_nationality_match:
                nationalities = [
                    value.title()
                    for value in group_nationality_match.groups()
                    if value
                ]
                entities["nationality"] = nationalities[0]
                entities["nationalities"] = ",".join(nationalities)

        if "nationality" not in entities:
            described_adults = re.search(
                rf"\b(?:\d+|{'|'.join(_NUMBER_WORDS)})\s+"
                rf"({'|'.join(sorted(_KNOWN_NATIONALITIES, key=len, reverse=True))})\s+"
                r"adults?\b",
                text,
            )
            if described_adults:
                nationality = described_adults.group(1).title()
                entities["nationality"] = nationality
                entities["nationalities"] = nationality

        if re.search(r"\b(?:average|mid[- ]range|moderate)\s+hotel\b", text):
            entities["accommodation_type"] = "HOTEL"
            entities["budget_style"] = "balanced"
        elif re.search(r"\bbudget[- ]friendly\s+hotel\b", text):
            entities["accommodation_type"] = "HOTEL"
            entities["budget_style"] = "budget"

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
                    match = re.match(
                        r"([a-z][a-z.'-]*(?:\s+[a-z][a-z.'-]*){0,3})",
                        padded[idx + 4:],
                    )
                    if not match:
                        search_from = idx + 4
                        continue
                    words = match.group(1).split()
                    if not words:
                        break
                    stop_words = {
                        "and", "at", "for", "from", "in", "next", "on", "or",
                        "this", "until", "where", "with",
                    }
                    candidate_words = []
                    for word in words:
                        if word in stop_words:
                            break
                        candidate_words.append(word)
                    candidate = " ".join(candidate_words).strip(".,?!")
                    invalid_candidates = (
                        "the", "my", "a", "an", "be", "me", "do", "go", "is", "stay",
                        "visit", "travel", "plan", "fly", "book", "see", "explore",
                        "change", "modify", "update", "reschedule", "cancel", "move",
                    )
                    if (
                        len(candidate) > 2
                        and candidate not in invalid_candidates
                        and candidate_words[0] not in invalid_candidates
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
                match = re.match(
                    r"([a-z][a-z.'-]*(?:\s+[a-z][a-z.'-]*){0,3})",
                    padded[idx + len(marker) + 1:],
                )
                if match:
                    words = match.group(1).split()
                    stop_words = {
                        "and", "at", "for", "from", "in", "next", "on", "or",
                        "this", "until", "where", "with",
                    }
                    candidate_words = []
                    for word in words:
                        if word in stop_words:
                            break
                        candidate_words.append(word)
                    candidate = " ".join(candidate_words).strip(".,?!")
                    if len(candidate) > 2 and candidate not in (
                        "the", "my", "a", "an", "be", "me", "do", "go", "is", "stay", "visit",
                        "city centre", "the city centre", "city center", "the city center",
                    ):
                        entities["destination"] = candidate.title()
                        destination_found = True
                        break

        if not destination_found:
            visa_destination = re.search(
                r"\b(?:visa|entry requirements?)\s+(?:for|to)\s+(?:the\s+)?"
                r"([a-z][a-z.'-]*(?:\s+[a-z][a-z.'-]*){0,3})(?=[?.,!]|$)",
                text,
            )
            if visa_destination:
                entities["destination"] = visa_destination.group(1).title()

        local_areas: list[str] = []
        if re.search(r"\bst\.?\s+mary(?:'s)?\s+parish\b", text):
            local_areas.append("St Mary Parish")
        if re.search(r"\b(?:ocho\s+rios|ochi\s+rios|oshi\s+rius)\b", text):
            local_areas.append("Ocho Rios")
        if local_areas:
            entities["local_areas"] = ",".join(local_areas)

        if (
            entities.get("accommodation_location_preference")
            == "Near Dublin city centre"
            and entities.get("destination")
        ):
            entities["accommodation_location_preference"] = (
                f"Near {entities['destination']} city centre"
            )

        if "nationality" not in entities:
            nationality_statement = re.search(
                rf"\b(?:i am|i'm)\s+({'|'.join(sorted(_KNOWN_NATIONALITIES, key=len, reverse=True))})\b",
                text,
            )
            if nationality_statement:
                entities["nationality"] = nationality_statement.group(1).title()

        if "nationality" not in entities:
            bare_nationality = re.fullmatch(
                rf"(?:we\s+(?:are|'re)\s+)?"
                rf"({'|'.join(sorted(_KNOWN_NATIONALITIES, key=len, reverse=True))})"
                r"(?:\s+passports?)?[.!]?",
                text,
            )
            if bare_nationality:
                nationality = bare_nationality.group(1).title()
                entities["nationality"] = nationality
                entities["nationalities"] = nationality

        if "nationality" not in entities:
            idx = text.find(" passport")
            if idx != -1:
                before = text[:idx].split()
                if before:
                    candidate = before[-1].strip(".,?!")
                    if candidate not in ("my", "a", "the", "valid", "your", "our"):
                        entities["nationality"] = candidate.title()

        months = (
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december",
        )
        month_pattern = "|".join(months)
        duration_matches = list(re.finditer(
            rf"\b(a|an|\d{{1,2}}|{'|'.join(_NUMBER_WORDS)})\s*(?:-\s*)?"
            r"(days?|weeks?)\b",
            text,
        ))
        duration_matches = [
            match
            for match in duration_matches
            if not re.match(r"\s+trips?\b", text[match.end():])
            or re.match(r"\s+trip\b", text[match.end():]) is not None
        ]
        duration_matches = [
            match
            for match in duration_matches
            if not (
                re.search(r"\bin\s*$", text[:match.start()])
                and match.group(2).startswith("day")
            )
        ]
        if duration_matches:
            # A trip brief can contain an excursion length as well as the
            # overall holiday length: "5 days ... Wicklow Mountains for a
            # day".  When a numeric/number-word duration exists, an article-
            # based singular day is an activity duration, not a replacement
            # for the whole trip.  "a week ... 15 days" remains a genuine
            # conflicting trip-duration pair and is still surfaced.
            has_explicit_duration = any(
                match.group(1) not in {"a", "an"}
                for match in duration_matches
            )
            if has_explicit_duration:
                duration_matches = [
                    match
                    for match in duration_matches
                    if not (
                        match.group(1) in {"a", "an"}
                        and match.group(2).startswith("day")
                    )
                ]
            durations: list[int] = []
            for duration_match in duration_matches:
                raw_duration, unit = duration_match.groups()
                duration = (
                    1
                    if raw_duration in {"a", "an"}
                    else int(raw_duration)
                    if raw_duration.isdigit()
                    else _NUMBER_WORDS[raw_duration]
                )
                if unit.startswith("week"):
                    duration *= 7
                durations.append(duration)
            entities["duration_days"] = str(durations[-1])
            if len(set(durations)) > 1:
                entities["duration_conflict"] = (
                    f"Both {durations[0]} days and {durations[-1]} days were supplied; "
                    f"using the later {durations[-1]}-day request."
                )
        elif re.search(r"\b(?:a\s+)?fortnight\b", text):
            entities["duration_days"] = "14"

        range_match = re.search(
            rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({month_pattern})(?:\s+(\d{{4}}))?"
            rf"\s+(?:to|until|-)+\s+(\d{{1,2}})(?:st|nd|rd|th)?\s+"
            rf"({month_pattern})(?:\s+(\d{{4}}))?\b",
            text,
        )
        if range_match:
            start_day, start_month, start_year, end_day, end_month, end_year = (
                range_match.groups()
            )
            year = start_year or end_year
            if year:
                try:
                    start = datetime.strptime(
                        f"{start_day} {start_month} {year}", "%d %B %Y"
                    ).date()
                    end = datetime.strptime(
                        f"{end_day} {end_month} {end_year or year}", "%d %B %Y"
                    ).date()
                    if end > start:
                        entities["start_date"] = start.isoformat()
                        entities["end_date"] = end.isoformat()
                        entities["duration_days"] = str((end - start).days)
                        entities["date_hint"] = range_match.group(0)
                except ValueError:
                    pass

        # Natural trip briefs often state the outbound date first and the
        # return date in a later sentence rather than as "date to date".
        # Accept ordinal forms with "of" ("10th of October 2026") and
        # inherit the outbound year when the return sentence omits it.
        if "start_date" not in entities:
            outbound_match = re.search(
                rf"\b(?:the\s+)?(\d{{1,2}})(?:st|nd|rd|th)?(?:\s+of)?\s+"
                rf"({month_pattern})\s+(20\d{{2}})\b",
                text,
            )
            return_match = re.search(
                rf"\breturn\s+date\b.*?(?:the\s+)?(\d{{1,2}})"
                rf"(?:st|nd|rd|th)?(?:\s+of)?\s+({month_pattern})"
                rf"(?:\s+(20\d{{2}}))?\b",
                text,
            )
            if outbound_match:
                try:
                    start = datetime.strptime(
                        " ".join(outbound_match.groups()), "%d %B %Y"
                    ).date()
                    entities["start_date"] = start.isoformat()
                    entities["date_hint"] = outbound_match.group(0)
                    if return_match:
                        end_day, end_month, end_year = return_match.groups()
                        end = datetime.strptime(
                            f"{end_day} {end_month} {end_year or start.year}",
                            "%d %B %Y",
                        ).date()
                        if end > start:
                            entities["end_date"] = end.isoformat()
                            entities["duration_days"] = str((end - start).days)
                            entities["date_hint"] = (
                                f"{outbound_match.group(0)} to {return_match.group(0)}"
                            )
                    elif entities.get("duration_days"):
                        end = start + timedelta(days=int(entities["duration_days"]))
                        entities["end_date"] = end.isoformat()
                except ValueError:
                    pass

        # A dated trip that omits only the year uses the current calendar
        # year.  Preserve the inference explicitly so the UI can make it
        # visible and the traveller can correct it before any purchase.
        if "start_date" not in entities:
            day_without_year = re.search(
                rf"\b(?:on\s+)?(?:the\s+)?(\d{{1,2}})(?:st|nd|rd|th)?"
                rf"(?:\s+of)?\s+({month_pattern})\b(?!\s+20\d{{2}})",
                text,
            )
            if day_without_year:
                day, month_name = day_without_year.groups()
                inferred_year = datetime.now().year
                entities["departure_day"] = str(int(day))
                entities["month"] = str(months.index(month_name) + 1)
                entities["date_hint"] = f"{int(day)} {month_name.title()}"
                entities["travel_year"] = str(inferred_year)
                entities["date_year_inferred"] = "true"
                entities["date_inference_note"] = (
                    f"Year not supplied; using {inferred_year}."
                )
                try:
                    start = datetime.strptime(
                        f"{day} {month_name} {inferred_year}", "%d %B %Y"
                    ).date()
                    entities["start_date"] = start.isoformat()
                    if entities.get("duration_days"):
                        end = start + timedelta(days=int(entities["duration_days"]))
                        entities["end_date"] = end.isoformat()
                except ValueError:
                    pass

        # A single dated departure plus an explicit duration is also a
        # complete date range: "on 17 August 2026 for two weeks".
        if "start_date" not in entities:
            single_date_match = re.search(
                rf"\b(\d{{1,2}})(?:st|nd|rd|th)?(?:\s+of)?\s+"
                rf"({month_pattern})\s+(\d{{4}})\b",
                text,
            )
            if single_date_match:
                try:
                    start = datetime.strptime(
                        " ".join(single_date_match.groups()), "%d %B %Y"
                    ).date()
                    entities["start_date"] = start.isoformat()
                    entities["date_hint"] = single_date_match.group(0)
                    if entities.get("duration_days"):
                        end = start + timedelta(
                            days=int(entities["duration_days"])
                        )
                        entities["end_date"] = end.isoformat()
                except ValueError:
                    pass

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
        for i, name in enumerate(months, start=1):
            if f" {name} " in padded or f" {name}?" in padded or f" {name}." in padded:
                entities["month"] = str(i)
                # PLAN_TRIP completeness uses date_hint. A bare month also
                # appears inside explicit ranges such as "10 August to 17
                # August 2026", so preserve it as a usable date hint rather
                # than repeatedly asking the traveller for dates.
                entities.setdefault("date_hint", name)
                break

        month_year_match = re.search(
            rf"\b({month_pattern})\s+(20\d{{2}})\b",
            text,
        )
        if month_year_match and "start_date" not in entities:
            entities["month"] = str(months.index(month_year_match.group(1)) + 1)
            entities["travel_year"] = month_year_match.group(2)
            entities["date_hint"] = month_year_match.group(0)
            entities["date_precision"] = "MONTH"
        elif entities.get("start_date") and entities.get("end_date"):
            entities["date_precision"] = "EXACT"
        elif entities.get("month"):
            entities["date_precision"] = "MONTH"

        trip_year = (
            entities.get("start_date", "")[:4]
            or entities.get("travel_year")
        )

        birthday_match = re.search(
            rf"\bbirthday\b.*?(?:the\s+)?(\d{{1,2}})(?:st|nd|rd|th)?"
            rf"(?:\s+of)?\s+({month_pattern})(?:\s+(20\d{{2}}))?\b",
            text,
        )
        if birthday_match:
            day, month_name, explicit_year = birthday_match.groups()
            year = explicit_year or trip_year
            entities["special_occasion"] = "Birthday"
            if year:
                try:
                    occasion_date = datetime.strptime(
                        f"{day} {month_name} {year}", "%d %B %Y"
                    ).date()
                    entities["special_occasion_date"] = occasion_date.isoformat()
                except ValueError:
                    pass
            if "party with friends" in text:
                entities["special_occasion_notes"] = "Party with friends"

        checkout_match = re.search(
            rf"\buntil\s+(?:the\s+)?(\d{{1,2}})(?:st|nd|rd|th)?"
            rf"(?:\s+of)?\s+({month_pattern})(?:\s+(20\d{{2}}))?\b",
            text,
        )
        if "riu hotel" in text or "riu hotels" in text:
            entities["stay_1_property"] = "RIU Hotel"
            if "Ocho Rios" in local_areas:
                entities["stay_1_area"] = "Ocho Rios"
            if entities.get("start_date"):
                entities["stay_1_start_date"] = entities["start_date"]
            if checkout_match:
                checkout_day, checkout_month, checkout_year = checkout_match.groups()
                year = checkout_year or trip_year
                if year:
                    try:
                        checkout = datetime.strptime(
                            f"{checkout_day} {checkout_month} {year}", "%d %B %Y"
                        ).date()
                        entities["stay_1_end_date"] = checkout.isoformat()
                    except ValueError:
                        pass

        if re.search(r"\bbudget[- ]friendly\s+hotel\b", text):
            entities["stay_2_style"] = "Budget-friendly hotel"
            if "St Mary Parish" in local_areas:
                entities["stay_2_area"] = "St Mary Parish"
            if entities.get("stay_1_end_date"):
                entities["stay_2_start_date"] = entities["stay_1_end_date"]
            if entities.get("end_date"):
                entities["stay_2_end_date"] = entities["end_date"]

        budget_patterns = (
            (r"£\s*([\d,]+(?:\.\d{1,2})?)", "GBP"),
            (r"€\s*([\d,]+(?:\.\d{1,2})?)", "EUR"),
            (r"\$\s*([\d,]+(?:\.\d{1,2})?)", "USD"),
            (
                r"\b([\d,]+(?:\.\d{1,2})?)\s*"
                r"(?:pounds?|gbp)\b",
                "GBP",
            ),
            (
                r"\b([\d,]+(?:\.\d{1,2})?)\s*"
                r"(?:euros?|eur)\b",
                "EUR",
            ),
            (
                r"\b([\d,]+(?:\.\d{1,2})?)\s*"
                r"(?:dollars?|usd)\b",
                "USD",
            ),
        )
        for pattern, currency in budget_patterns:
            match = re.search(pattern, text)
            if not match:
                continue
            amount = match.group(1).replace(",", "")
            try:
                parsed = float(amount)
            except ValueError:
                continue
            if parsed > 0:
                entities["budget_amount"] = (
                    str(int(parsed)) if parsed.is_integer() else str(parsed)
                )
                entities["budget_currency"] = currency
                break

        negative_constraints: list[str] = []
        if re.search(r"\b(?:no alcohol|alcohol[- ]free|avoid alcohol)\b", text):
            negative_constraints.append("No alcohol")
        if re.search(r"\b(?:no nightlife|avoid nightlife)\b", text):
            negative_constraints.append("No nightlife")
        if negative_constraints:
            entities["negative_constraints"] = ",".join(negative_constraints)

        dietary_requirements: list[str] = []
        dietary_patterns = {
            "Halal": r"\bhalal\b",
            "Kosher": r"\bkosher\b",
            "Vegetarian": r"\bvegetarian\b",
            "Vegan": r"\bvegan\b",
            "Gluten-free": r"\bgluten[- ]free\b",
            "Nut allergy": r"\b(?:nut|peanut)\s+allerg(?:y|ies|ic)\b",
        }
        for label, pattern in dietary_patterns.items():
            if re.search(pattern, text):
                dietary_requirements.append(label)
        if dietary_requirements:
            entities["dietary_requirements"] = ",".join(dietary_requirements)

        return entities

    @staticmethod
    def _extract_minor_ages(text: str) -> list[int]:
        """Extract explicitly supplied under-18 ages without guessing.

        Covers natural planner wording ("children aged 6 and 9"), a
        clarification reply ("their ages are 6 and 9"), and individual
        descriptions ("a 6-year-old and a 10-year-old"). Adult ages are
        never inferred from unrelated numbers.
        """
        age_values: list[int] = []
        labelled = re.search(
            r"\b(?:(?:children|child|kids?|infants?|bab(?:y|ies)|their|children'?s|kids'?)\s+)"
            r"(?:(?:are|will\s+be)\s+)?(?:aged?|ages?)\s*(?:are|is|:)?\s*"
            r"(\d{1,2}(?:(?:\s*,\s*and\s+|\s*,\s*|\s+and\s+)\d{1,2})*)"
            r"(?=\s*(?:[,.;!?]|\b(?:departing|returning|travelling|traveling|with|we\s+want)\b|$))",
            text,
        )
        if labelled:
            age_values.extend(
                int(value)
                for value in re.findall(r"\b\d{1,2}\b", labelled.group(1))
            )

        if not age_values:
            for match in re.finditer(r"\b(\d{1,2})[- ]year[- ]old\b", text):
                age_values.append(int(match.group(1)))

        return [age for age in age_values if 0 <= age <= 17]
