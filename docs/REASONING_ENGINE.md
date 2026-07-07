# Reasoning Engine

The TravelOS Reasoning Engine is a collection of four specialist reasoners that derive structured travel intelligence from the Knowledge Graph. Reasoners are stateless services — each call is independent and returns a self-contained dict.

## Reasoners

### DestinationReasoner

Aggregates all graph knowledge about a city into a single structured summary.

```python
from knowledge.reasoning.destination_reasoner import destination_reasoner

result = destination_reasoner.reason(
    destination="London",
    traveller_profile={"preferences": {"budget_style": "luxury"}},
)
```

**Output keys:**

| Key | Description |
|-----|-------------|
| `destination_found` | Whether the city is in the graph |
| `city` | Name, timezone, descriptive tags |
| `country` | Name, ISO code, safety level, primary language |
| `currency` | Code, name, symbol |
| `airports` | List of airports serving the city |
| `recommended_hotels` | Hotels filtered by budget style (up to 3) |
| `top_attractions` | Up to 5 attractions |
| `museums` | Up to 3 museums |
| `football_clubs` | Football clubs based in the city |
| `events` | Up to 4 events/festivals |
| `local_transport` | Transport systems serving the city |
| `weather_overview` | Monthly weather records for the city |

---

### BudgetReasoner

Estimates total trip cost broken down by accommodation, food, activities, and flights.

```python
from knowledge.reasoning.budget_reasoner import budget_reasoner

result = budget_reasoner.reason(
    destination="Paris",
    duration_days=7,
    traveller_profile={"preferences": {"budget_style": "comfort", "cabin_class": "business"}},
)
```

**Output keys:**

| Key | Description |
|-----|-------------|
| `daily_estimate_usd` | Estimated daily spend |
| `daily_breakdown_usd` | Split: accommodation, food, activities, misc |
| `flight_estimate_usd` | Round-trip flight estimate |
| `flight_type` | short-haul / medium-haul / long-haul |
| `total_estimate_usd` | Full trip cost estimate |
| `total_estimate_range_usd` | Low (–15%) / High (+20%) confidence range |
| `confidence` | `medium` in Sprint 1 (no live data) |

Sprint 1 uses static regional daily rate tables by `budget_style` × `continent`. Sprint 3 will replace this with live pricing feeds.

---

### ExperienceReasoner

Matches traveller interests to experiences available at the destination using tag-based graph traversal.

```python
from knowledge.reasoning.experience_reasoner import experience_reasoner

result = experience_reasoner.reason(
    destination="Barcelona",
    traveller_profile={"preferences": {"travel_interests": ["sport", "food_drink", "culture"]}},
)
```

**Output keys:**

| Key | Description |
|-----|-------------|
| `matched_attractions` | Attractions ranked by interest tag overlap |
| `matched_museums` | Culture/history-focused museums |
| `matched_restaurants` | Restaurants filtered by budget tier |
| `events` | All events in the city |
| `football_clubs` | Shown when `sport` is an interest |
| `personalisation_note` | Human-readable summary of applied filters |
| `confidence` | 0.65 in Sprint 1 |

---

### TimelineReasoner

Advises on the best time to visit and what to expect in a given month.

```python
from knowledge.reasoning.timeline_reasoner import timeline_reasoner

result = timeline_reasoner.reason(
    destination="Dubai",
    travel_month=11,
    duration_days=10,
    traveller_profile={"preferences": {"travel_interests": ["beach", "luxury"]}},
)
```

**Output keys:**

| Key | Description |
|-----|-------------|
| `best_months` | Top 3 months scored by weather + events |
| `months_to_avoid` | Months flagged for extreme weather |
| `travel_month_snapshot` | Specific month weather + events if requested |
| `events_calendar` | All events sorted by month |
| `planning_tips` | Booking and logistics tips |
| `confidence` | 0.70 in Sprint 1 |

---

## Integration Pattern

Reasoners are consumed by specialist agents (`BudgetAgent`, `ExperienceAgent`, etc.), which add AI-layer reasoning on top of the structured graph output.

```python
# Inside BudgetAgent.execute()
from knowledge.reasoning.budget_reasoner import budget_reasoner

graph_data = budget_reasoner.reason(destination, duration_days, traveller_profile)
# Agent then wraps graph_data in AgentResult with confidence, assumptions, etc.
```

This separation means the Knowledge Graph can evolve independently of the agent layer.

## Sprint Roadmap

| Sprint | Improvement |
|--------|-------------|
| Sprint 1 | Static estimates + tag matching (current) |
| Sprint 2 | Add live flight/hotel prices; expand graph to 50+ cities |
| Sprint 3 | ML-ranked experience scoring; traveller-history personalisation |
| Sprint 4 | Graph DB migration; real-time graph updates via travel data feeds |
