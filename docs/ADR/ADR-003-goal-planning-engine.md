# ADR-003: Goal Planning Engine — In-Memory Domain with Future PostgreSQL Path

**Status:** Accepted  
**Date:** 2026-07-08  
**Deciders:** Engineering

---

## Context

TravelOS plans trips based on traveller intent. Before this ADR, the system had no persistent structure for what a traveller wanted to achieve — conversations accumulated context, but nothing was formalised. Without a Goal model, the system cannot:

1. Pause and resume planning across sessions
2. Distinguish between a "help me find a beach" query and a 10-day family holiday goal
3. Know whether it has enough information to start planning
4. Route the right agents to the right task

The Goal Planning Engine introduces this missing layer between the traveller's expressed desire and the trip planning execution.

---

## Decision

### 1. Goal as a first-class domain entity

`Goal` is a dataclass in `app/domains/goals/models.py` with 15 fields covering budget, timeframe, travellers, interests, constraints, success criteria, and flexibility. The domain is isolated in `app/domains/goals/` following the same pattern as other FastAPI domains.

### 2. In-memory repository for Sprint 1

`GoalRepository` stores goals in a Python dict, keyed by `goal_id`. The `GoalService` wraps it. This keeps Sprint 1 zero-dependency while the interface is already designed for a future PostgreSQL adapter:

```python
# Sprint 1
class GoalRepository:
    def save(self, goal: Goal) -> Goal: ...
    def get(self, goal_id: str) -> Goal | None: ...
    def list_by_traveller(self, traveller_id: str) -> list[Goal]: ...
    def update(self, goal_id: str, updates: dict) -> Goal | None: ...

# Sprint 3: replace with PostgreSQLGoalRepository implementing the same interface
```

### 3. AI layer is separate from the domain layer

`ai/goals/goal_classifier.py` and `ai/goals/goal_reasoner.py` live in the AI layer, not the domain. They are stateless utilities that take text or goal dicts and return structured results. This means:
- The domain works without the AI layer (for direct API calls)
- The AI layer can be upgraded (LLM → keyword → ML) without touching the domain

### 4. Keyword-based GoalClassifier (Sprint 1)

`GoalClassifier` uses priority-ordered keyword pattern matching to infer `GoalType` from raw text or interest lists. Deterministic, testable, no external dependencies.

### 5. Deterministic GoalReasoner

`GoalReasoner` computes planning readiness (0.0–1.0) from a goal dict using a weighted field checklist. Returns structured output: `goal_summary`, `missing_information`, `planning_readiness_score`, `recommended_next_actions`, `suitable_agents`.

### 6. Conversation engine auto-creates Goals on PLAN_TRIP

When the `ConversationEngine` classifies intent as `PLAN_TRIP` and the session has no `goal_id`, it calls `goal_service.create_from_conversation()` to create a `DRAFT` goal and stores the ID on the session. The `goal_id` is returned in the API response so clients can navigate to the goal view.

### 7. Frontend: server + client component split

- `/goals/new` — client component (form state, submit handler)
- `/goals/[id]` — server component (server-side fetch, no JS for rendering)

---

## Alternatives Considered

### A. Store goal context only in conversation session
Simple, but no URL-addressable goal, no persistence across sessions, no agent routing.

### B. SQLite persistence from Sprint 1
Adds a dependency; the interface would be identical. Value is low until Sprint 3 when multi-session persistence is actually needed. Rejected.

### C. Merge Goal into TIP (Traveller Intelligence Profile)
TIP models who the traveller *is*. Goals model what they *want to achieve*. These are different concerns: a single traveller may have multiple concurrent goals. Rejected.

---

## Consequences

**Good:**
- Goals survive session boundaries (in-memory per process in Sprint 1; DB in Sprint 3)
- Conversation engine can reference Goal without exposing domain internals
- Frontend has a URL-addressable goal view immediately
- GoalClassifier is testable without LLMs
- Status auto-promotion reduces manual updates

**Neutral:**
- In-memory goals reset on process restart — acceptable for Sprint 1
- GoalClassifier is keyword-based — sufficient for MVP, not for production NLU

**Bad:**
- No multi-goal prioritisation in Sprint 1 — one active goal per session
- No link between `Goal` and planned `Trip` yet — Trip model is Sprint 2

---

## Sprint Migration Path

| Sprint | Change |
|--------|--------|
| 1 | In-memory repository (current) |
| 2 | Add `trip_id` foreign key; link Goal→Trip when planning completes |
| 3 | PostgreSQL persistence; `GoalRepository` swap only |
| 4 | LLM-based GoalClassifier; multi-goal scoring and prioritisation |

---

## Related

- `docs/GOAL_PLANNING_ENGINE.md` — overview and component map
- `docs/API_GOALS.md` — endpoint reference
- `docs/TRAVEL_INTELLIGENCE_LAYER.md` — downstream knowledge + reasoning layer
- `docs/ADR/ADR-001-conversation-engine.md` — conversation layer ADR
