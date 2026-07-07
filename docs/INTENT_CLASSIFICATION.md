# Intent Classification — Specification

## Overview

Every traveller message is classified into one of 8 intents before routing.
Classification determines which specialist agents are invoked and whether
additional information is needed before proceeding.

**File:** `ai/concierge/intent_classifier.py`

**Sprint 1:** Rule-based keyword pattern matching.
**Sprint 3+:** LLM-powered classification with calibrated confidence scores.

---

## Intent Catalogue

| Intent | Enum Value | Description |
|--------|-----------|-------------|
| `PLAN_TRIP` | `Intent.PLAN_TRIP` | Traveller wants to arrange a trip |
| `MODIFY_TRIP` | `Intent.MODIFY_TRIP` | Traveller wants to change an existing trip |
| `VIEW_PROFILE` | `Intent.VIEW_PROFILE` | Traveller wants to see their TIP |
| `UPDATE_PREFERENCES` | `Intent.UPDATE_PREFERENCES` | Traveller wants to change preferences |
| `DESTINATION_QUESTION` | `Intent.DESTINATION_QUESTION` | Question about a specific place |
| `TRAVEL_ADVICE` | `Intent.TRAVEL_ADVICE` | General travel tips or recommendations |
| `BUDGET_ADVICE` | `Intent.BUDGET_ADVICE` | Questions about costs or budget |
| `GENERAL_CONVERSATION` | `Intent.GENERAL_CONVERSATION` | Fallback — no pattern matched |

---

## Intent Detail

### PLAN_TRIP

Triggers the full trip-planning pipeline. Requires `destination` entity.

**Keyword patterns:**
```
plan a trip, book a flight, book flights, fly to,
travel to, trip to, visit, going to,
i want to go, i need to travel, arrange a trip, journey to
```

**Required entities:** `destination`
**Optional entities:** `date_hint`

**If missing:** DecisionEngine sets `follow_up_questions` and engine returns a clarification.

**Agents dispatched:** `flight_agent`, `hotel_agent`, `budget_agent`, `experience_agent`, `visa_agent`

---

### MODIFY_TRIP

Traveller wants to change something about a planned or booked trip.

**Keyword patterns:**
```
change my trip, modify my trip, update my trip,
reschedule, cancel my trip, different hotel,
move my flight, change my flight, change my booking
```

**Agents dispatched:** `flight_agent`, `hotel_agent`

**Sprint 1 behaviour:** Returns structured clarification (booking system not yet live).

---

### VIEW_PROFILE

Traveller wants to see their stored Traveller Intelligence Profile (TIP).

**Keyword patterns:**
```
my profile, show profile, view profile,
my settings, my account, show my preferences,
what do you know about me
```

**Agents dispatched:** None — ResponseComposer renders profile from TravellerIntelligenceService.

---

### UPDATE_PREFERENCES

Traveller wants to update a stored preference (seat, cabin, meal, etc.).

**Keyword patterns:**
```
update my preferences, change my preferences,
i prefer, i now prefer, set my preference,
prefer window, prefer aisle, change my seat
```

**Agents dispatched:** None — Sprint 3 adds a PATCH preferences endpoint.

---

### DESTINATION_QUESTION

Traveller wants information about a specific location.

**Keyword patterns:**
```
tell me about, what is it like, what's it like,
weather in, best places in, what to do in,
what to see in, how safe is, visa requirements for,
is it safe to travel to
```

**Agents dispatched:** `experience_agent`

---

### TRAVEL_ADVICE

General travel tips or recommendations.

**Keyword patterns:**
```
travel advice, travel tips, tips for travelling,
recommend, suggest, should i visit,
is it worth, best time to visit, best time to go, worth visiting
```

**Agents dispatched:** `experience_agent`

---

### BUDGET_ADVICE

Questions about cost, price, or affordability.

**Keyword patterns:**
```
how much does it cost, how much will it cost, what does it cost,
travel budget, cheap flights, affordable hotels,
can i afford, price of, how expensive
```

**Agents dispatched:** `budget_agent`

---

### GENERAL_CONVERSATION

Default fallback when no pattern matches. Returns a greeting and helpful prompt.

**Agents dispatched:** None

---

## ClassifiedIntent

```python
@dataclass
class ClassifiedIntent:
    intent: Intent        # Enum value
    confidence: float     # 0.0 – 1.0
    entities: dict[str, str]  # Extracted named entities
```

**Confidence values in Sprint 1:**

| Source | Score |
|--------|-------|
| Keyword match found | 0.85 |
| No match (GENERAL_CONVERSATION fallback) | 1.0 |

Sprint 3 will produce calibrated probabilities from the LLM classifier.

---

## Entity Extraction

Two entity types extracted from every message:

### `destination`

Scans for positional markers (`to`, `in`, `visit`, `near`, `about`) and takes the first
non-stopword token following the marker.

```
"I want to fly to Accra"     → destination: "Accra"
"Tell me about Paris"        → destination: "Paris"
"What's it like in Lisbon"   → destination: "Lisbon"
```

Stopwords excluded: `the`, `my`, `a`, `an`, `be`, `me`, `do`, `go`, `is`

### `date_hint`

Matched against a fixed set of natural-language date expressions:

```
next week, next month, tomorrow, this weekend,
next friday, next saturday,
in january … in december
```

---

## Agent Dispatch Map

| Intent | Agents |
|--------|--------|
| `PLAN_TRIP` | flight, hotel, budget, experience, visa |
| `MODIFY_TRIP` | flight, hotel |
| `DESTINATION_QUESTION` | experience |
| `TRAVEL_ADVICE` | experience |
| `BUDGET_ADVICE` | budget |
| `VIEW_PROFILE` | (none) |
| `UPDATE_PREFERENCES` | (none) |
| `GENERAL_CONVERSATION` | (none) |

---

## Sprint 3 Upgrade Path

`IntentClassifier` exposes a single public method:

```python
classifier.classify(message: str) -> ClassifiedIntent
```

The Sprint 3 LLM classifier implements the same interface.
No other code changes when the classifier is upgraded.
