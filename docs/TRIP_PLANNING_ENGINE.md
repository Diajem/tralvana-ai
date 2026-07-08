# Trip Planning Engine

Sprint 1 implementation. Turns a Traveller Goal into a structured, explainable draft trip plan.

## Architecture

```
Traveller  →  Goal  →  Trip Brief  →  Trip Plan  →  Itinerary + Budget + Risks
```

| Layer | Module | Responsibility |
|-------|--------|----------------|
| Domain | `services/api/app/domains/trips/` | TripPlan model, REST API, in-memory repo |
| AI Orchestrator | `ai/planning/trip_planner.py` | Coordinates all planners |
| Itinerary | `ai/planning/itinerary_builder.py` | Day-by-day plan by goal_type |
| Budget | `ai/planning/budget_estimator.py` | Cost estimate using TIL or static tables |
| Risk | `ai/planning/risk_assessor.py` | Safety, visa, and logistic risks |
| Conversation | `ai/concierge/conversation_engine.py` | Auto-triggers on PLAN_TRIP intent |

## Trip Plan Fields

| Field | Type | Description |
|-------|------|-------------|
| `trip_id` | str | UUID |
| `traveller_id` | str \| None | Linked traveller |
| `goal_id` | str \| None | Linked Goal |
| `title` | str | Auto-generated |
| `origin` | str | Departure city |
| `destination` | str | Destination city |
| `duration_days` | int | Length of trip |
| `budget` | dict | From linked Goal |
| `travellers` | dict | adults / children / infants |
| `interests` | list | Merged from goal + request |
| `travel_style` | str | budget_style value |
| `assumptions` | list | Planning assumptions |
| `missing_information` | list | Data gaps |
| `recommended_destinations` | list | Suggested alternatives when no destination given |
| `draft_itinerary` | list | Day-by-day plan (see below) |
| `estimated_budget_breakdown` | dict | Cost breakdown |
| `risks` | list | Risk assessment |
| `confidence` | float | 0.0–1.0 |
| `status` | str | DRAFT / NEEDS_INFORMATION / READY / ARCHIVED |

## Trip Statuses

| Status | Meaning |
|--------|---------|
| `DRAFT` | Created but missing some context |
| `NEEDS_INFORMATION` | Missing key fields (destination, dates, budget) |
| `READY` | Confidence ≥ 65% — ready for agent dispatch |
| `ARCHIVED` | No longer active |

## Itinerary Format

Each day in `draft_itinerary`:

```json
{
  "day": 2,
  "title": "Day 2: Stadium & Football Heritage",
  "theme": "Stadium & Football Heritage",
  "morning": "Stadium tour and team shop visit",
  "afternoon": "Football museum or fan gallery",
  "evening": "Pre-match pub dinner and fan culture",
  "accommodation": "Mid-Range Hotel (3-4 Star), London",
  "estimated_daily_cost_usd": 150,
  "notes": ""
}
```

## AI Planning Modules

### ItineraryBuilder
- Day 1: always Arrival
- Day N: always Departure
- Middle days: cycled from goal_type templates (11 types × 4 themes each)
- When destination is in the knowledge graph: enriches mornings/evenings/afternoons with real venues

### BudgetEstimator
1. Tries `BudgetReasoner` from Travel Intelligence Layer (uses KG city/country/continent data)
2. Falls back to global static rate tables if destination not in graph
3. Returns full breakdown: flights, accommodation, food, activities, misc

### RiskAssessor
1. Tries `SafetyReasoner` for safety level and visa lookup
2. Adds tropical health risk for known West/East African cities
3. Always appends: financial, logistics, health common risks

## Confidence Score

| Condition | Points |
|-----------|--------|
| Base | +0.30 |
| Destination provided | +0.20 |
| Duration > 0 | +0.10 |
| Traveller profile linked | +0.10 |
| Goal has budget range | +0.10 |
| Goal has travel dates | +0.10 |
| Goal has interests | +0.10 |
| **Max** | **1.00** |

## Conversation Integration

When a message triggers `PLAN_TRIP` with destination and date known:
1. T-007 creates a Draft Goal
2. T-008 creates a Trip Plan (called from `_create_trip()`)
3. `trip_id` is stored on the session and returned in the API response

## Constraints

- No external APIs
- No database (in-memory only)
- No bookings
- Sprint 3+: swap `TripRepository` for PostgreSQL adapter
