# Flight Intelligence Engine

T-015 — the first Discovery Layer module. Turns a flight search into a ranked, explainable set of recommendations instead of a raw list of options.

## Architecture

```
Traveller Intelligence → Goal → Trip Plan → Flight Intelligence → Flight Recommendation → Explanation
```

| Layer | Module | Responsibility |
|-------|--------|----------------|
| Domain | `services/api/app/domains/flights/` | FlightOption model, REST API, in-memory repo |
| AI Orchestrator | `ai/discovery/flights/flight_intelligence.py` | Generates candidates, scores, ranks, labels |
| Provider | `ai/discovery/flights/flight_intelligence.py::MockFlightProvider` | Deterministic mock inventory — swappable |
| Scoring | `ai/discovery/flights/flight_scorer.py` | 0.0–1.0 match score, per-dimension breakdown |
| Explanation | `ai/discovery/flights/flight_reasoner.py` | Human-readable reasoning from the score breakdown |
| Risk | `ai/discovery/flights/flight_risk_assessor.py` | Per-option risk flags |
| Conversation | `ai/concierge/conversation_engine.py` | Routes `FLIGHT_SEARCH` intent directly to this engine |

## Why Flight Intelligence is separate from `flight_agent`

`ai/agents/flight_agent.py` already exists — a lightweight specialist agent dispatched by `TravelManager` as part of `PLAN_TRIP`, returning a single mock flight summary. It was preserved untouched.

Flight Intelligence is a different tier: a full Discovery Layer module with its own domain (persisted `FlightOption` records, its own REST API), its own AI submodule, and multi-option ranking with explainable scoring. This mirrors the existing precedent of `ai/planning/budget_estimator.py` coexisting with `ai/agents/budget_agent.py` — a rich planning engine and a lightweight specialist agent are not mutually exclusive in this architecture.

## FlightOption Fields

| Field | Type | Description |
|-------|------|-------------|
| `flight_option_id` | str | UUID |
| `traveller_id` | str \| None | Linked traveller |
| `trip_id` | str \| None | Linked Trip Plan |
| `origin` / `destination` | str | Route |
| `departure_date` / `return_date` | str \| None | ISO dates |
| `airline` / `flight_number` | str | Mock carrier |
| `cabin_class` | str | economy / business / first |
| `stops` | int | 0, 1, or 2 |
| `layover_duration` | str | e.g. `"1h 35m"`, empty for direct |
| `departure_time` / `arrival_time` | str | `HH:MM` |
| `total_duration` | str | e.g. `"11h 20m"` |
| `estimated_price` | float | Mock fare |
| `currency` | str | Always `"USD"` in Sprint 1 |
| `baggage_included` | bool | |
| `refundability` | str | refundable / partially_refundable / non_refundable |
| `flexibility` | str | flexible / fixed |
| `match_score` | float | 0.0–1.0, see Scoring below |
| `reasoning` | str | Explanation of the score |
| `risks` | list[str] | Per-option risk flags |
| `assumptions` | list[str] | Per-option assumptions |
| `recommendation_type` | str | One of the 8 types below |

## Recommendation Types

Every option receives exactly one label — no duplicates, no gaps. Assigned in priority order so no option is labeled twice:

1. **AVOID** — `match_score < 0.35`
2. **BEST_OVERALL** — highest `match_score` among the rest
3. **LOWEST_PRICE** — cheapest among the rest
4. **SHORTEST_DURATION** — fastest among the rest
5. **BEST_FOR_BUSINESS / BEST_FOR_FAMILY / BEST_FOR_COMFORT / BEST_FOR_BUDGET** — persona-weighted sub-scores (see Scoring) pick the winner for each remaining persona
6. Any option still unlabeled (more candidates than categories) falls back to its own single best-fit persona, so every option always gets a label from the closed set of 8.

## Scoring

`FlightScorer` computes seven weighted, independently explainable dimensions:

| Dimension | Weight | Signal |
|-----------|--------|--------|
| `price_fit` | 0.25 | Price vs. a budget-style-derived ceiling |
| `cabin_match` | 0.15 | Requested cabin vs. actual cabin |
| `airline_preference` | 0.10 | Loyalty programs / explicit preference |
| `layover_tolerance` | 0.15 | Stops vs. budget-style-derived tolerance |
| `baggage_fit` | 0.10 | Baggage included vs. trip length / accommodation type |
| `time_of_day_fit` | 0.10 | Departure hour vs. preference (red-eye penalised) |
| `duration_fit` | 0.15 | Total travel time, more sensitive on short trips |

A DNA/goal-type adjustment (±0.05–0.08 per signal) is applied afterward — e.g. a traveller with high `business_orientation` gets a boost for flexible, direct fares; high `luxury_orientation` boosts premium cabins. Every adjustment is logged in `dna_notes` and surfaces in the option's `reasoning` text — explainable, not a black-box multiplier.

**Explainable AI, not a black box** (per `ENGINEERING_PRINCIPLES.md`): `FlightReasoner` turns the breakdown into a sentence-by-sentence explanation, always traceable to a specific field or weighted dimension.

## Mock Provider

`MockFlightProvider.search()` deterministically generates 6 candidate flights from fixed carrier archetypes (premium direct, standard direct, budget direct, standard one-stop, budget one-stop with a long layover, budget two-stop). Prices and flight duration are derived from a formula seeded by the origin/destination string — same route always produces the same candidates, no randomness.

**Ready for a real provider**: any future `FlightProvider` (Amadeus, Skyscanner) only needs to implement `search(origin, destination, departure_date, return_date, cabin_class) -> list[dict]` with the same field shape. `FlightIntelligence(provider=...)` accepts the swap — no other code in the discovery layer changes. This follows `ENGINEERING_PRINCIPLES.md` #6, No Hardcoded Providers.

## Conversation Integration

A new `Intent.FLIGHT_SEARCH` was added, checked before `PLAN_TRIP` in the pattern list (patterns: "recommend flights", "find flights", "flight options", "search flights", etc. — verified not to collide with existing `PLAN_TRIP` phrases like "fly to" / "book a flight" or `MODIFY_TRIP`'s "change my flight").

Unlike `PLAN_TRIP`, `FLIGHT_SEARCH` only requires a destination — no date is required, since Flight Intelligence defaults the departure date and records it as an assumption. `DecisionEngine` maps `FLIGHT_SEARCH` to zero specialist agents (`requires_agents: []`) — it is dispatched directly by `ConversationEngine._get_flight_recommendations()`, not through `TravelManager`/`AgentRegistry`, matching how Goal and Trip creation are also direct calls rather than agent dispatches.

## Constraints

- No external flight APIs (no Amadeus, no Skyscanner)
- No booking, no payment
- Deterministic mock data only — same inputs always produce the same candidates and prices
- Sprint 4+: swap `MockFlightProvider` for a real `FlightProvider`; scoring/reasoning/risk logic is unchanged
