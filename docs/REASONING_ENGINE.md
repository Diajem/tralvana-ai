# Reasoning Engine

The TravelOS Reasoning Engine consists of six specialist reasoning services. Each service answers a specific travel intelligence question using the Knowledge Graph. All services share a consistent interface and return a `ReasoningResult` struct.

## Consistent Interface

```python
from ai.intelligence.reasoning.base_reasoner import BaseReasoner, ReasoningResult

@dataclass
class ReasoningResult:
    reasoner_name: str
    subject: str        # destination city, traveller_id, etc.
    success: bool
    confidence: float   # 0.0–1.0
    data: dict[str, Any]
    assumptions: list[str]
    limitations: list[str]
    reasoning_source: str

class BaseReasoner(ABC):
    def reason(self, **kwargs) -> ReasoningResult: ...
```

Every reasoner accepts an optional `knowledge_service` for dependency injection. By default, all reasoners use the singleton from `ai.intelligence`.

---

## 1. DestinationReasoner

**Question:** "What do I need to know about [destination]?"

```python
from ai.intelligence.reasoning.destination_reasoner import destination_reasoner

result = destination_reasoner.reason("Barcelona", traveller_profile={...})
```

**Output data keys:** city, region, country, currency, airports, rail_stations, recommended_hotels (filtered by budget_style), top_attractions, museums, restaurants, football_clubs, sports_venues, events, local_transport, weather_overview

---

## 2. ExperienceReasoner

**Question:** "What should I do/eat/see in [destination] given my interests?"

```python
from ai.intelligence.reasoning.experience_reasoner import experience_reasoner

result = experience_reasoner.reason(
    "London",
    traveller_profile={"preferences": {"travel_interests": ["sport", "food_drink"]}}
)
```

**Output data keys:** interests_applied, matched_attractions (ranked by tag overlap), museums, restaurants (filtered by tier), events, football_clubs, sports_venues

---

## 3. BudgetReasoner

**Question:** "How much will a trip to [destination] cost me?"

```python
from ai.intelligence.reasoning.budget_reasoner import budget_reasoner

result = budget_reasoner.reason("Dubai", duration_days=10, traveller_profile={...})
```

**Output data keys:** daily_estimate_usd, daily_breakdown_usd (accommodation / food / activities / misc), flight_estimate_usd, flight_type, total_estimate_usd, total_range_usd (low / high)

Sprint 1: static regional tables by `budget_style` × `continent`. Sprint 3+: live pricing.

---

## 4. TimelineReasoner

**Question:** "When is the best time to visit [destination]?"

```python
from ai.intelligence.reasoning.timeline_reasoner import timeline_reasoner

result = timeline_reasoner.reason("Tokyo", travel_month=4, duration_days=10)
```

**Output data keys:** best_months (top 3 by weather score + events), months_to_avoid, travel_month_snapshot (weather + season + events), events_calendar, planning_tips

---

## 5. SeasonReasoner

**Question:** "What season is [destination] in, and how does that affect my trip?"

```python
from ai.intelligence.reasoning.season_reasoner import season_reasoner

result = season_reasoner.reason("Dubai", month=7, traveller_profile={...})
```

**Output data keys:** current_season (name, type, characteristics), current_weather, crowd_level, price_impact, all_seasons, recommended_season (personalised by budget_style)

Sprint 1 season types: `peak | shoulder | off-peak | festival | dry | wet | harmattan`

---

## 6. SafetyReasoner

**Question:** "Is it safe to travel to [destination]? Do I need a visa?"

```python
from ai.intelligence.reasoning.safety_reasoner import safety_reasoner

result = safety_reasoner.reason("Lagos", passport_country_iso="GB")
```

**Output data keys:** safety_level, risk_summary, precautions, visa (requirement / max_stay_days / notes), local_languages, health_tips, embassy_hint, advisory_note

Sprint 1 safety levels: `low | medium | high | critical` — from `Country.safety_level` in the graph.

---

## Reasoner Integration with Agents

Reasoners are consumed by specialist agents in `ai/agents/`. The agent wraps the `ReasoningResult.data` in an `AgentResult`:

```python
from ai.intelligence.reasoning.budget_reasoner import budget_reasoner
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus

graph_data = budget_reasoner.reason(destination, duration_days, traveller_profile)

result = AgentResult(
    agent_name="BudgetAgent",
    status=AgentStatus.SUCCESS if graph_data.success else AgentStatus.PARTIAL,
    confidence=graph_data.confidence,
    data=graph_data.data,
    assumptions=graph_data.assumptions,
)
```

## Sprint Roadmap

| Sprint | Enhancement |
|--------|-------------|
| 1 | Static estimates + tag matching + rule-based safety (current) |
| 2 | Live weather API; expand to 50+ cities |
| 3 | ML experience ranking; DNA-driven personalisation |
| 4 | Graph DB; live FCDO advisories; real-time pricing |
