# ADR-004: Trip Planning Engine

**Date**: 2026-07-08
**Status**: Accepted
**Sprint**: 1

## Context

TravelOS needed to move from understanding traveller goals to producing an explainable draft trip plan. The plan must be deterministic, reproducible, and ready for Sprint 3 live-data integration without requiring an architectural rewrite.

## Decision

Build a four-module AI planning layer (`ai/planning/`) that produces a `TripPlan` domain object stored in-memory:

1. **TripPlanner** — orchestrator; computes confidence, missing info, next actions
2. **ItineraryBuilder** — template-driven day-by-day plan enriched by the knowledge graph
3. **BudgetEstimator** — wraps `BudgetReasoner` (TIL) with static fallback
4. **RiskAssessor** — wraps `SafetyReasoner` (TIL) with heuristic enrichment

The `TripPlanningService` in the domain layer owns repository interaction and merges Goal + profile + request context before delegating to `TripPlanner`.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| Single monolithic planner | Hard to test, violates SRP |
| LLM-generated itinerary | Non-deterministic, costly, Sprint 1 constraint |
| Use TravelManager agents directly | Agents return AgentResult, not structured plan |
| External planning API | Violates "no external APIs" constraint |

## Consequences

- All planning is deterministic: same inputs always produce the same plan
- Itinerary quality is limited by template data — enriched with KG data for ~10 known cities
- Budget estimates have ±20% margin (static tables); Sprint 3+ adds live pricing
- Confidence scoring tells the frontend what data is missing

## Sprint 3+ Migration Path

| Component | Upgrade |
|-----------|---------|
| `TripRepository` | Swap for PostgreSQL adapter |
| `BudgetEstimator` | Add Skyscanner / Amadeus flight pricing |
| `ItineraryBuilder` | Add Viator / GetYourGuide activity lookup |
| `TripPlanner.plan()` | Add optional LLM narrative enrichment pass |
| `RiskAssessor` | Add FCDO / US State Dept travel advisory integration |
