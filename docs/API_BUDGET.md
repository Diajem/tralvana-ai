# Budget API

Base URL: `http://localhost:8000`

## Endpoints

### POST /budget/recommend

Generate ranked budget-tier recommendations for a trip. Always returns five options — one per budget style (`backpacker`, `budget`, `balanced`, `comfort`, `luxury`).

**Request body**

```json
{
  "traveller_id": "traveller_001",
  "trip_id": "uuid",
  "destination": "Tokyo",
  "goal_type": "FAMILY_TRIP",
  "budget_style": "balanced",
  "duration_days": 7,
  "adults": 2,
  "children": 1
}
```

All fields are optional. If `trip_id` is provided, `destination`/`duration_days` are taken from the linked Trip Plan when present; if the trip has a linked Goal, its `budget.max_usd` drives `cap_fit` scoring. If `destination` is omitted, rates default to a global-average band and every option is still returned. `budget_style` is a preference used for `style_fit` scoring — it does not filter which tiers are returned.

**Response: 201 Created**

```json
{
  "traveller_id": null,
  "trip_id": null,
  "destination": "Tokyo",
  "budget_options": [
    {
      "budget_option_id": "uuid",
      "destination": "Tokyo",
      "region": "Asia",
      "budget_style": "balanced",
      "duration_days": 7,
      "adults": 2,
      "children": 1,
      "cabin_class": "economy",
      "daily_cost_usd": 358,
      "flight_cost_usd": 2475,
      "accommodation_usd": 1126,
      "food_usd": 626,
      "activities_usd": 500,
      "misc_usd": 250,
      "total_cost_usd": 4977,
      "cost_per_day_usd": 711,
      "cost_per_person_usd": 1659,
      "currency": "USD",
      "affordability_score": 0.6,
      "comfort_score": 0.6,
      "cost_certainty_score": 0.85,
      "family_suitability_score": 0.85,
      "match_score": 0.78,
      "reasoning": "Balanced tier in Tokyo totals USD 4977 over 7 day(s) — scores 0.78. ...",
      "risks": [],
      "assumptions": ["No traveller profile — default style and family assumptions applied."],
      "recommendation_type": "BEST_OVERALL"
    }
  ],
  "assumptions": [
    "No goal budget cap supplied — cap-fit scoring uses a neutral baseline.",
    "Budget estimates are deterministic mock regional rates — no live pricing was queried."
  ],
  "next_actions": [
    "Confirm your actual budget cap so cap-fit scoring is precise.",
    "Compare the top-ranked tier against live flight and accommodation pricing before booking.",
    "Budget data has not been checked live — figures are indicative only."
  ],
  "recommended_agents": ["budget_agent"],
  "summary": "5 budget option(s) ranked for Tokyo. Best overall: Balanced tier at USD 4977 (match 0.78). No live pricing was queried."
}
```

---

### GET /budget/{budget_option_id}

Retrieve a single budget option by ID.

**Response: 200 OK** — full `BudgetOption` object, or **404** if not found.

---

### GET /trips/{trip_id}/budget

List all budget options previously recommended and linked to a trip.

**Response: 200 OK** — array of `BudgetOption` objects (empty array if the trip has no saved options).

---

## Budget Styles

| Style | Implied Cabin | Notes |
|-------|---------------|-------|
| `backpacker` | economy | Leanest tier; assumes hostel-level accommodation and informal transport |
| `budget` | economy | Value-conscious, standard economy travel |
| `balanced` | economy | Mid-range, the default preference |
| `comfort` | business | Business-cabin flights, higher-comfort accommodation |
| `luxury` | first | First-cabin flights, premium accommodation |

## Recommendation Types

| Type | Meaning |
|------|---------|
| `BEST_OVERALL` | Highest match score |
| `LOWEST_COST` | Cheapest total cost among the remaining tiers |
| `MOST_COMFORTABLE` | Highest comfort score among the remaining tiers |
| `BEST_VALUE` | Best affordability-to-comfort ratio |
| `BEST_FOR_FAMILY` | Best suited to travelling with children |
| `AVOID` | Below the match threshold — in practice, almost always a tier that badly exceeds the supplied budget cap |

A persona only claims `BEST_VALUE`/`BEST_FOR_FAMILY` if genuinely relevant (`persona_score >= 0.45`) — see `docs/BUDGET_INTELLIGENCE_ENGINE.md` and `docs/DISCOVERY_LAYER_PATTERN.md` for the general assignment algorithm.

## Conversation Shortcut

`POST /conversation/message` with a budget-comparison message (e.g. `"recommend a budget for my trip"`, `"compare budget options in Tokyo"`) routes to the same Budget Intelligence engine and returns a composed natural-language summary referencing the top match — see `docs/CONVERSATION_ENGINE.md`. Simpler single-number cost questions (`"how much does it cost"`, `"how expensive is Tokyo"`) continue routing to the pre-existing `BUDGET_ADVICE` intent and `budget_agent`.
