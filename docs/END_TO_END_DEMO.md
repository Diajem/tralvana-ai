# End-to-End TravelOS Demo

T-009 — connects every layer of the TravelOS stack into one callable pipeline.

## Demo Scenario

| Field | Value |
|-------|-------|
| Traveller | Alex Okafor, Manchester, UK |
| Destination | Japan (Tokyo) |
| Duration | 10 days |
| Budget | £2,000 per person |
| Interests | Football, Food, Photography |
| Travellers | 2 adults |
| Goal Type | Football Travel |

## Pipeline Stages

```
POST /demo/japan-football-food
        │
        ├── Stage 1: Traveller Profile Built (mock)
        │
        ├── Stage 2: DNA Inference
        │     └── TravellerDNAInferenceService.infer()
        │           → Primary: Food Traveller
        │           → Secondary: Football Traveller, Explorer, Photography Traveller
        │
        ├── Stage 3: Goal Created
        │     └── GoalService.create()
        │           → Status: DRAFT → scored at 100% readiness
        │
        ├── Stage 4: Goal Reasoned
        │     └── GoalReasoner.reason()
        │           → planning_readiness_score, missing_information, suitable_agents
        │
        ├── Stage 5: Knowledge Graph Queried
        │     └── KnowledgeService.find_entity("City", "Tokyo")
        │           → Narita Airport, Senso-ji Temple, Sushi Saito, Gamba Osaka,
        │             Panasonic Stadium, Hanami Festival, Shinkansen, weather records
        │
        ├── Stage 6: Conversation Engine
        │     └── ConversationEngine.process()
        │           → Intent: PLAN_TRIP, confidence: ~0.57
        │           → Destination extracted: Japan
        │           → Date hint: "in october"
        │           → Goal auto-created, Trip auto-generated (when has_enough_info=True)
        │
        └── Stage 7: Trip Plan Generated
              └── TripPlanningService.plan()
                    → ItineraryBuilder: 10 days, FOOTBALL_TRAVEL templates + KG enrichment
                    → BudgetEstimator: KG-backed or static fallback
                    → RiskAssessor: SafetyReasoner + common risks
                    → confidence: 1.0 (all data present)
                    → status: READY
```

## Demo Endpoint

```
POST /demo/japan-football-food
```

No request body required.

### Response Shape

```json
{
  "demo_id": "japan-football-food",
  "generated_at": "...",
  "traveller": { "name": "Alex Okafor", "home_city": "Manchester", "summary": "..." },
  "dna": { "primary_type": "Food Traveller", "secondary_types": [...], "confidence": 0.54 },
  "goal": { "title": "Football & Food Tour — Japan", "planning_readiness_score": 1.0, ... },
  "conversation": { "intent": "PLAN_TRIP", "response": "...", "confidence": 0.57 },
  "knowledge_insights": {
    "destination_city": "Tokyo",
    "airports": [...], "attractions": [...], "football_clubs": [...], "events": [...], "weather_records": [...]
  },
  "trip_plan": {
    "status": "READY", "confidence": 1.0,
    "draft_itinerary": [ ... 10 days ... ],
    "estimated_budget_breakdown": { "total_estimate_usd": 4400 },
    "risks": [...], "next_actions": [...]
  },
  "pipeline_summary": { "stages_completed": 7, "overall_confidence": 1.0 }
}
```

## Frontend

**`/demo`** — "Run Japan Football & Food Demo" button triggers the pipeline and renders:
- Pipeline summary with stage checklist
- Traveller profile card
- DNA archetype with trait bars
- Goal card with readiness bar
- Conversation card with intent + AI response
- Knowledge Graph insights (airports, attractions, football clubs, weather)
- 10-day itinerary (day cards)
- Budget breakdown table
- Risk assessment cards
- Recommended next steps

## Constraints

- No external APIs
- No database
- No bookings
- All data is deterministic and reproducible
- Every service called is the same singleton used by the live REST API
