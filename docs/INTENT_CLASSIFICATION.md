# Intent Classification — Specification

## Overview

Every traveller message is classified into one of 8 intents before routing.
Classification determines which agent or handler processes the request.

**Sprint 1:** Rule-based keyword matching in `IntentClassifier`.
**Sprint 3+:** LLM-powered classification with confidence scores and multi-intent detection.

---

## Intent Catalogue

| Intent | Trigger | Handler |
|--------|---------|---------|
| `plan_trip` | Traveller wants to arrange travel | `ConversationEngine._handle_plan_trip()` |
| `modify_trip` | Traveller wants to change an existing trip | `ConversationEngine._dispatch()` → clarify |
| `view_profile` | Traveller wants to see their TIP | `ConversationEngine._dispatch()` → compose |
| `update_preferences` | Traveller wants to change preferences | `ConversationEngine._dispatch()` → compose |
| `ask_destination` | Traveller wants info about a place | `ConversationEngine._dispatch()` → compose |
| `travel_advice` | Traveller wants travel tips | `ConversationEngine._dispatch()` → compose |
| `budget_advice` | Traveller wants cost/budget help | `ConversationEngine._dispatch()` → compose |
| `general_conversation` | None of the above (fallback) | `ConversationEngine._dispatch()` → compose |

---

## Intent Detail

### plan_trip

The most important intent. Triggers the full trip-planning pipeline.

**Trigger patterns:**
```
plan a trip, book a flight, fly to, travel to, trip to,
visit, going to, i want to go, i need to be in, arrange a trip, journey to
```

**Required entities:** `destination`
**Optional entities:** `date_hint`
**Missing entity action:** Ask clarifying questions; set `pending_questions`.

**Example turns:**
- "I want to plan a trip to Lisbon"
- "Book me a flight to Lagos next month"
- "We're visiting Dubai this weekend"

---

### modify_trip

Traveller wants to change something about an existing booking or plan.

**Trigger patterns:**
```
change my trip, modify my trip, update my trip,
reschedule, cancel my trip, different hotel, move my flight,
change my flight, change my booking
```

**Sprint 1 behaviour:** Returns clarifying questions (no booking system yet).

---

### view_profile

Traveller wants to see the data stored in their Traveller Intelligence Profile.

**Trigger patterns:**
```
my profile, show profile, view profile,
my settings, my account, show my preferences
```

**Behaviour:** If `traveller_id` is on the session, fetches enriched TIP from
`TravellerIntelligenceService` and surfaces `preference_summary`.

---

### update_preferences

Traveller wants to change a preference (seat, cabin, meal, etc.).

**Trigger patterns:**
```
update my preferences, change my preferences,
i prefer, i now prefer, set my preference,
prefer window, prefer aisle
```

**Sprint 1 behaviour:** Asks traveller to use the profile ID to update via API.
**Sprint 3:** Live preference update via PATCH endpoint.

---

### ask_destination

Traveller wants information about a specific place.

**Trigger patterns:**
```
tell me about, what is it like, what's it like,
destination info, weather in, best places in,
what to do in, what to see in, how safe is
```

**Entity:** `destination` (extracted from message context).

---

### travel_advice

General travel tips or recommendations.

**Trigger patterns:**
```
travel advice, travel tips, tips for travelling,
recommend, suggest, should i visit, is it worth,
best time to visit, best time to go, worth visiting
```

---

### budget_advice

Questions about cost, pricing, or affordability.

**Trigger patterns:**
```
how much does it cost, how much will it cost, what does it cost,
travel budget, cheap flights, affordable hotels,
can i afford, price of, how expensive
```

---

### general_conversation

Default fallback when no other intent matches.

**Behaviour:** Returns a greeting / helpful prompt to guide the traveller.

---

## Entity Extraction

The classifier extracts two entity types from every message:

### `destination`

Extracted by scanning for positional markers (`to`, `in`, `visit`, `near`, `about`)
and taking the first non-stopword token that follows.

```
"I want to fly to Accra next month"  →  destination: "Accra"
"Tell me about Paris"                →  destination: "Paris"
```

Stopwords excluded: `the`, `my`, `a`, `an`, `be`, `me`, `do`, `go`, `is`

### `date_hint`

Matched against a fixed set of natural-language date expressions:

```
next week, next month, tomorrow, this weekend,
next friday, next saturday, in january … in december
```

---

## Confidence Scores

| Source | Score | Meaning |
|--------|-------|---------|
| Keyword match | 0.85 | Pattern found |
| Fallback | 1.00 | No pattern found; defaulting to general |

Sprint 3 will produce calibrated probabilities from the LLM classifier.

---

## Classification Pipeline

```
User message (raw text)
    │
    ▼
text.lower().strip()
    │
    ▼
Iterate _INTENT_PATTERNS (priority order)
    │
    ├─ Pattern found?  →  ClassifiedIntent(intent, confidence=0.85, entities)
    │
    └─ No match       →  ClassifiedIntent("general_conversation", confidence=1.0, entities)
    │
    ▼
_extract_entities(text)  →  {destination?, date_hint?}
```

---

## Sprint 3 Upgrade Path

The current `IntentClassifier` is a standalone class with a single public method:

```python
classifier.classify(message: str) -> ClassifiedIntent
```

The Sprint 3 LLM classifier will implement the same interface. No other code needs to change.
