# ADR-010: Flight Intelligence Engine

**Date**: 2026-07-08
**Status**: Accepted
**Sprint**: 2 (T-015)

## Context

Tralvana Travel's mission is explicitly not "search flights" — it's reasoning about which flight options best fit the traveller, goal, budget, trip plan, and travel preferences. This is the first module of the Discovery Layer, sitting after Trip Planning in the architecture:

```
Traveller Intelligence → Goal → Trip Plan → Flight Intelligence → Flight Recommendation → Explanation
```

A lightweight `ai/agents/flight_agent.py` already existed (a specialist agent dispatched by `TravelManager`, returning one mock flight summary as part of `PLAN_TRIP`). It does not rank options, does not score against preferences, and returns a single result — insufficient for what T-015 asks for.

## Decision

**A new tier, not a replacement.** Built `ai/discovery/flights/` (a new `ai/discovery/` package — the first Discovery Layer module) alongside the existing `flight_agent.py`, which was left untouched. This mirrors the existing precedent of `ai/planning/budget_estimator.py` (a rich planning engine) coexisting with `ai/agents/budget_agent.py` (a lightweight specialist agent) — the two tiers already coexist elsewhere in this codebase.

**Four-module AI layer**, mirroring `ai/planning/`'s structure:
1. `FlightIntelligence` (`flight_intelligence.py`) — orchestrator: generate candidates → score → explain → assess risk → rank → label
2. `MockFlightProvider` (same file) — deterministic mock inventory behind a `search()` interface a real provider can implement later
3. `FlightScorer` (`flight_scorer.py`) — seven weighted, independently explainable scoring dimensions
4. `FlightReasoner` (`flight_reasoner.py`) — turns the score breakdown into a human-readable explanation
5. `FlightRiskAssessor` (`flight_risk_assessor.py`) — per-option risk flags

**Domain layer** (`services/api/app/domains/flights/`) follows the same five-file structure as `goals/` and `trips/` — `models.py`, `schemas.py`, `repository.py`, `service.py`, `router.py` — with an in-memory `FlightRepository`, matching `TripRepository`'s Sprint-1 pattern.

**Recommendation type assignment is priority-ordered and exhaustive.** AVOID (score < 0.35) is filtered first; then BEST_OVERALL, LOWEST_PRICE, and SHORTEST_DURATION each claim one option from what's left; then the four `BEST_FOR_*` persona types each claim their best-fit remaining option; any option still unlabeled falls back to its own single best-fit persona. Every option in a response always receives exactly one of the 8 types — no duplicates, no gaps.

**Conversation integration is a direct call, not an agent dispatch.** A new `Intent.FLIGHT_SEARCH` (patterns checked before `PLAN_TRIP`, verified not to collide with existing "fly to" / "book a flight" / "change my flight" triggers) maps to zero specialist agents in `DecisionEngine._AGENT_MAP`. `ConversationEngine._get_flight_recommendations()` calls the Flight Intelligence Service directly, exactly as Goal and Trip creation already do — not through `TravelManager`/`AgentRegistry`. Unlike `PLAN_TRIP`, `FLIGHT_SEARCH` only requires a destination; the departure date is defaulted by the engine and recorded as an assumption, avoiding an unnecessary clarification round-trip for a quick "recommend flights to Tokyo" style request.

## Alternatives Considered

| Option | Rejected Because |
|--------|-------------------|
| Extend `flight_agent.py` in place | It's a specialist agent returning a single `AgentResult`, not built for ranking multiple options with per-option explainability; extending it would conflate two different tiers |
| Dispatch `FLIGHT_SEARCH` through `TravelManager`/`AgentRegistry` | Adds an unnecessary indirection for a rich, multi-field response; Goal/Trip creation already establish the precedent of direct service calls from `ConversationEngine` for richer results |
| Single `recommendation_type` chosen purely by rank position (1st = BEST_OVERALL, 2nd = LOWEST_PRICE, ...) | Ignores the actual data — the 2nd-ranked option by match score isn't necessarily the cheapest; persona-weighted sub-scores give each label real meaning |
| Random/seeded mock data generator | Violates "deterministic mock data only" — same route must always return the same candidates for reproducible testing and demos |
| Real provider interface via ABC/Protocol now | Premature — Sprint 1 has exactly one provider; `MockFlightProvider`'s `search()` signature is already the seam a real provider slots into, an ABC adds no value until a second implementation exists |

## Consequences

- Two flight-related code paths now exist by design: `flight_agent.py` (specialist agent, part of `PLAN_TRIP`'s agent dispatch) and Flight Intelligence (`FLIGHT_SEARCH`, direct discovery). Documented explicitly in `FLIGHT_INTELLIGENCE_ENGINE.md` to prevent future confusion about which one a new contributor should extend.
- Every flight option carries its own `reasoning`, `risks`, and `assumptions` — the response is self-explanatory without needing to cross-reference a separate scoring document.
- `FlightRepository` is in-memory, matching `TripRepository`/`GoalRepository` — swapped for PostgreSQL in the same Sprint 3 migration as the rest of the domain layer.
- `MockFlightProvider`'s price/duration formulas are seeded from the origin/destination string, not a distance lookup table — deterministic and reproducible, but not geographically realistic. Acceptable for Sprint 1 mock data; a real provider replaces this entirely.
- All 92 pre-existing tests continue to pass unchanged; 49 new tests cover the scorer, risk assessor, orchestrator, API endpoints, and conversation routing (including two explicit non-collision regression tests for "fly to" and "change my flight").

## Sprint 4+ Migration Path

| Component | Upgrade |
|-----------|---------|
| `MockFlightProvider` | Real `FlightProvider` (Amadeus, Skyscanner) behind the same `search()` signature |
| `FlightScorer` | Incorporate live on-time-performance and disruption data |
| `FlightRiskAssessor` | Live delay/cancellation risk from provider data instead of static heuristics |
| `FlightRepository` | Swap for PostgreSQL adapter (same Sprint 3 migration as Goals/Trips) |
| `Intent.FLIGHT_SEARCH` | LLM-backed classification, replacing keyword patterns |
